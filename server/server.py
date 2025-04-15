import concurrent.futures.process
import logging
import os
import pathlib
import uuid
from functools import lru_cache
from typing import Annotated, TypedDict
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor

import pydantic.networks
import sqlalchemy.exc
from fastapi import FastAPI, File, status, UploadFile, HTTPException, Form, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import pandas as pd
from sqlalchemy.orm import Session

from model import TimeAvailability
from model.model import Student, Commission, Professor, CommissionEntry, OptimizationConfiguration, SolutionCommission
from model.enums import Degree, UniversityRole, SolverEnum
from session_maker import SessionMakerSingleton
from utils.logging import is_valid_log_level

SERVER_PROCESS_NAME = "server"
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Settings(BaseSettings):
    public_api_url: Annotated[str, pydantic.networks.HttpUrl]
    public_web_url: Annotated[str, pydantic.networks.HttpUrl]

    database_logging_level: str = "WARNING"
    server_logging_level: str = "INFO"

    db_url: Annotated[sqlalchemy.engine.url.URL, pydantic.networks.PostgresDsn]

    max_workers: int = 4

    model_config = SettingsConfigDict(env_file=".env")

    def get_origins(self) -> list[str]:
        return [self.public_api_url, self.public_web_url]


@lru_cache
def get_settings():
    return Settings()


class ServerState:
    executor: ProcessPoolExecutor

    def __init__(self, executor: ProcessPoolExecutor):
        self.executor = executor


server_state: ServerState | None = None


