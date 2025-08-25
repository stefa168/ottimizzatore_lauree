import type {GradSession, GradSessionEntry, PartialExcept, Professor, ProfessorBurden, SessionProfessor} from "@/types";
import {getContext, setContext} from "svelte";
import {computeProfessorsBurdens} from "@/utils";

export class SessionData {
  public session: GradSession;
  public student_entries: GradSessionEntry[];
  public studentEntriesMap: Map<number, GradSessionEntry>;
  public sessionProfessors: SessionProfessor[];
  public sessionProfessorsMap: Map<number, SessionProfessor>;
  public professorsBurdens: Map<number, ProfessorBurden>;

  constructor(session: GradSession, student_entries: GradSessionEntry[], professors: SessionProfessor[]) {
    this.session = $state(session);
    this.student_entries = $state(student_entries);
    this.studentEntriesMap = $derived(new Map(this.student_entries.map(s => [s.id, s])));
    this.sessionProfessors = $state(professors);
    this.sessionProfessorsMap = $derived(new Map(this.sessionProfessors.map(p => [p.id, p])));
    this.professorsBurdens = $derived(computeProfessorsBurdens(this.sessionProfessorsMap, this.student_entries));
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