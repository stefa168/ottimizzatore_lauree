import asyncio
from pathlib import Path
from typing import Any, cast, Iterable, Optional

import structlog
from advanced_alchemy.config import SQLAlchemyAsyncConfig
from advanced_alchemy.repository import LoadSpec
from pandas import DataFrame
from pyomo.core import ConcreteModel
from pyomo.core.base.set import OrderedScalarSet
from pyomo.opt import SolverFactory, SolverResults, SolverStatus, TerminationCondition, OptSolver
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from optimization.models import create_min_durata_model
from v2.db.models import GradSession, OptimizationConfiguration, SolverEnum, OptimizationLog, SolutionCommission, \
    SessionProfessor
from v2.domain.grad_sessions.deps import GradSessionRepository, OptimizationConfigurationRepository, \
    StudentRepository, SessionProfessorRepository
from v2.domain.grad_sessions.schemas import OptConfCompleteDTO
from v2.utils.crud_helpers import get_one_or_raise, exists_or_raise

logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger()


async def check_gs_exists_raise(graduation_session_repo: GradSessionRepository,
                                session_id: int
                                ) -> None:
    """
    Check if a Graduation Session exists, and raise an HTTPException if it does not.

    This function verifies the existence of a Graduation Session in the repository
    based on its unique identifier. If the specified session does not exist, it raises
    an HTTP 404 exception with an appropriate error message.

    :param graduation_session_repo: The repository interface for accessing graduation sessions.
    :type graduation_session_repo: GradSessionRepository
    :param session_id: The unique identifier of the Graduation Session to check.
    :type session_id: int
    :return: None
    :rtype: None
    :raises HTTPException: Raised with HTTP 404 if the Graduation Session does not exist.
    """
    logger.debug(f"Retrieving session {session_id}")

    await exists_or_raise(
        graduation_session_repo,
        GradSession.id == session_id,
        not_found_msg="The specified Graduation Session does not exist"
    )


async def get_opt_conf_raise(configuration_id: int,
                             session_id: int,
                             optimization_configuration_repo: OptimizationConfigurationRepository,
                             load: Optional[LoadSpec] = None,
                             ) -> OptimizationConfiguration:
    """
    Retrieve an optimization configuration for a given configuration ID and session ID.

    This function queries the provided optimization configuration repository to fetch
    an optimization configuration that matches the given configuration ID and session ID.
    If no configuration is found, an HTTPException with a "Configuration not found" message
    is raised, and the HTTP 404 NOT FOUND status code is returned.

    :param load: Optional argument indicating additional optimization configuration loading specifications.
    :param configuration_id: The unique identifier for the configuration to fetch.
    :type configuration_id: int
    :param session_id: The session identifier associated with the configuration.
    :type session_id: int
    :param optimization_configuration_repo: Repository to query for optimization configurations.
    :type optimization_configuration_repo: OptimizationConfigurationRepository
    :return: The matching optimization configuration if found.
    :rtype: OptimizationConfiguration
    :raises HTTPException: If no matching configuration is found, with HTTP status 404.
    """
    return await get_one_or_raise(
        optimization_configuration_repo,
        OptimizationConfiguration.id == configuration_id,
        OptimizationConfiguration.session_id == session_id,
        load=load,
        not_found_msg=f"Configuration with ID {configuration_id} (SID {session_id}) not found"
    )


async def get_session_professor_raise(session_id: int,
                                      session_professor_id: int,
                                      session_prof_repo: SessionProfessorRepository) -> SessionProfessor:
    """
    Retrieve the session professor details for the given session using the provided
    repository. If the session professor is not found, this will raise an error.

    :param session_id: The ID of the session.
    :param session_professor_id: The ID of the session professor for the given session.
    :param session_prof_repo: The repository to interface with session professor
        data layer operations.
    :return: An instance of `SessionProfessor` corresponding to the specified session
        and professor IDs.
    """
    return await get_one_or_raise(
        session_prof_repo,
        SessionProfessor.session_id == session_id,
        SessionProfessor.id == session_professor_id,
        load=[SessionProfessor.professor],
        not_found_msg=f"SessionProfessor with {session_professor_id} (SID {session_id}) not found"
    )


