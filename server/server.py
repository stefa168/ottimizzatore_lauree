import concurrent.futures.process
import logging
import pathlib

import sqlalchemy.exc
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from http import HTTPStatus
import pandas as pd
from sqlalchemy.orm import Session

from model.model import mapper_registry, Student, Commission, Professor, CommissionEntry, \
    OptimizationConfiguration
from model.enums import Degree, UniversityRole
from session_maker import SessionMakerSingleton

app = Flask(__name__)

app.secret_key = 'key'

HOST_NAME = "0.0.0.0"
HOST_PORT = 5000


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

        commission_id: int | None = None

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

            commission_id = commission.id

    except Exception as e:
        print(e)
        return jsonify({'error': 'Error processing the file', 'details': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
    else:
        return jsonify({
            'success': 'File processed successfully',
            'name': commission_name,
            'id': commission_id
        }), HTTPStatus.OK


@app.route('/commission', defaults={'cid': None}, methods=['GET'])
@app.route('/commission/<cid>', methods=['GET'])
def get_commission(cid: int | None):
    session_maker = SessionMakerSingleton.get_session_maker()

    try:
        if cid is None:
            # No ID provided, return all commissions
            with session_maker.begin() as session:
                commissions = session.query(Commission.id, Commission.title).all()
                return jsonify([{'id': cid, 'title': title} for cid, title in commissions]), HTTPStatus.OK
        else:
            # ID provided, return specific commission
            with session_maker.begin() as session:
                commission = session.query(Commission).filter_by(id=cid).first()
                if commission is None:
                    return jsonify({'error': 'Commission not found'}), HTTPStatus.NOT_FOUND
                else:
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
            configuration = OptimizationConfiguration(cid, "Nuova configurazione")
            session.add(configuration)
            # needed to actually have the database generate the ID
            session.flush()

            new_id = configuration.id
            title = f"{configuration.title} {new_id}"

            configuration.title = title
            session.commit()

            return jsonify({'success': 'Configuration created', 'id': new_id, 'title': title}), HTTPStatus.CREATED

    except Exception as e:
        print(e)
        return jsonify({
            'error': 'Error creating the configuration',
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

            new_role = request.json.get('role')
            if new_role is None or new_role == "":
                return jsonify({'error': 'No role specified'}), HTTPStatus.BAD_REQUEST

            professor.role = UniversityRole(new_role)

            return jsonify(f"Role for professor {professor.name} {professor.surname} ({pid}) updated"), HTTPStatus.OK

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
    session_maker = SessionMakerSingleton.get_session_maker()

    # retrieve the Commission data from the database
    # for now we don't have a configuration data model, so we just ignore the config_id
    try:
        with session_maker.begin() as session:
            commission: Commission = session.query(Commission).filter_by(id=commission_id).first()
            if commission is None:
                return jsonify({'error': f'Commission with ID {commission_id} not found'}), HTTPStatus.NOT_FOUND

            configuration: OptimizationConfiguration = (
                session.query(OptimizationConfiguration)
                .filter_by(id=config_id)
                .first()
            )
            if configuration is None:
                return jsonify({'error': f'Configuration with ID {config_id} not found'}), HTTPStatus.NOT_FOUND

            # todo lock the commission and configuration to avoid concurrent optimization

            base_path = pathlib.Path(OPT_TMP_DIR)
            cc_path = base_path / str(commission_id) / str(config_id)

            # We create the configuration file
            configuration.create_dat_file(cc_path)
            # And also the datafile
            # noinspection PyArgumentList
            commission.export_xls(cc_path)

            version_hash = configuration.hash()
            session.expunge(configuration)

            global executor
            # We start the optimization
            # todo save the future object in a dictionary to be able to interact with it later
            future = executor.submit(configuration.solver_wrapper, cc_path, version_hash)

            return jsonify({'success': 'Optimization started', 'future_id': id(future)}), HTTPStatus.ACCEPTED

    except Exception as e:
        print(e)
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

    mapper_registry.metadata.create_all(SessionMakerSingleton.get_engine())
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)
    app.run(host=HOST_NAME, port=HOST_PORT, debug=True)


if __name__ == '__main__':
    executor: concurrent.futures.process.ProcessPoolExecutor

    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    SessionMakerSingleton.initialize("postgresql://user:password@localhost:5432/postgres")

    CORS(app, origins=["http://localhost:5000", "http://localhost:5173"])
    main()
