import logging

import sqlalchemy.exc
from sqlalchemy import create_engine
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pandas as pd
from sqlalchemy.orm import sessionmaker

from model.model import mapper_registry, Student, Commission

app = Flask(__name__)

app.secret_key = 'key'

HOST_NAME = "0.0.0.0"
HOST_PORT = 5000


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': "No file part"}), 400

    file = request.files['file']

    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        excel = pd.read_excel(file)

        expected_columns = {'MATRICOLA', 'COGNOME', 'NOME', 'CELLULARE', 'EMAIL', 'EMAIL_ATENEO',
                            'TIPO_CORSO_DESCRIZIONE', 'REL_COGNOME', 'REL_NOME', 'REL2_COGNOME', 'REL2_NOME',
                            'CONTROREL_COGNOME', 'CONTROREL_NOME'}
        actual_columns = set([col.upper() for col in excel.columns])
        missing_columns = expected_columns - actual_columns

        if len(missing_columns) > 0:
            return jsonify({
                'error': 'Some expected columns are missing',
                'missing_columns': list(missing_columns)
            }), 422

        global Session

        with Session.begin() as session:
            commission = Commission("Nuova commissione")

            for index, row in excel.iterrows():
                print(row)

                entry = CommissionEntry(
                    candidate=Student(
                        matriculation_number=row['MATRICOLA'],
                        name=row['NOME'],
                        surname=row['COGNOME'],
                        phone_number=row['CELLULARE'],
                        personal_email=row['EMAIL'],
                        university_email=row['EMAIL_ATENEO']
                    )
                )

                student = Student(
                    matriculation_number=row['MATRICOLA'],
                    name=row['NOME'],
                    surname=row['COGNOME'],
                    phone_number=row['CELLULARE'],
                    personal_email=row['EMAIL'],
                    university_email=row['EMAIL_ATENEO']
                )




    except Exception as e:
        print(e)
        return jsonify({'error': 'Error processing the file', 'details': str(e)}), 500


# Needed to fix Preflight Checks for CORS.
# https://github.com/corydolphin/flask-cors/issues/292#issuecomment-883929183
@app.before_request
def basic_authentication():
    if request.method.upper() == 'OPTIONS':
        return Response()


def main():
    global engine

    mapper_registry.metadata.create_all(engine)
    app.run(host=HOST_NAME, port=HOST_PORT, debug=True)


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    engine = create_engine('postgresql://user:password@localhost:5432/postgres')
    Session = sessionmaker(engine)
    CORS(app, origins=["http://localhost:5000", "http://localhost:5173"])
    main()
