import concurrent.futures.process
import logging
import os
import pathlib
import uuid

import sqlalchemy.exc
from dotenv import dotenv_values
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from http import HTTPStatus
import pandas as pd
from sqlalchemy.orm import Session

from model import TimeAvailability
from model.model import Student, Commission, Professor, CommissionEntry, \
    OptimizationConfiguration, SolutionCommission
from model.enums import Degree, UniversityRole, SolverEnum
from session_maker import SessionMakerSingleton
from utils.logging import is_valid_log_level

app = Flask(__name__)

app.secret_key = 'key'

HOST_NAME = "0.0.0.0"
HOST_PORT = 5000

SERVER_PROCESS_NAME = "server"
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'details': "Nessun file specificato"}), HTTPStatus.BAD_REQUEST

    file = request.files['file']

    # If the user does not select a file, the browser submits an empty file without a filename.
    # Because of this, we need to check if the filename is empty to avoid errors.
    if file.filename == '':
        return jsonify({'details': 'No selected file'}), HTTPStatus.BAD_REQUEST

    try:
        excel = pd.read_excel(file).fillna('None')

        # Check if the file has ALL the expected columns
        expected_columns = {'MATRICOLA', 'COGNOME', 'NOME', 'CELLULARE', 'EMAIL', 'EMAIL_ATENEO',
                            'TIPO_CORSO_DESCRIZIONE', 'REL_COGNOME', 'REL_NOME', 'REL2_COGNOME', 'REL2_NOME',
                            'CONTROREL_COGNOME', 'CONTROREL_NOME'}
        actual_columns = set([col.upper() for col in excel.columns])
        missing_columns = expected_columns - actual_columns

        if len(missing_columns) > 0:
            return jsonify({
                'error': 'Some expected columns are missing',
                'missing_columns': list(missing_columns)
            }), HTTPStatus.UNPROCESSABLE_ENTITY

        # The actual processing of the file, creating the objects and adding them to the database
        session_maker = SessionMakerSingleton.get_session_maker()
        commission_name = request.form.get('title') or file.filename.removesuffix(".xlsx").removesuffix(".xls")

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

            return jsonify({
                'success': 'File processed successfully',
                'commission': {
                    'id': commission.id,
                    'title': commission.title
                }
            }), HTTPStatus.CREATED

    except Exception as e:
        print(e)
        return jsonify({'error': 'Error processing the file', 'details': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/commissions', methods=['GET'])
def get_commissions():
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        session: Session
        with session_maker.begin() as session:
            commissions = session.query(Commission).all()
            return jsonify([c.serialize() for c in commissions]), HTTPStatus.OK

    except Exception as e:
        print(e)
        return jsonify({
            'error': 'Error retrieving the commissions',
            'details': str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/commission', defaults={'cid': None}, methods=['GET'])
@app.route('/commission/<cid>', methods=['GET'])
def get_commission(cid: int | None):
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        session: Session
        with session_maker.begin() as session:
            if cid is None:
                # No ID provided, return all commissions
                commissions = session.query(Commission.id, Commission.title).all()
                return jsonify([{'id': cid, 'title': title} for cid, title in commissions]), HTTPStatus.OK
            else:
                # ID provided, return specific commission
                commission = session.query(Commission).filter_by(id=cid).first()
                if commission is None:
                    return jsonify({'error': 'Commission not found'}), HTTPStatus.NOT_FOUND
                else:
                    # noinspection PyArgumentList
                    return jsonify(commission.serialize()), HTTPStatus.OK

    except Exception as e:
        print(e)
        return jsonify({
            'error': 'Error retrieving the commission',
            'details': str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/commission/<cid>/configuration', defaults={'config_id': None}, methods=['GET'])
@app.route('/commission/<cid>/configuration/<config_id>', methods=['GET'])
def get_configuration(cid: int, config_id: int | None):
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        with session_maker.begin() as session:
            if config_id is None:
                # No ID provided, return all configurations for the commission
                configurations: list[OptimizationConfiguration] = (
                    session.query(OptimizationConfiguration)
                    .filter_by(commission_id=cid)
                    .all()
                )
                return jsonify([c.serialize() for c in configurations]), HTTPStatus.OK
            else:
                # ID provided, return specific configuration
                configuration = (
                    session.query(OptimizationConfiguration)
                    .filter_by(id=config_id, commission_id=cid)
                    .first()
                )
                if configuration is None:
                    return jsonify({'error': 'Configuration not found'}), HTTPStatus.NOT_FOUND
                else:
                    return jsonify(configuration.serialize()), HTTPStatus.OK

    except Exception as e:
        print(e)
        return jsonify({
            'error': 'Error retrieving the configuration',
            'details': str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/commission/<cid>/configuration', methods=['POST'])
def create_configuration(cid: int):
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

            return jsonify({
                'success': 'Configuration created',
                'id': configuration.id,
                'title': title,
                'new_config': configuration.serialize()
            }), HTTPStatus.CREATED

    except Exception as e:
        print(e)
        return jsonify({
            'error': 'Error creating the configuration',
            'details': str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/commission/<cid>/configuration/<config_id>', methods=['PUT'])
def update_configuration(cid: int, config_id: int):
    logger = logging.getLogger(SERVER_PROCESS_NAME)
    session_maker = SessionMakerSingleton.get_session_maker()

    logger.debug(f"Updating configuration {config_id} for commission {cid}")

    try:
        session: Session
        with session_maker.begin() as session:
            configuration = session.query(OptimizationConfiguration).filter_by(id=config_id, commission_id=cid).first()
            if configuration is None:
                logger.error(f"Configuration with ID {config_id} not found")
                return jsonify({'error': 'Configuration not found'}), HTTPStatus.NOT_FOUND

            if configuration.run_lock:
                if session.query(SolutionCommission).filter_by(opt_config_id=config_id).count() > 0:
                    logger.error(f"Configuration with ID {config_id} already solved")
                    return jsonify({
                        'error': 'Configuration already solved',
                        'state': 'solved'
                    }), HTTPStatus.CONFLICT
                else:
                    logger.error(f"Configuration with ID {config_id} is currently being solved")
                    return jsonify({
                        'error': 'Configuration is currently being solved',
                        'state': 'solving'
                    }), HTTPStatus.CONFLICT

            new_config: dict = request.get_json()

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

                if (configuration.min_professor_number is None or
                        configuration.max_professor_number is None or
                        configuration.min_professor_number_masters is None):
                    session.rollback()
                    return jsonify({
                        'error': 'min_professor_number, max_professor_number and min_professor_number_masters must be '
                                 'specified'
                    }), HTTPStatus.BAD_REQUEST
                elif configuration.min_professor_number > configuration.max_professor_number:
                    session.rollback()
                    return jsonify({
                        'error': 'min_professor_number must be less than or equal to max_professor_number'
                    }), HTTPStatus.BAD_REQUEST
                elif configuration.min_professor_number_masters > configuration.max_professor_number:
                    session.rollback()
                    return jsonify({
                        'error': 'min_professor_number_masters must be less than or equal to max_professor_number'
                    }), HTTPStatus.BAD_REQUEST
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
                    return jsonify({
                        'error': 'Invalid solver specified',
                        'valid_solvers': [solver.name for solver in SolverEnum]
                    }), HTTPStatus.BAD_REQUEST

            configuration.optimization_time_limit = new_config.get('optimization_time_limit',
                                                                   configuration.optimization_time_limit)
            configuration.optimization_gap = new_config.get('optimization_gap', configuration.optimization_gap)

            return jsonify({
                'success': 'Configuration updated',
                'updated_config': configuration.serialize()
            }), HTTPStatus.OK

    except Exception as e:
        logger.exception("Error updating the configuration", exc_info=e)
        return jsonify({
            'error': 'Error updating the configuration',
            'details': str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/professor/<pid>', methods=['PUT'])
def update_professor(pid: int):
    session_maker = SessionMakerSingleton.get_session_maker()

    professor: Professor | None = None
    try:
        with session_maker.begin() as session:
            professor = session.query(Professor).filter_by(id=pid).first()
            if professor is None:
                return jsonify({'error': f'Professor with ID {pid} not found'}), HTTPStatus.NOT_FOUND

            new_role: str = request.json.get('role')
            if new_role is not None:
                if new_role == "":
                    return jsonify({'error': 'No role specified'}), HTTPStatus.BAD_REQUEST

                professor.role = UniversityRole(new_role)

            new_availability: str = request.json.get('availability')
            if new_availability is not None:
                if new_role == "":
                    return jsonify({'error': 'No availability specified'}), HTTPStatus.BAD_REQUEST

                professor.availability = TimeAvailability(new_availability)

            return jsonify({
                'professor': professor.serialize(),
                'response': f"Professor {professor.name} {professor.surname} ({pid}) updated"
            }), HTTPStatus.OK

    except Exception as e:
        print(e)
        return jsonify({'error': 'Error updating the professor', 'details': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/commission/<cid>', methods=['DELETE'])
def delete_commission(cid: int):
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        with session_maker.begin() as session:
            commission = session.query(Commission).filter_by(id=cid).first()
            if commission is None:
                return jsonify({'error': f'Commission with ID {cid} not found'}), HTTPStatus.NOT_FOUND

            session.delete(commission)

            return jsonify(f"Commission {cid} deleted"), HTTPStatus.OK

    except Exception as e:
        print(e)
        return jsonify({'error': 'Error deleting the commission', 'details': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


# Path to the directories that hold the datfiles and solutions produced.
# Inside this directory there is a directory with this structure:
# temp
# |- [problem_id] - [config_id] --- cfg.dat
# |_ ...                         |_ model.lp
#                                |_ val.xls
OPT_TMP_DIR = ".temp/"


@app.route('/commission/<commission_id>/solve/<config_id>', methods=['POST'])
def solve_commission(commission_id: int, config_id: int):
    logger = logging.getLogger(SERVER_PROCESS_NAME)

    logger.info(f"Received request to solve commission {commission_id} with configuration {config_id}")
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        with session_maker.begin() as session:
            logger.debug(f"Retrieving commission {commission_id} and configuration {config_id}")
            commission: Commission = session.query(Commission).filter_by(id=commission_id).first()
            if commission is None:
                logger.error(f"Commission with ID {commission_id} not found")
                return jsonify({'error': f'Commission with ID {commission_id} not found'}), HTTPStatus.NOT_FOUND

            configuration: OptimizationConfiguration = (
                session.query(OptimizationConfiguration)
                .filter_by(id=config_id)
                .first()
            )

            if configuration is None:
                logger.error(f"Configuration with ID {config_id} not found")
                return jsonify({'error': f'Configuration with ID {config_id} not found'}), HTTPStatus.NOT_FOUND

            # First we check if the configuration has already been solved
            if session.query(SolutionCommission).filter_by(opt_config_id=config_id).count() > 0:
                logger.error(f"Configuration with ID {config_id} already solved")
                return jsonify({'error': f'Configuration with ID {config_id} already solved'}), HTTPStatus.CONFLICT

            # Then we check if the configuration is already running. If we're here, we're sure that we haven't saved a
            # solution yet.
            # todo we should return another kind of error if the lock is set but there is no future currently running
            if configuration.run_lock:
                logger.error(f"Configuration with ID {config_id} is already running")
                return jsonify({'error': f'Configuration with ID {config_id} is already running'}), HTTPStatus.CONFLICT

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

            global executor
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

            future: concurrent.futures.Future = executor.submit(
                configuration.solver_wrapper,
                cc_path,
                version_hash,
                process_logger
            )
            logger.info(f"Optimization process started for commission {commission_id} and configuration {config_id}")

            return jsonify({
                'success': 'Optimization started',
                'future_id': id(future),
                'uuid': process_uuid,
                'version_hash': version_hash
            }), HTTPStatus.ACCEPTED

    except Exception as e:
        logger.exception(
            f"Error starting the optimization for commission {commission_id} and configuration {config_id}",
            exc_info=e
        )

        return jsonify({
            'error': 'Error starting the optimization',
            'details': str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Needed to fix Preflight Checks for CORS.
# https://github.com/corydolphin/flask-cors/issues/292#issuecomment-883929183
@app.before_request
def basic_authentication():
    if request.method.upper() == 'OPTIONS':
        return Response()


def main():
    global executor

    executor = concurrent.futures.ProcessPoolExecutor(max_workers=int(config.get("MAX_WORKERS", "4")))
    app.run(host=HOST_NAME, port=HOST_PORT, debug=True)


if __name__ == '__main__':
    executor: concurrent.futures.process.ProcessPoolExecutor

    config = dotenv_values(verbose=True)

    sqla_log_level = config.get("DATABASE_LOGGING_LEVEL", "WARNING")
    if not is_valid_log_level(sqla_log_level):
        raise ValueError(f"Invalid logging level for database: {sqla_log_level}. "
                         f"Available levels are: {list(logging.getLevelNamesMapping().keys())}")
    logging.getLogger("sqlalchemy.engine").setLevel(sqla_log_level)

    server_log_level = config.get("SERVER_LOGGING_LEVEL", "DEBUG")
    if not is_valid_log_level(server_log_level):
        raise ValueError(f"Invalid logging level for server: {server_log_level}. "
                         f"Available levels are: {list(logging.getLevelNamesMapping().keys())}")
    server_logger = logging.getLogger(SERVER_PROCESS_NAME)
    server_logger.setLevel(server_log_level)
    handler = logging.StreamHandler()
    handler.setFormatter(FORMATTER)
    server_logger.addHandler(handler)

    db_url = sqlalchemy.URL.create("postgresql",
                                   username=config["DB_USER"],
                                   password=config["DB_PASSWORD"],
                                   host=config["DB_HOST"],
                                   port=config["DB_PORT"],
                                   database=config["DB_NAME"])


    def run_migrations(url: sqlalchemy.engine.url.URL):
        from alembic import command
        from alembic.config import Config

        logger = logging.getLogger(SERVER_PROCESS_NAME)

        logger.info("Running database migrations")
        # preload the configuration file for the migrations, we have to adjust the database url.
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False))
        logger.debug("alembic.ini loaded")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied")


    run_migrations(db_url)

    SessionMakerSingleton.initialize(db_url)

    CORS(app, origins=[os.getenv("PUBLIC_API_URL"), os.getenv("PUBLIC_WEB_URL")])
    main()
