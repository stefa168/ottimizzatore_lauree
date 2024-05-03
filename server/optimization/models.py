import pyomo.environ as pyo
import pandas
from pathlib import Path


# noinspection PyUnresolvedReferences
def create_min_durata_model(dat_path: Path) -> pyo.AbstractModel:
    model = pyo.AbstractModel()

    # 1. Parameters
    model.max_durata = pyo.Param()
    model.min_docenti = pyo.Param()
    model.min_docenti_magistrale = pyo.Param()
    model.max_docenti = pyo.Param()

    # 2. Sets
    model.commissioni_mattina = pyo.Set()
    model.commissioni_pomeriggio = pyo.Set()

    model.commissioni = model.commissioni_mattina | model.commissioni_pomeriggio

    # 3. Data
    model.excel_path = pyo.Param(within=pyo.Any)

    # 4. Create the model instance
    model = model.create_instance(str(dat_path))

    # 5. Read the data from the excel file
    # todo move to a csv file
    model.tesisti = pandas.read_excel(pyo.value(model.excel_path), index_col=0, dtype={'Matricola': str})
    # We drop the rows where the column 'Relatore' is not defined
    model.tesisti = model.tesisti.dropna(subset=['Relatore'])

    # 6. Set the candidates
    model.candidati = set(model.tesisti.index)
    model.n_tesisti = len(model.tesisti)

    # 7. Set the supervisors
    # We first load the supervisors, and to avoid duplicates we drop them
    model.relatori = model.tesisti.drop_duplicates(subset='Relatore')
    # todo load also the database IDs corresponding to all the professors
    # Then, we select the columns we are interested in
    model.relatori = model.relatori[['Relatore', 'MATTINA', 'POMERIGGIO', 'Ruolo']]
    # Finally, we rename the columns of the new dataframe
    model.relatori.columns = ['Relatore', 'MATTINA', 'POMERIGGIO', 'tipo']

    # 8. Set the counter-supervisors (the procedure is the same as for the supervisors)
    model.controrelatori = model.tesisti.drop_duplicates(subset='Controrelatore').dropna(subset=['Controrelatore'])
    model.controrelatori = model.controrelatori[['Controrelatore', 'MATTINA', 'POMERIGGIO', 'Ruolo.1']]
    model.controrelatori.columns = ['Relatore', 'MATTINA', 'POMERIGGIO', 'tipo']

    # 9. Set the assistant supervisors
    # model.co_relatori = model.tesisti.drop_duplicates(subset='Co-Relatore').dropna(subset=['Co-Relatore'])
    # model.co_relatori = model.assistanti[['Assistente', 'MATTINA', 'POMERIGGIO', 'Ruolo.2']]
    # model.co_relatori.columns = ['Relatore', 'MATTINA', 'POMERIGGIO', 'tipo']

    # 10. Concatenate the supervisors, counter-supervisors and assistant supervisors
    model.docenti = (
        pandas
        # .concat([model.relatori, model.controrelatori, model.co_relatori], ignore_index=True)
        .concat([model.relatori, model.controrelatori], ignore_index=True)
        .drop_duplicates().reset_index(drop=True)
    )

    # 11. Set the names of the supervisors
    model.nomi_docenti = model.docenti.get('Relatore').array

    # 12. Set the type of the supervisors
    model.is_ordinario = dict()
    model.disponibilita = dict()
    model.durata = dict()

    # 13. Set the duration of the candidates
    for i, t in model.tesisti.iterrows():
        model.durata[i] = t['Durata']

    # 14. Set the role and availability of the supervisors
    for docente in model.nomi_docenti:
        ruolo = (
            model.docenti
            .where(model.docenti['Relatore'] == docente)
            .dropna(subset=['Relatore'])['tipo'].values[0]
        )
        disponibilita_mattino = (
            model.docenti
            .where(model.docenti['Relatore'] == docente)
            .dropna(subset=['Relatore'])['MATTINA'].values[0]
        )
        disponibilita_pomeriggio = (
            model.docenti
            .where(model.docenti['Relatore'] == docente)
            .dropna(subset=['Relatore'])['POMERIGGIO'].values[0]

        )
        if ruolo == 'PO':
            model.is_ordinario[docente] = True
        else:
            model.is_ordinario[docente] = False

        if disponibilita_mattino == 'NO':
            for k in model.commissioni_mattina:
                model.disponibilita[docente, k] = 0
        else:
            for k in model.commissioni_mattina:
                model.disponibilita[docente, k] = 1

        if disponibilita_pomeriggio == 'NO':
            for k in model.commissioni_pomeriggio:
                model.disponibilita[docente, k] = 0
        else:
            for k in model.commissioni_pomeriggio:
                model.disponibilita[docente, k] = 1

    # 15. Define the variables
    model.min_ord = pyo.Var(within=pyo.NonNegativeIntegers)
    model.max_ord = pyo.Var(within=pyo.NonNegativeIntegers)
    # model.min_doc = Var(within=NonNegativeIntegers)

    # 16. Define the binary variables
    model.x = pyo.Var(model.Candidati, model.Commissioni, within=pyo.Binary)
    # y[c] rappresenta se la commissione c e' in uso
    model.y = pyo.Var(model.Commissioni, within=pyo.Binary)
    # y2[c] rappresenta se la commissione c e' magistrale
    model.y2 = pyo.Var(model.Commissioni, within=pyo.Binary)

    model.z = pyo.Var(model.NomiDocenti, model.Commissioni, within=pyo.Binary)

    model.w = pyo.Var(within=pyo.Reals)
    model.w2 = pyo.Var(within=pyo.Reals)

    # 17. Define the objective function
    model.alpha = 10000
    model.beta = 1000
    model.gamma = 10

    def obj_expression(model):
        return + model.alpha * model.w2 - model.beta * model.w \
            + model.gamma * (model.max_ord - model.min_ord) \
            + sum(model.y[k] for k in model.CommissioniPomeriggio)

    model.OBJ = pyo.Objective(rule=obj_expression, sense=pyo.minimize)

    # todo
    raise NotImplementedError


