from pathlib import Path
from typing import Any, cast, Iterable

import structlog
from litestar import status_codes as http_statuses
from litestar.exceptions import HTTPException
from pandas import DataFrame
from pyomo.core import ConcreteModel
from pyomo.core.base.set import OrderedScalarSet
from pyomo.opt import SolverFactory, SolverResults, SolverStatus, TerminationCondition, OptSolver
from sqlalchemy.ext.asyncio import AsyncSession

from optimization.models import create_min_durata_model, create_max_durata_model
from utils import FileChangeHandler
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
                             optimization_configuration_repo: OptimizationConfigurationRepository
                             ) -> OptimizationConfiguration:
    """
    Retrieve an optimization configuration for a given configuration ID and session ID.

    This function queries the provided optimization configuration repository to fetch
    an optimization configuration that matches the given configuration ID and session ID.
    If no configuration is found, an HTTPException with a "Configuration not found" message
    is raised, and the HTTP 404 NOT FOUND status code is returned.

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
        db_session: AsyncSession,
        config_dto: OptConfCompleteDTO,
        cc_path: Path
) -> bool:
    logger.bind(opt_id=config_dto.id, session_id=config_dto.session_id)
    logger.info(f"Starting optimization")
    conf_repo = OptimizationConfigurationRepository(session=db_session)

    config = await conf_repo.get_one_or_none(OptimizationConfiguration.id == config_dto.id)

    if config is None:
        raise RuntimeError("Optimization configuration does not exist")

    try:
        await solve_model(config, cc_path, db_session)
        await conf_repo.add(config, auto_commit=True)
        # await conf_repo.session.flush()
        # await conf_repo.session.commit()
        # await conf_repo.update(config)
    except Exception as e:
        logger.error(f"An error occurred while solving the optimization problem: {e}", e)
        return False
    else:
        logger.info("Optimization completed and correctly saved to database.")
        return True


async def solve_model(config: OptimizationConfiguration, cc_path: Path, db_session: AsyncSession):
    dat_path = cc_path / "temp.dat"

    model: ConcreteModel
    if config.online:
        # mindurata
        model = create_min_durata_model(dat_path)
    else:
        # maxdurata
        model = create_max_durata_model(dat_path)
    logger.debug("Optimization model created")

    model_filename = cc_path / "model.lp"
    # Actually create the model that will be solved
    model.write(str(model_filename), io_options={'symbolic_solver_labels': True})
    logger.debug(f"Model written to file ${model_filename}")

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

    # Wipe the file clean if it already exists, otherwise the existing content will mess with the watchdog logger.
    solver_log_path.open("w").close()
    solver_log_handler = FileChangeHandler(logger, solver_log_path)

    # Small logger just to print the solver output to the main logger
    def solver_log_observer(new_lines):
        for line in new_lines:
            logger.debug("", new_line=line)

    # solver_log_handler.register_observer(solver_log_observer)

    # observer = Observer()
    # observer.schedule(solver_log_handler, str(solver_log_path.parent), recursive=False)
    # observer.start()
    logger.info("Running solver...")
    opt_log = OptimizationLog(
        opt_config=config
    )

    opt_log.started()
    results: SolverResults = solver.solve(
        model,
        keepfiles=True,
        logfile=str(solver_log_path.absolute())
    )
    logger.info(f"The solver has exited. Status: {results.solver.status}")
    # logger.debug("Stopping observer...")
    # observer.stop()
    # logger.debug("Observer stopped. Joining observer thread...")
    # observer.join()
    # logger.debug("Observer thread joined.")

    solver_ok = results.solver.status == SolverStatus.ok
    solver_reached_optimality = results.solver.termination_condition == TerminationCondition.optimal
    solver_reached_time_limit = results.solver.termination_condition == TerminationCondition.maxTimeLimit

    opt_log.finished(solver_ok, solver_reached_optimality, solver_reached_time_limit)
    opt_log.log = solver_log_handler.read_file()

    config.optimization_log = opt_log

    if not solver_ok:
        # todo decide what to do in case of failure
        logger.error(f"Solver encountered an error. Solver status: {results.solver.status}")
        return

    if solver_reached_optimality or solver_reached_time_limit:
        # todo return also the reason why the solver stopped
        morning_commissions, afternoon_commissions = await generate_commissions_from_model(config, model, db_session)
        config.commissions = morning_commissions + afternoon_commissions
        return
    else:
        # todo decide what to do in case of failure
        logger.error(f"Solver failed to reach optimality. Solver status: {results.solver.status}")
        return


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

    # commission: int
    for commission_id, commission in enumerate(commission_model):
        new_commission = SolutionCommission(morning=morning, duration=0)

        for index, professor in cast(DataFrame, model.docenti).iterrows():
            if value(model.z[professor['Relatore'], commission]) > 0.8:
                professor_id = int(professor['ID'])
                session_professor = await session_prof_repo.get_one(
                    SessionProfessor.professor_id == professor_id,
                    SessionProfessor.session_id == session_id
                )

                if session_professor is None:
                    raise RuntimeError("Missing Session Professor entry")

                new_commission.professors.append(session_professor)

        for candidate in cast(Iterable[int], model.candidati):
            if value(model.x[candidate, commission]) > 0.8:
                session_candidate = await students_repo.get(int(candidate))

                new_commission.students.append(session_candidate)
                new_commission.duration += int(model.tesisti['Durata'][candidate])

        commissions.append(new_commission)

    # Let's filter out the commissions that aren't used
    used_commissions = [comm for comm in commissions if comm.duration > 0]

    # Now we assign the ID to the commissions
    for index, comm in enumerate(used_commissions):
        comm.order_key = index + commission_count_offset

    return used_commissions