def run_migrations(url: sqlalchemy.engine.url.URL):
    from alembic import command
    from alembic.config import Config
    # https://stackoverflow.com/questions/77170361/running-alembic-migrations-on-fastapi-startup

    logger = logging.getLogger(SERVER_PROCESS_NAME)

    logger.info("Running database migrations")
    # preload the configuration file for the migrations, we have to adjust the database url.
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False))
    logger.debug("alembic.ini loaded")
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    executor = ProcessPoolExecutor(max_workers=settings.max_workers)

    # todo migrate to new logging structure https://www.restack.io/p/fastapi-answer-logger-dependency
    if not is_valid_log_level(settings.database_logging_level):
        raise ValueError(f"Invalid logging level for database: {settings.database_logging_level}. "
                         f"Available levels are: {list(logging.getLevelNamesMapping().keys())}")
    logging.getLogger("sqlalchemy.engine").setLevel(settings.database_logging_level)

    if not is_valid_log_level(settings.server_logging_level):
        raise ValueError(f"Invalid logging level for server: {settings.server_logging_level}. "
                         f"Available levels are: {list(logging.getLevelNamesMapping().keys())}")
    server_logger = logging.getLogger(SERVER_PROCESS_NAME)
    server_logger.setLevel(settings.server_logging_level)
    handler = logging.StreamHandler()
    handler.setFormatter(FORMATTER)
    server_logger.addHandler(handler)

    SessionMakerSingleton.initialize(settings.db_url)
    run_migrations(settings.db_url)

    # noinspection PyTypeChecker
    app.add_middleware(
        # https://github.com/fastapi/fastapi/discussions/10968
        CORSMiddleware,
        allow_origins=settings.get_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    global server_state
    server_state = ServerState(executor)

    yield

    server_logger.info("Shutting down")
    server_state.executor.shutdown(wait=True, cancel_futures=True)


app = FastAPI(lifespan=lifespan)


@app.post('/upload', status_code=status.HTTP_201_CREATED)
def upload_file(file: Annotated[UploadFile, File(description="Source Spreadsheet file for the graduation")],
                title: Annotated[str | None, Form(description="Title for the graduation commission")]) -> Commission:
    # if 'file' not in request.files:
    #     return jsonify({'details': "Nessun file specificato"}), HTTPStatus.BAD_REQUEST
    #
    # file = request.files['file']

    # If the user does not select a file, the browser submits an empty file without a filename.
    # Because of this, we need to check if the filename is empty to avoid errors.
    if file.filename == '':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No selected file")

    try:
        excel = pd.read_excel(file).fillna('None')

        # Check if the file has ALL the expected columns
        expected_columns = {'MATRICOLA', 'COGNOME', 'NOME', 'CELLULARE', 'EMAIL', 'EMAIL_ATENEO',
                            'TIPO_CORSO_DESCRIZIONE', 'REL_COGNOME', 'REL_NOME', 'REL2_COGNOME', 'REL2_NOME',
                            'CONTROREL_COGNOME', 'CONTROREL_NOME'}
        actual_columns = set([col.upper() for col in excel.columns])
        missing_columns = expected_columns - actual_columns

        if len(missing_columns) > 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail={
                                    'error': 'Some expected columns are missing',
                                    'missing_columns': list(missing_columns)
                                })

        # The actual processing of the file, creating the objects and adding them to the database
        session_maker = SessionMakerSingleton.get_session_maker()
        commission_name = title or file.filename.removesuffix(".xlsx").removesuffix(".xls")

        def get_or_create_professor(ext_session: Session, name: str, surname: str):
            """
            This function checks if a professor exists in the database by their name and surname.
            If the professor exists, it returns the professor object.
            If the professor does not exist, it creates a new professor with the given name and surname,
            and an unspecified role. The new professor is added to the session, and the function returns
            the new professor object.

            If either the name or surname is None, the function returns None. This is because both a name
            and a surname are required to identify a professor.

            Note: The role of a new professor is set to 'unspecified' by default.

            Args:
                ext_session (sqlalchemy.orm.session.Session): The session to use for querying the database.
                name (str): The name of the professor. If this is None, the function returns None.
                surname (str): The surname of the professor. If this is None, the function returns None.

            Returns:
                Professor: The existing or newly created professor object, or None if either name or surname is None.
            """
            if name is None or surname is None or name == "" or surname == "" or name == "None" or surname == "None":
                return None

            try:
                prof = ext_session.query(Professor).filter_by(name=name, surname=surname).one()
            except sqlalchemy.exc.NoResultFound:
                prof = Professor(name, surname, UniversityRole.UNSPECIFIED)
                ext_session.add(prof)
            return prof

        session: Session

        # Automatically commit the transaction if no exception is raised
        with session_maker.begin() as session:
            commission = Commission(title=commission_name)
            session.add(commission)

            for index, row in excel.iterrows():
                print(row)

                # Create a new student object
                student = Student(
                    matriculation_number=row['MATRICOLA'],
                    name=row['NOME'],
                    surname=row['COGNOME'],
                    phone_number=row['CELLULARE'],
                    personal_email=row['EMAIL'],
                    university_email=row['EMAIL_ATENEO']
                )
                session.add(student)

                # Retrieve or create the professors
                professor = get_or_create_professor(session, row['REL_NOME'], row['REL_COGNOME'])
                professor2 = get_or_create_professor(session, row['REL2_NOME'], row['REL2_COGNOME'])
                counter_supervisor = get_or_create_professor(session, row['CONTROREL_NOME'], row['CONTROREL_COGNOME'])

                # lowercase contains "magistrale" then it's a master degree
                if "magistrale" in row['TIPO_CORSO_DESCRIZIONE'].lower():
                    degree = Degree.MASTERS
                else:
                    degree = Degree.BACHELORS

                # Create a new commission entry
                entry = CommissionEntry(
                    candidate=student,
                    degree_level=degree,
                    supervisor=professor,
                    supervisor_assistant=professor2,
                    counter_supervisor=counter_supervisor
                )
                session.add(entry)

                # Add the student and the commission entry to the session
                commission.entries.append(entry)

            session.flush()

            return commission

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={
                                'error': 'Error processing the file',
                                'details': str(e)
                            })