# noinspection PyUnresolvedReferences
def create_max_durata_model(dat_path: Path) -> pyo.AbstractModel:
    model = pyo.AbstractModel()

    # 1. Parameters
    model.max_durata = pyo.Param(within=pyo.Integers)

    # 2. Sets
    model.commissioni_mattina = pyo.Set()
    model.commissioni_pomeriggio = pyo.Set()

    model.commissioni = model.commissioni_mattina | model.commissioni_pomeriggio

    # 3. Data
    model.excel_path = pyo.Param(within=pyo.Any)

    # 4. Create the model instance
    model = model.create_instance(str(dat_path))

    # 5. Read the data from the excel file
    # todo move to a csv file
    model.tesisti = pandas.read_excel(pyo.value(model.excel_path), index_col=0, dtype={'Matricola': str})
    # We drop the rows where the column 'Relatore' is not defined
    model.tesisti = model.tesisti.dropna(subset=['Relatore'])

    # 6. Set the candidates
    model.candidati = set(model.tesisti.index)
    model.n_tesisti = len(model.tesisti)

    # 7. Set the supervisors
    # We first load the supervisors, and to avoid duplicates we drop them
    model.relatori = model.tesisti.drop_duplicates(subset='Relatore')
    # todo load also the database IDs corresponding to all the professors
    # Then, we select the columns we are interested in
    model.relatori = model.relatori[['ID_Relatore', 'Relatore', 'Mattina', 'Pomeriggio', 'Ruolo']]
    # Finally, we rename the columns of the new dataframe
    model.relatori.columns = ['ID', 'Relatore', 'Mattina', 'Pomeriggio', 'tipo']

    # 8. Set the counter-supervisors (the procedure is the same as for the supervisors)
    model.controrelatori = model.tesisti.drop_duplicates(subset='Controrelatore').dropna(subset=['Controrelatore'])
    model.controrelatori = model.controrelatori[
        ['ID_Controrelatore', 'Controrelatore', 'Mattina.1', 'Pomeriggio.1', 'Ruolo.1']
    ]
    model.controrelatori.columns = ['ID', 'Relatore', 'Mattina', 'Pomeriggio', 'tipo']

    # 9. Set the assistant supervisors
    # model.co_relatori = model.tesisti.drop_duplicates(subset='Co-Relatore').dropna(subset=['Co-Relatore'])
    # model.co_relatori = model.assistanti[['Assistente', 'Mattina', 'Pomeriggio', 'Ruolo.2']]
    # model.co_relatori.columns = ['Relatore', 'Mattina', 'Pomeriggio', 'tipo']

    # 10. Concatenate the supervisors, counter-supervisors and assistant supervisors
    model.docenti = (
        pandas
        # .concat([model.relatori, model.controrelatori, model.co_relatori], ignore_index=True)
        .concat([model.relatori, model.controrelatori], ignore_index=True)
        .drop_duplicates().reset_index(drop=True)
    )

    # 11. Set the names of the supervisors
    model.nomi_docenti = model.docenti.get('Relatore').array

    # 12. Set the type of the supervisors
    model.is_ordinario = dict()
    model.disponibilita = dict()
    model.durata = dict()

    # 13. Set the duration of the candidates
    for i, t in model.tesisti.iterrows():
        model.durata[i] = t['Durata']

    # 14. Set the role and availability of the supervisors
    for docente in model.nomi_docenti:
        ruolo = (
            model.docenti
            .where(model.docenti['Relatore'] == docente)
            .dropna(subset=['Relatore'])['tipo'].values[0]
        )
        disponibilita_mattino = (
            model.docenti
            .where(model.docenti['Relatore'] == docente)
            .dropna(subset=['Relatore'])['Mattina'].values[0]
        )
        disponibilita_pomeriggio = (
            model.docenti
            .where(model.docenti['Relatore'] == docente)
            .dropna(subset=['Relatore'])['Pomeriggio'].values[0]

        )
        if ruolo == 'PO':
            model.is_ordinario[docente] = 1
        else:
            model.is_ordinario[docente] = 0

        if disponibilita_mattino == 'NO':
            for k in model.commissioni_mattina:
                model.disponibilita[docente, k] = 0
        else:
            for k in model.commissioni_mattina:
                model.disponibilita[docente, k] = 1

        if disponibilita_pomeriggio == 'NO':
            for k in model.commissioni_pomeriggio:
                model.disponibilita[docente, k] = 0
        else:
            for k in model.commissioni_pomeriggio:
                model.disponibilita[docente, k] = 1

    # 15. Define the variables
    model.min_ord = pyo.Var(within=pyo.NonNegativeIntegers)
    model.max_ord = pyo.Var(within=pyo.NonNegativeIntegers)
    model.min_doc = pyo.Var(within=pyo.NonNegativeIntegers)
    model.max_doc = pyo.Var(within=pyo.NonNegativeIntegers)

    # 16. Define the binary variables
    # X: candidati assegnati a commissione
    model.x = pyo.Var(model.candidati, model.commissioni, within=pyo.Binary)
    # Y: commissione in uso
    model.y = pyo.Var(model.commissioni, within=pyo.Binary)
    # Z: docenti assegnati a commissione
    model.z = pyo.Var(model.nomi_docenti, model.commissioni, within=pyo.Binary)

    # W: massimizzare la durata di ogni singola commissione
    model.w = pyo.Var(within=pyo.Reals)

    # 17. Define the objective function
    model.alpha = 10000
    model.beta = 1000
    model.gamma = 10

    def obj_expression(model):
        return (
                model.alpha * model.w
                - model.beta * (model.max_ord - model.min_ord)
                - model.gamma * (model.max_doc - model.min_doc)
                - sum(model.y[k] for k in model.commissioni_pomeriggio)
        )

    model.OBJ = pyo.Objective(rule=obj_expression, sense=pyo.maximize)

    # 18. Define the constraints
    # 1. tutti i candidati sono assegnati a una commissione
    def all_candidates_c(model, cand):
        return sum(model.x[cand, com] for com in model.commissioni) == 1

    model.allCandCst = pyo.Constraint(model.candidati, rule=all_candidates_c)

    # 2. durata commissioni non deve eccedere la massima durata
    def comm_duration_c(model, com):
        return sum(model.durata[cand] * model.x[cand, com] for cand in model.candidati) <= model.max_durata * model.y[
            com]

    model.commDurCst = pyo.Constraint(model.commissioni, rule=comm_duration_c)

    # 3. massimizzare la durata di ogni singola commissione
    def max_min_c(model, com):
        return sum(model.durata[cand] * model.x[cand, com] for cand in model.candidati) >= \
            model.w - model.max_durata * (1 - model.y[com])

    model.maxMinCst = pyo.Constraint(model.commissioni, rule=max_min_c)

    # 4. Relatori devono essere presenti per la commissione dei loro studenti
    def prof_avail_c(model, t, com):
        rel = model.tesisti['Relatore'][t]
        return model.x[t, com] <= model.disponibilita[rel, com] * model.z[rel, com]

    model.profAvailCst = pyo.Constraint(model.candidati, model.commissioni, rule=prof_avail_c)

    # 4b. Controrelatori devono essere presenti per la commissione dei loro studenti
    def prof2_avail_c(model, t, com):
        rel = model.tesisti['Controrelatore'][t]
        return model.x[t, com] <= model.disponibilita[rel, com] * model.z[rel, com] if pandas.notnull(
            rel) else pyo.Constraint.Feasible

    model.prof2AvailCst = pyo.Constraint(model.candidati, model.commissioni, rule=prof2_avail_c)

    # 5. Ogni docente deve essere al massimo in una commissione
    def prof_comm_c(model, p):
        return sum(model.z[p, com] for com in model.commissioni) <= 1

    model.profCommCst = pyo.Constraint(model.nomi_docenti, rule=prof_comm_c)

    # 6. min_ord deve essere il minimo numero di docenti ordinari per ogni commissione
    def prof_min_ord_c(model, com):
        return sum(model.z[p, com] * model.is_ordinario[p] for p in model.nomi_docenti) >= model.min_ord - 50 * (
                1 - model.y[com])
        # rimuovere -50....  in caso non vada bene

    model.profMinOrdCst = pyo.Constraint(model.commissioni, rule=prof_min_ord_c)

    # 6b. max_ord deve essere il massimo numero di docenti ordinari per ogni commissione
    def prof_max_ord_c(model, com):
        return sum(model.z[p, com] * model.is_ordinario[p] for p in model.nomi_docenti) <= model.max_ord

    model.profMaxOrdCst = pyo.Constraint(model.commissioni, rule=prof_max_ord_c)

    # 7. min_doc deve essere il minimo numero di docenti per ogni commissione
    def prof_min_all_c(model, com):
        return sum(model.z[p, com] for p in model.nomi_docenti) >= model.min_doc - 50 * (1 - model.y[com])
        # rimuovere -50....  in caso non vada bene

    model.profMinAllCst = pyo.Constraint(model.commissioni, rule=prof_min_all_c)

    # 7b. max_ord deve essere il massimo numero di docenti per ogni commissione
    def prof_max_all_c(model, com):
        return sum(model.z[p, com] for p in model.nomi_docenti) <= model.max_doc

    model.profMaxAllCst = pyo.Constraint(model.commissioni, rule=prof_max_all_c)

    return model
