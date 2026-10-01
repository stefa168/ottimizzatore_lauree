import type {GradSession, GradSessionEntry, ProfessorBurden, SessionProfessor} from "@/types";
import {getContext, setContext} from "svelte";
import {computeProfessorsBurdens} from "@/utils";

/** Where the session data comes from: the remote queries awaited by the session layout. */
export interface SessionDataSource {
  readonly session: GradSession;
  readonly students: GradSessionEntry[];
  readonly professors: SessionProfessor[];
}

/**
 * Data of a graduation session shared by its tabs. It reads the remote queries through `source`, so it's always in
 * sync with them: commands refresh the queries they change, and everything derived here follows.
 */
export class SessionData {
  public studentEntriesMap: Map<number, GradSessionEntry>;
  public sessionProfessorsMap: Map<number, SessionProfessor>;
  public professorsBurdens: Map<number, ProfessorBurden>;
  // Splits and substitutes derived from each Session Professor, by parent id
  public childrenOf: Map<number, SessionProfessor[]>;

  readonly #source: SessionDataSource;

  get session() {
    return this.#source.session;
  }

  get student_entries() {
    return this.#source.students;
  }

  get sessionProfessors() {
    return this.#source.professors;
  }

  constructor(source: SessionDataSource) {
    this.#source = source;
    this.studentEntriesMap = $derived(new Map(this.student_entries.map(s => [s.id, s])));
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
}

const SESSION_DATA_KEY = Symbol("SESSION_DATA");

export function setSessionData(source: SessionDataSource) {
  return setContext(SESSION_DATA_KEY, new SessionData(source));
}

export function getSessionData() {
  return getContext<ReturnType<typeof setSessionData>>(SESSION_DATA_KEY);
}