@app.get('/commissions')
def get_commissions() -> list[Commission]:
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        session: Session
        with session_maker.begin() as session:
            commissions = session.query(Commission).all()
            return commissions

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={
                                'error': 'Error retrieving the commissions',
                                'details': str(e)
                            })


class BasicCommissionDetails:
    id: int
    title: str

    def __init__(self, id: int, title: str):
        self.id = id
        self.title = title


# @app.get('/commission', defaults={'cid': None})
@app.get('/commission/{cid}')
def get_commission(cid: Annotated[int | None, Path()]) -> Commission | list[BasicCommissionDetails]:
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        session: Session
        with session_maker.begin() as session:
            if cid is None:
                # No ID provided, return all commissions
                commissions = session.query(Commission.id, Commission.title).all()
                return [BasicCommissionDetails(cid, title) for cid, title in commissions]
            else:
                # ID provided, return specific commission
                commission = session.query(Commission).filter_by(id=cid).first()
                if commission is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND)
                else:
                    return commission

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={
                                'error': 'Error retrieving the commission',
                                'details': str(e)
                            })


@app.get('/commission/{cid}/configuration/{config_id}')
def get_configuration(cid: Annotated[int, Path()],
                      config_id: Annotated[int | None, Path()],
                      ) -> OptimizationConfiguration | list[OptimizationConfiguration]:
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        with session_maker.begin() as session:
            if config_id is None:
                # No ID provided, return all configurations for the commission
                configurations = (
                    session.query(OptimizationConfiguration)
                    .filter_by(commission_id=cid)
                    .all()
                )
                return configurations
            else:
                # ID provided, return specific configuration
                configuration = (
                    session.query(OptimizationConfiguration)
                    .filter_by(id=config_id, commission_id=cid)
                    .first()
                )
                if configuration is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND)
                else:
                    return configuration

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={
                                'error': 'Error retrieving the commission',
                                'details': str(e)
                            })


class CommissionCreationSuccess:
    success: str
    id: int
    title: str
    new_config: OptimizationConfiguration

    def __init__(self, commission_id: int, title: str, config: OptimizationConfiguration):
        self.success = 'Configuration created'
        self.id = commission_id
        self.title = title
        self.new_config = config


@app.post('/commission/{cid}/configuration', status_code=status.HTTP_201_CREATED)
def create_configuration(cid: Annotated[int, Path()]) -> CommissionCreationSuccess:
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        session: Session
        with session_maker.begin() as session:
            # get count of all configurations for the commission
            count = session.query(OptimizationConfiguration).filter_by(commission_id=cid).count()

            configuration = OptimizationConfiguration(cid, "Nuova configurazione")
            session.add(configuration)
            # needed to actually have the database generate the ID
            session.flush()

            title = f"{configuration.title} {count + 1}"

            configuration.title = title
            # session.commit()

            return CommissionCreationSuccess(configuration.id, title, configuration)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={
                                'error': 'Error creating the configuration',
                                'details': str(e)
                            })


# todo add pydantic checks to the fields!
class OptimizationConfigurationUpdateParams(BaseModel):
    title: str | None

    max_duration: int | None
    max_commissions_morning: int | None
    max_commissions_afternoon: int | None

    online: bool | None
    min_professor_number: int | None
    min_professor_number_masters: int | None
    max_professor_numer: int | None

    solver: SolverEnum | None

    optimization_time_limit: int | None
    optimization_gap: float | None


