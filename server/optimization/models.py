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

    # 4. Create the model instance (to load .dat with path to Excel)
    model = model.create_instance(str(dat_path))

    # 5. Read the data from the excel file
    df = pandas.read_excel(pyo.value(model.excel_path), dtype={"ID_Studente": int})
    # drop students without a supervisor SP
    df = df.dropna(subset=["ID_Relatore"])

    # 6. Set candidates
    # We'll use the "ID_Studente" column as the candidate ID
    model.tesisti = df.set_index("ID_Studente")
    model.Candidati = pyo.Set(initialize=set(model.tesisti.index))
    model.n_tesisti = len(model.tesisti)

    # 7. Build the docenti (SessionProfessor rows) from supervisor and counter-supervisor columns
    # Normalize supervisors
    rel_cols = [
        ("ID_Relatore", "PID_Relatore", "Relatore", "Relatore_Mattina", "Relatore_Pomeriggio", "Ruolo_Relatore"),
    ]
    rel_df_parts = []
    for id_col, pid_col, name_col, m_col, p_col, role_col in rel_cols:
        part = model.tesisti[[id_col, pid_col, name_col, m_col, p_col, role_col]].copy()
        part.columns = ["SP_ID", "PID", "Nome", "MATTINA", "POMERIGGIO", "tipo"]
        rel_df_parts.append(part)

    # Normalize counter-supervisors if present
    ctr_cols_present = {"ID_Controrelatore", "PID_Controrelatore", "Controrelatore",
                        "Controrelatore_Mattina", "Controrelatore_Pomeriggio", "Ruolo_Controrelatore"} <= set(
        model.tesisti.columns
    )
    ctr_df_parts = []
    if ctr_cols_present:
        ctr = model.tesisti[
            ["ID_Controrelatore", "PID_Controrelatore", "Controrelatore",
             "Controrelatore_Mattina", "Controrelatore_Pomeriggio", "Ruolo_Controrelatore"]
        ].dropna(subset=["ID_Controrelatore"]).copy()
        if not ctr.empty:
            ctr.columns = ["SP_ID", "PID", "Nome", "MATTINA", "POMERIGGIO", "tipo"]
            ctr_df_parts.append(ctr)

    docenti_df = pandas.concat(rel_df_parts + ctr_df_parts, ignore_index=True)
    # Remove duplicates by SessionProfessor ID
    docenti_df = docenti_df.drop_duplicates(subset=["SP_ID"]).reset_index(drop=True)
    # Persist on model for solution extraction later
    model.docenti = docenti_df

    # 8. Sets for SPs and Persons (human professors)
    SPs = list(map(int, docenti_df["SP_ID"].tolist()))
    PIDs = list(map(int, docenti_df["PID"].drop_duplicates().tolist()))
    model.SPs = pyo.Set(initialize=SPs)
    model.Persone = pyo.Set(initialize=PIDs)

    # Python-side helpers
    sp_to_person = {int(r.SP_ID): int(r.PID) for _, r in docenti_df.iterrows()}
    model.sp_by_person = {}
    for pid in PIDs:
        model.sp_by_person[pid] = [int(r.SP_ID) for _, r in docenti_df[docenti_df["PID"] == pid].iterrows()]

    # 9. Parameters
    # Durata per candidato
    model.durata = pyo.Param(model.Candidati, initialize=lambda m, t: int(m.tesisti.loc[t, "Durata"]), within=pyo.NonNegativeIntegers)

    # Supervisor SP and Counter-supervisor SP for each candidate (NaN -> None)
    def _safe_int(x):
        try:
            return int(x)
        except Exception:
            return None

    model.supervisor_sp_of = {t: _safe_int(model.tesisti.loc[t, "ID_Relatore"]) for t in model.tesisti.index}
    model.counter_sp_of = {
        t: _safe_int(model.tesisti.loc[t, "ID_Controrelatore"]) if "ID_Controrelatore" in model.tesisti.columns else None
        for t in model.tesisti.index
    }

    # Ordinariness at person level (same for all SPs of a person)
    ordinari_by_pid = {}
    for pid in PIDs:
        # If any SP row says PO, consider person as ordinario
        roles = set(docenti_df[docenti_df["PID"] == pid]["tipo"].astype(str))
        ordinari_by_pid[pid] = any(role == "PO" for role in roles)
    model.is_ordinario_person = pyo.Param(model.Persone, initialize=lambda m, pid: 1 if ordinari_by_pid[pid] else 0)

    # Availability per SP and commission
    def disponibilita_init(m, sp, com):
        row = docenti_df.loc[docenti_df["SP_ID"] == sp].iloc[0]
        if com in m.commissioni_mattina:
            return 1 if str(row["MATTINA"]).upper() == "SI" else 0
        else:
            return 1 if str(row["POMERIGGIO"]).upper() == "SI" else 0

    model.disponibilita_sp = pyo.Param(model.SPs, model.commissioni, initialize=disponibilita_init, within=pyo.Binary)

    # 10. Variables
    model.min_ord = pyo.Var(within=pyo.NonNegativeIntegers)
    model.max_ord = pyo.Var(within=pyo.NonNegativeIntegers)
    model.x = pyo.Var(model.Candidati, model.commissioni, within=pyo.Binary)
    model.y = pyo.Var(model.commissioni, within=pyo.Binary)     # commission used
    model.y2 = pyo.Var(model.commissioni, within=pyo.Binary)    # commission is magistrale

    # z at SP level; zp at PERSON level
    model.z = pyo.Var(model.SPs, model.commissioni, within=pyo.Binary)
    model.zp = pyo.Var(model.Persone, model.commissioni, within=pyo.Binary)

    model.w = pyo.Var(within=pyo.Reals)
    model.w2 = pyo.Var(within=pyo.Reals)

    # 11. Objective
    model.alpha = 10000
    model.beta = 1000
    model.gamma = 10

    def obj_expression(m):
        return + m.alpha * m.w2 - m.beta * m.w + m.gamma * (m.max_ord - m.min_ord) \
            + sum(m.y[k] for k in m.commissioni_pomeriggio)

    model.OBJ = pyo.Objective(rule=obj_expression, sense=pyo.minimize)

    # 12. Constraints

    # 1. all candidates assigned exactly one commission
    def all_candidates_c(m, cand):
        return sum(m.x[cand, com] for com in m.commissioni) == 1

    # 2. commission duration <= max
    def comm_duration_c(m, com):
        return sum(m.x[cand, com] * m.durata[cand] for cand in m.Candidati) <= m.max_durata * m.y[com]

    # 3. maximize minimum commission duration (w = min)
    def max_min_c(m, com):
        return sum(m.durata[cand] * m.x[cand, com] for cand in m.Candidati) >= m.w - m.max_durata * (1 - m.y[com])

    # 4. minimize maximum commission duration (w2 = max)
    def max_min_c2(m, com):
        return sum(m.durata[cand] * m.x[cand, com] for cand in m.Candidati) <= m.w2 + m.max_durata * (1 - m.y[com])

    # 5. Supervisor must be present (use the SP availability but count the PERSON)
    # Availability/use must reference z (SP-level), not only zp (person-level).
    def prof_avail_c(m, t, com):
        sp = m.supervisor_sp_of[t]
        if sp is None:
            return pyo.Constraint.Feasible
        return m.x[t, com] <= m.disponibilita_sp[sp, com] * m.z[sp, com]

    def prof2_avail_c(m, t, com):
        sp = m.counter_sp_of[t]
        if sp is None:
            return pyo.Constraint.Feasible
        return m.x[t, com] <= m.disponibilita_sp[sp, com] * m.z[sp, com]

    # Link both ways: z -> zp and zp -> z
    def link_sp_person_upper(m, sp, com):
        pid = sp_to_person[sp]
        return m.z[sp, com] <= m.zp[pid, com]

    def link_person_lower(m, pid, com):
        return m.zp[pid, com] <= sum(m.z[sp, com] for sp in model.sp_by_person[pid])

    # Optional but recommended: don’t allow picking an unavailable SP
    def sp_availability_cap(m, sp, com):
        return m.z[sp, com] <= m.disponibilita_sp[sp, com]

    # Only one SP of the same person in a commission
    def one_sp_per_person_per_comm(m, pid, com):
        return sum(m.z[sp, com] for sp in model.sp_by_person[pid]) <= 1


    # 7. Every person at most in one commission overall
    def person_comm_c(m, pid):
        return sum(m.zp[pid, com] for com in m.commissioni) <= 1

    # 8. min_ord is minimum number of ordinari per commission
    def prof_min_ord_c(m, com):
        return sum(m.zp[pid, com] * m.is_ordinario_person[pid] for pid in m.Persone) >= m.min_ord - m.max_docenti * (1 - m.y[com])

    # 9. max_ord is maximum number of ordinari per commission
    def prof_max_ord_c(m, com):
        return sum(m.zp[pid, com] * m.is_ordinario_person[pid] for pid in m.Persone) <= m.max_ord

    # 10. Minimum number of professors per commission
    def prof_min_all_c(m, com):
        return sum(m.zp[pid, com] for pid in m.Persone) >= m.min_docenti * m.y[com]

    # 11. Maximum number of professors per commission
    def prof_max_all_c(m, com):
        return sum(m.zp[pid, com] for pid in m.Persone) <= m.max_docenti

    # 12. If a magistrale student is assigned, commission must be magistrale
    def comm_mag1(m, t, com):
        # duration > 15 is magistrale in this model
        return m.x[t, com] * int(m.durata[t] > 15) <= m.y2[com]

    # 13. Minimum number of professors for magistrale commission
    def comm_mag2(m, com):
        return sum(m.zp[pid, com] for pid in m.Persone) >= m.min_docenti_magistrale * m.y2[com]

    # 14. Magistrale implies commission is used
    def comm_mag3(m, com):
        return m.y2[com] <= m.y[com]

    # 15. Commission cannot be magistrale if no magistrale student is present
    def comm_mag4(m, com):
        return sum(m.x[t, com] * int(m.durata[t] > 15) for t in m.Candidati) >= m.y2[com]

    model.allCandCst = pyo.Constraint(model.Candidati, rule=all_candidates_c)
    model.commDurCst = pyo.Constraint(model.commissioni, rule=comm_duration_c)
    model.maxMinCst = pyo.Constraint(model.commissioni, rule=max_min_c)
    model.maxMinCst2 = pyo.Constraint(model.commissioni, rule=max_min_c2)
    model.profAvailCst = pyo.Constraint(model.Candidati, model.commissioni, rule=prof_avail_c)
    model.prof2AvailCst = pyo.Constraint(model.Candidati, model.commissioni, rule=prof2_avail_c)

    model.linkSpPersonUpper = pyo.Constraint(model.SPs, model.commissioni, rule=link_sp_person_upper)
    model.linkPersonLower = pyo.Constraint(model.Persone, model.commissioni, rule=link_person_lower)

    model.oneSpPerPersonPerComm = pyo.Constraint(model.Persone, model.commissioni, rule=one_sp_per_person_per_comm)
    model.personCommCst = pyo.Constraint(model.Persone, rule=person_comm_c)

    model.profMinOrdCst = pyo.Constraint(model.commissioni, rule=prof_min_ord_c)
    model.profMaxOrdCst = pyo.Constraint(model.commissioni, rule=prof_max_ord_c)
    model.profMinAllCst = pyo.Constraint(model.commissioni, rule=prof_min_all_c)
    model.profMaxAllCst = pyo.Constraint(model.commissioni, rule=prof_max_all_c)

    model.comm_mag1 = pyo.Constraint(model.Candidati, model.commissioni, rule=comm_mag1)
    model.comm_mag2 = pyo.Constraint(model.commissioni, rule=comm_mag2)
    model.comm_mag3 = pyo.Constraint(model.commissioni, rule=comm_mag3)
    model.comm_mag4 = pyo.Constraint(model.commissioni, rule=comm_mag4)

    return model


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