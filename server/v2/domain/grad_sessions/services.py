from pathlib import Path

import structlog
from litestar import status_codes as http_statuses
from litestar.exceptions import HTTPException
from pyomo.core import AbstractModel
from pyomo.opt import SolverFactory, SolverResults, SolverStatus, TerminationCondition, OptSolver
from watchdog.observers import Observer

from optimization.models import create_min_durata_model, create_max_durata_model
from utils import FileChangeHandler
from v2.db.models import GradSession, OptimizationConfiguration, SolverEnum, OptimizationLog, SolutionCommission
from v2.domain.grad_sessions.deps import GradSessionRepository, OptimizationConfigurationRepository

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

    if not await graduation_session_repo.exists(GradSession.id == session_id):
        logger.error(f"Session with ID {session_id} not found")

        raise HTTPException(
            detail="The specified Graduation Session does not exist",
            status_code=http_statuses.HTTP_404_NOT_FOUND
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
    config: OptimizationConfiguration | None = await optimization_configuration_repo.get_one_or_none(
        OptimizationConfiguration.id == configuration_id,
        OptimizationConfiguration.session_id == session_id,
    )
    if config is None:
        logger.error(f"Configuration with ID {configuration_id} (SID {session_id}) not found")
        raise HTTPException("Configuration not found", status_code=http_statuses.HTTP_404_NOT_FOUND)
    return config


async def solver_wrapper(config: OptimizationConfiguration, cc_path: Path):
    logger.info(f"Starting optimization for commission with ID {config.session_id}")

    try:
        await solve_model(config, cc_path)
    except Exception as e:
        logger.error(f"An error occurred while solving the optimization problem: {e}", e)
    else:
        logger.info("Optimization completed and correctly saved to database.")


async def solve_model(config: OptimizationConfiguration, cc_path: Path):
    dat_path = cc_path / "temp.dat"

    model: AbstractModel
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

    solver_arguments = dict()
    solver_arguments['options'] = dict()

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

    observer = Observer()
    observer.schedule(solver_log_handler, str(solver_log_path.parent), recursive=False)
    observer.start()
    logger.info("Running solver...")
    opt_log = OptimizationLog(
        opt_config_id=config.id
    )

    results: SolverResults = solver.solve(
        model,
        keepfiles=True,
        logfile=str(solver_log_path.absolute())
    )
    logger.info(f"The solver has exited. Status: {results.solver.status}")
    logger.debug("Stopping observer...")
    observer.stop()
    logger.debug("Observer stopped. Joining observer thread...")
    observer.join()
    logger.debug("Observer thread joined.")

    solver_ok = results.solver.status == SolverStatus.ok
    solver_reached_optimality = results.solver.termination_condition == TerminationCondition.optimal
    solver_reached_time_limit = results.solver.termination_condition == TerminationCondition.maxTimeLimit

    # opt_log.finished(solver_ok, solver_reached_optimality, solver_reached_time_limit)
    opt_log.log = solver_log_handler.read_file()

    # todo save on DB

    if not solver_ok:
        # todo decide what to do in case of failure
        logger.error(f"Solver encountered an error. Solver status: {results.solver.status}")
        return None

    if solver_reached_optimality or solver_reached_time_limit:
        # todo return also the reason why the solver stopped
        return generate_commissions_from_model(config, model)
    else:
        # todo decide what to do in case of failure
        logger.error(f"Solver failed to reach optimality. Solver status: {results.solver.status}")
        return None


def generate_commissions_from_model(
        config: OptimizationConfiguration,
        model: AbstractModel
) -> tuple[list[SolutionCommission], list[SolutionCommission],]:
    pass