@app.put('/commission/{cid}/configuration/{config_id}')
def update_configuration(cid: Annotated[int, Path()],
                         config_id: Annotated[int, Path()],
                         new_config: OptimizationConfigurationUpdateParams):
    logger = logging.getLogger(SERVER_PROCESS_NAME)
    session_maker = SessionMakerSingleton.get_session_maker()

    logger.debug(f"Updating configuration {config_id} for commission {cid}")

    try:
        session: Session
        with session_maker.begin() as session:
            configuration = session.query(OptimizationConfiguration).filter_by(id=config_id, commission_id=cid).first()
            if configuration is None:
                logger.error(f"Configuration with ID {config_id} not found")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'error': 'Configuration not found'})

            if configuration.run_lock:
                if session.query(SolutionCommission).filter_by(opt_config_id=config_id).count() > 0:
                    logger.error(f"Configuration with ID {config_id} already solved")
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                        'error': 'Configuration already solved',
                        'state': 'solved'
                    })
                else:
                    logger.error(f"Configuration with ID {config_id} is currently being solved")
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                        'error': 'Configuration is currently being solved',
                        'state': 'solving'
                    })

            # new_config: dict = request.get_json()

            configuration.title = new_config.get('title', configuration.title)
            configuration.max_duration = new_config.get('max_duration', configuration.max_duration)
            configuration.max_commissions_morning = new_config.get('max_commissions_morning',
                                                                   configuration.max_commissions_morning)
            configuration.max_commissions_afternoon = new_config.get('max_commissions_afternoon',
                                                                     configuration.max_commissions_afternoon)

            # We need to do some additional checks if the configuration is online
            configuration.online = new_config.get('online', configuration.online)
            if configuration.online:
                configuration.min_professor_number = new_config.get('min_professor_number',
                                                                    configuration.min_professor_number)
                configuration.max_professor_number = new_config.get('max_professor_number',
                                                                    configuration.max_professor_number)
                configuration.min_professor_number_masters = new_config.get('min_professor_number_masters',
                                                                            configuration.min_professor_number_masters)

                # todo remove these checks since the "online" configuration structure will be the only one available.
                # if (configuration.min_professor_number is None or
                #         configuration.max_professor_number is None or
                #         configuration.min_professor_number_masters is None):
                #     session.rollback()
                #     return jsonify({
                #         'error': 'min_professor_number, max_professor_number and min_professor_number_masters must be '
                #                  'specified'
                #     }), HTTPStatus.BAD_REQUEST
                # elif configuration.min_professor_number > configuration.max_professor_number:
                #     session.rollback()
                #     return jsonify({
                #         'error': 'min_professor_number must be less than or equal to max_professor_number'
                #     }), HTTPStatus.BAD_REQUEST
                # elif configuration.min_professor_number_masters > configuration.max_professor_number:
                #     session.rollback()
                #     return jsonify({
                #         'error': 'min_professor_number_masters must be less than or equal to max_professor_number'
                #     }), HTTPStatus.BAD_REQUEST
            else:
                configuration.min_professor_number = None
                configuration.max_professor_number = None
                configuration.min_professor_number_masters = None

            solver_str: str | None = new_config.get('solver', None)
            if solver_str is not None:
                try:
                    configuration.solver = SolverEnum[solver_str.upper()]
                except KeyError:
                    session.rollback()
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={
                        'error': 'Invalid solver specified',
                        'valid_solvers': [solver.name for solver in SolverEnum]
                    })

            configuration.optimization_time_limit = new_config.get('optimization_time_limit',
                                                                   configuration.optimization_time_limit)
            configuration.optimization_gap = new_config.get('optimization_gap', configuration.optimization_gap)

            return configuration

    except Exception as e:
        logger.exception("Error updating the configuration", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            'error': 'Error updating the configuration',
            'details': str(e)
        })


@app.put('/professor/{pid}')
def update_professor(pid: Annotated[int, Path()],
                     role: UniversityRole | None,
                     availability: TimeAvailability | None) -> Professor:
    logger = logging.getLogger(SERVER_PROCESS_NAME)
    session_maker = SessionMakerSingleton.get_session_maker()

    professor: Professor | None = None
    try:
        with session_maker.begin() as session:
            professor = session.query(Professor).filter_by(id=pid).first()
            if professor is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f'Professor with ID {pid} not found')

            if role is not None:
                professor.role = UniversityRole(role)

            if availability is not None:
                professor.availability = availability

            return professor

    except Exception as e:
        logger.exception("Error updating the professor", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            'error': 'Error updating the professor',
            'details': str(e)
        })


