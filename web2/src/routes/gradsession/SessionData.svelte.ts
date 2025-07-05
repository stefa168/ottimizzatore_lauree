import type {GradSession, GradSessionEntry, ProfessorBurden, SessionProfessor} from "@/types";
import {getContext, setContext} from "svelte";
import {computeProfessorsBurdens} from "@/utils";

export class SessionData {
  public session: GradSession;
  public student_entries: GradSessionEntry[];
  public professors: SessionProfessor[];
  public professorsMap: Map<number, SessionProfessor>;
  public professorsBurdens: Map<number, ProfessorBurden>;

  constructor(session: GradSession, student_entries: GradSessionEntry[], professors: SessionProfessor[]) {
    this.session = $state(session);
    this.student_entries = $state(student_entries);
    this.professors = $state(professors);
    this.professorsMap = $derived(new Map(this.professors.map(p => [p.id, p])));
    this.professorsBurdens = $derived(computeProfessorsBurdens(this.professorsMap, this.student_entries));
  }
}

const SESSION_DATA_KEY = Symbol("SESSION_DATA");

export function setSessionData(session: GradSession, student_entries: GradSessionEntry[], professors: SessionProfessor[]) {
  return setContext(SESSION_DATA_KEY, new SessionData(session, student_entries, professors));
}

export function getSessionData() {
  return getContext<ReturnType<typeof setSessionData>>(SESSION_DATA_KEY);
}