async def solver_wrapper(
        db_conf: SQLAlchemyAsyncConfig,
        config_dto: OptConfCompleteDTO,
        cc_path: Path
) -> bool:
    logg = logger.bind(opt_id=config_dto.id, session_id=config_dto.session_id)
    logg.info(f"Starting optimization")

    def run_solver_blocking(config: OptimizationConfiguration, cc_path: Path):
        return asyncio.run(run_solver(config, cc_path))

    async with db_conf.get_session() as db_session:
        conf_repo = OptimizationConfigurationRepository(session=db_session)
        config = await get_opt_conf_raise(config_dto.id, config_dto.session_id, conf_repo)
        # db_session.expunge(config)

    try:
        # results, model, opt_log = await run_solver(config, cc_path)
        results, model, opt_log = await asyncio.to_thread(run_solver_blocking, config, cc_path)
    except Exception as e:
        logg.exception(f"An error occurred while solving the optimization problem", e)
        return False

    if not opt_log.success:
        # todo decide what to do in case of failure
        logg.error(f"Solver encountered an error. Solver status: {results.solver.status}")
        return False
    if not opt_log.solver_reached_optimality and not opt_log.solver_time_limit_reached:
        # todo decide what to do in case of failure
        logg.error(f"Solver failed to reach optimality. Solver status: {results.solver.status}")
        return False

    async with db_conf.get_session() as db_session:
        # todo return also the reason why the solver stopped
        morning_commissions, afternoon_commissions = await generate_commissions_from_model(config, model, db_session)
        new_commissions = morning_commissions + afternoon_commissions

        conf_repo = OptimizationConfigurationRepository(session=db_session)
        # Re-load the persistent parent, then apply changes on it
        persistent = await get_opt_conf_raise(
            config.id,
            config.session_id,
            conf_repo,
            load=[selectinload(OptimizationConfiguration.commissions).options(
                selectinload(SolutionCommission.professors),
                selectinload(SolutionCommission.students)
            )]
        )

        opt_log.opt_config = persistent

        # Replace existing commissions (if any). This is just a precaution
        persistent.optimization_log = opt_log
        persistent.commissions.clear()
        persistent.commissions.extend(new_commissions)

        try:
            await db_session.commit()
            await db_session.flush()
        except Exception as e:
            logg.exception("Error while saving optimization results to the database")
            raise

    logg.info("Optimization completed and correctly saved to database.")
    return True


