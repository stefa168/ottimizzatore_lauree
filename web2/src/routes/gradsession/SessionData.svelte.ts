import type {GradSession, GradSessionEntry, PartialExcept, Professor, ProfessorBurden, SessionProfessor} from "@/types";
import {getContext, setContext} from "svelte";
import {computeProfessorsBurdens} from "@/utils";
import {GradSessionApi} from "@/api/GradSesssionApi";
import {fromRawList} from "@/api/RawTypes";

export class SessionData {
  public session: GradSession;
  public student_entries: GradSessionEntry[];
  public studentEntriesMap: Map<number, GradSessionEntry>;
  public sessionProfessors: SessionProfessor[];
  public sessionProfessorsMap: Map<number, SessionProfessor>;
  public professorsBurdens: Map<number, ProfessorBurden>;
  // Splits and substitutes derived from each Session Professor, by parent id
  public childrenOf: Map<number, SessionProfessor[]>;

  constructor(session: GradSession, student_entries: GradSessionEntry[], professors: SessionProfessor[]) {
    this.session = $state(session);
    this.student_entries = $state(student_entries);
    this.studentEntriesMap = $derived(new Map(this.student_entries.map(s => [s.id, s])));
    this.sessionProfessors = $state(professors);
    this.sessionProfessorsMap = $derived(new Map(this.sessionProfessors.map(p => [p.id, p])));
    this.professorsBurdens = $derived(computeProfessorsBurdens(this.sessionProfessorsMap, this.student_entries));
    // Sorted by id, i.e. in creation order, so that splits keep their "Parte N" numbering
    this.childrenOf = $derived(this.sessionProfessors.toSorted((a, b) => a.id - b.id).reduce((map, sp) => {
      if (sp.derived_from_id !== null)
        map.set(sp.derived_from_id, [...(map.get(sp.derived_from_id) ?? []), sp]);
      return map;
    }, new Map<number, SessionProfessor[]>()));
  }

  /** Ids of the Session Professor and of all its splits and substitutes. */
  subtreeIds(id: number): Set<number> {
    const ids = new Set<number>([id]);
    const stack = [id];
    while (stack.length > 0) {
      for (const child of this.childrenOf.get(stack.pop()!) ?? []) {
        if (!ids.has(child.id)) {
          ids.add(child.id);
          stack.push(child.id);
        }
      }
    }
    return ids;
  }

  /** Students supervised by the Session Professor or by one of its splits and substitutes. */
  supervisedEntries(id: number): GradSessionEntry[] {
    const ids = this.subtreeIds(id);
    return this.student_entries.filter(e => ids.has(e.supervisor_id));
  }

  /**
   * Burden of a Session Professor including its splits and substitutes. Counter-supervisions stay assigned to the
   * original professor, so they're counted once.
   */
  subtreeBurden(id: number): ProfessorBurden {
    let total: ProfessorBurden = {asSupervisor: 0, asCounterSupervisor: 0};
    for (const spId of this.subtreeIds(id)) {
      const b = this.professorsBurdens.get(spId);
      if (b) total = {
        asSupervisor: total.asSupervisor + b.asSupervisor,
        asCounterSupervisor: total.asCounterSupervisor + b.asCounterSupervisor
      };
    }
    return total;
  }

  /** Reloads professors and students, e.g. after a split or a substitution changed several of them at once. */
  async refresh() {
    const api = GradSessionApi();
    const [professors, entries] = await Promise.all([
      api.getSessionProfessors(this.session.id).then(fromRawList<SessionProfessor>),
      api.getStudents(this.session.id).then(fromRawList<GradSessionEntry>),
    ]);
    this.sessionProfessors = professors;
    this.student_entries = entries;
  }

  // This method is required to trigger reactivity on the
  updateSessionProfessor(patch: PartialExcept<SessionProfessor, 'id'>) {
    const i = this.sessionProfessors.findIndex((p) => p.id === patch.id);
    if (i < 0) return;
    const next = { ...this.sessionProfessors[i]!, ...patch };
    this.sessionProfessors = this.sessionProfessors.with(i, next);
  }
}

const SESSION_DATA_KEY = Symbol("SESSION_DATA");

export function setSessionData(session: GradSession, student_entries: GradSessionEntry[], professors: SessionProfessor[]) {
  return setContext(SESSION_DATA_KEY, new SessionData(session, student_entries, professors));
}

export function getSessionData() {
  return getContext<ReturnType<typeof setSessionData>>(SESSION_DATA_KEY);
}