@app.delete('/commission/{cid}')
def delete_commission(cid: int):
    logger = logging.getLogger(SERVER_PROCESS_NAME)
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        with session_maker.begin() as session:
            commission = session.query(Commission).filter_by(id=cid).first()
            if commission is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Commission with ID {cid} not found')

            session.delete(commission)

    except Exception as e:
        logger.exception("Error updating the professor", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            'error': 'Error deleting the commission',
            'details': str(e)
        })


# Path to the directories that hold the datfiles and solutions produced.
# Inside this directory there is a directory with this structure:
# temp
# |- [problem_id] - [config_id] --- cfg.dat
# |_ ...                         |_ model.lp
#                                |_ val.xls
OPT_TMP_DIR = ".temp/"


@app.post('/commission/{commission_id}/solve/{config_id}', status_code=status.HTTP_202_ACCEPTED)
def solve_commission(commission_id: int, config_id: int):
    logger = logging.getLogger(SERVER_PROCESS_NAME)

    logger.info(f"Received request to solve commission {commission_id} with configuration {config_id}")
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        with session_maker.begin() as session:
            logger.debug(f"Retrieving commission {commission_id} and configuration {config_id}")
            commission = session.query(Commission).filter_by(id=commission_id).first()
            if commission is None:
                logger.error(f"Commission with ID {commission_id} not found")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f'Commission with ID {commission_id} not found')

            configuration = session.query(OptimizationConfiguration).filter_by(id=config_id).first()

            if configuration is None:
                logger.error(f"Configuration with ID {config_id} not found")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f'Configuration with ID {config_id} not found')

            # First we check if the configuration has already been solved
            if session.query(SolutionCommission).filter_by(opt_config_id=config_id).count() > 0:
                logger.error(f"Configuration with ID {config_id} already solved")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail=f'Configuration with ID {config_id} already solved')

            # Then we check if the configuration is already running. If we're here, we're sure that we haven't saved a
            # solution yet.
            # todo we should return another kind of error if the lock is set but there is no future currently running
            if configuration.run_lock:
                logger.error(f"Configuration with ID {config_id} is already running")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail=f'Configuration with ID {config_id} is already running')

            logger.debug(f"Locking the configuration {config_id}")
            configuration.run_lock = True
            session.flush()

            logger.debug(f"Setting up the optimization for commission {commission_id} and configuration {config_id}")
            base_path = pathlib.Path(OPT_TMP_DIR)
            cc_path = base_path / str(commission_id) / str(config_id)

            # We create the configuration file
            configuration.create_dat_file(cc_path)
            logger.debug(f"Configuration file created at {cc_path}")
            # And also the datafile that will be then loaded back by the optimizer
            # noinspection PyArgumentList
            commission.export_xls(cc_path)

            version_hash = configuration.hash()
            session.expunge(configuration)

            # We start the optimization
            # todo save the future object in a dictionary to be able to interact with it later
            process_uuid = uuid.uuid4()

            process_logger = logger.getChild(str(process_uuid))
            log_path = cc_path / "log.txt"
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(FORMATTER)

            process_logger.addHandler(file_handler)
            # todo add socket/database handler

            future: concurrent.futures.Future = server_state.executor.submit(
                configuration.solver_wrapper,
                cc_path,
                version_hash,
                process_logger
            )
            logger.info(f"Optimization process started for commission {commission_id} and configuration {config_id}")

            return {
                'success': 'Optimization started',
                'future_id': id(future),
                'uuid': process_uuid,
                'version_hash': version_hash
            }

    except Exception as e:
        logger.exception(
            f"Error starting the optimization for commission {commission_id} and configuration {config_id}",
            exc_info=e
        )

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            'error': 'Error starting the optimization',
            'details': str(e)
        })