async def run_solver(
        config: OptimizationConfiguration,
        cc_path: Path
) -> tuple[SolverResults, ConcreteModel, OptimizationLog]:
    dat_path = cc_path / "temp.dat"

    model: ConcreteModel
    if config.online:
        # mindurata
        model = create_min_durata_model(dat_path)
    else:
        # maxdurata
        # model = create_max_durata_model(dat_path)
        raise RuntimeError("Max durata model deprecated")
    logger.debug("Optimization model created")

    model_filename = cc_path / "model.lp"
    # Actually create the model that will be solved
    model.write(str(model_filename), io_options={'symbolic_solver_labels': True})
    logger.debug(f"Model written to file {model_filename}")

    solver_arguments: dict[str, Any] = {'options': {}}

    if config.solver == SolverEnum.CPLEX:
        solver_arguments['options']['timelimit'] = config.optimization_time_limit
        solver_arguments['options']['mip_tolerances_mipgap'] = config.optimization_gap
        solver_arguments['executable'] = "/opt/ibm/ILOG/CPLEX_Studio128/cplex/bin/x86-64_linux/cplex"
    elif config.solver == SolverEnum.GLPK:
        solver_arguments['options']['tmlim'] = config.optimization_time_limit
        solver_arguments['options']['mipgap'] = config.optimization_gap
    elif config.solver == SolverEnum.GUROBI:
        solver_arguments['options']['TimeLimit'] = config.optimization_time_limit
        solver_arguments['options']['MIPGap'] = config.optimization_gap
    else:
        raise ValueError("Unknown solver")

    logger.debug("Options for selected solver set")

    solver: OptSolver = SolverFactory(str(config.solver.value).lower(), **solver_arguments)
    solver_log_path = cc_path / "solver.log"

    logger.info("Running solver...")
    opt_log = OptimizationLog()

    opt_log.started()
    with solver_log_path.open('a+') as f:
        f.write(f'Optimizer try started at {str(opt_log.start_time.isoformat())}')

    results: SolverResults = solver.solve(
        model,
        keepfiles=True,
        logfile=str(solver_log_path.absolute())
    )
    logger.info(f"The solver has exited. Status: {results.solver.status}")

    solver_ok = results.solver.status == SolverStatus.ok
    solver_reached_optimality = results.solver.termination_condition == TerminationCondition.optimal
    solver_reached_time_limit = results.solver.termination_condition == TerminationCondition.maxTimeLimit

    opt_log.finished(solver_ok, solver_reached_optimality, solver_reached_time_limit)
    with solver_log_path.open('r') as f:
        opt_log.log = f.read()

    return results, model, opt_log


async def generate_commissions_from_model(
        config: OptimizationConfiguration,
        model: ConcreteModel,
        db_session: AsyncSession
) -> tuple[list[SolutionCommission], list[SolutionCommission]]:
    session_prof_repo = SessionProfessorRepository(session=db_session)
    students_repo = StudentRepository(session=db_session)

    morning_commissions = await extract_commissions(
        config,
        session_prof_repo, students_repo,
        model, model.commissioni_mattina
    )
    afternoon_commissions = await extract_commissions(
        config,
        session_prof_repo, students_repo,
        model, model.commissioni_pomeriggio,
        morning=False, commission_count_offset=len(morning_commissions)
    )

    # Set the configuration id of each commissionsolution
    for comm in morning_commissions + afternoon_commissions:
        comm.opt_config_id = config.id
        comm.session_id = config.session_id

    return morning_commissions, afternoon_commissions


async def extract_commissions(
        config: OptimizationConfiguration,
        session_prof_repo: SessionProfessorRepository,
        students_repo: StudentRepository,
        model: ConcreteModel,
        commission_model: OrderedScalarSet,
        morning=True,
        commission_count_offset=0
) -> list[SolutionCommission]:
    from pyomo.environ import value
    commissions: list[SolutionCommission] = []
    session_id = config.session_id

    for commission_id, commission in enumerate(commission_model):
        new_commission = SolutionCommission(morning=morning, duration=0)

        # Professors selected for this commission: check z[SP_ID, commission]
        for _, prof_row in cast(DataFrame, model.docenti).iterrows():
            sp_id = int(prof_row["SP_ID"])
            if value(model.z[sp_id, commission]) > 0.8:
                session_professor = await session_prof_repo.get_one_or_none(
                    SessionProfessor.id == sp_id,
                    SessionProfessor.session_id == session_id
                )

                if session_professor is None:
                    raise RuntimeError(f"Missing Session Professor entry for SP_ID={sp_id}")
                new_commission.professors.append(session_professor)

        # Students assigned to this commission
        for candidate in cast(Iterable[int], model.Candidati):
            if value(model.x[candidate, commission]) > 0.8:
                session_candidate = await students_repo.get(int(candidate))

                new_commission.students.append(session_candidate)
                new_commission.duration += int(model.tesisti.loc[candidate, 'Durata'])

        commissions.append(new_commission)

    # Let's filter out the commissions that aren't used
    used_commissions = [comm for comm in commissions if comm.duration > 0]

    # Now we assign the ID to the commissions
    for index, comm in enumerate(used_commissions):
        comm.order_key = index + commission_count_offset

    return used_commissions
