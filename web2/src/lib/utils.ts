import {clsx, type ClassValue} from "clsx";
import {twMerge} from "tailwind-merge";
import type {
  GradSessionEntry,
  OptimizationStatus,
  OptimizationTaskState,
  ProfessorBurden,
  SessionProfessor,
  TextTemplates
} from "@/types";
import type {OptimizationConfiguration} from "@/api/OptimizationConfigurationApi";
import {DateTime, Duration} from 'luxon'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, "children"> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };

/**
 * @deprecated Please use only for experimentation, this delay is not cancellable in its current form.
 */
export const delay = (ms: number) => {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export const capitalize = (s: string) =>
  s.toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

export const getDegreeLevelString = (s: GradSessionEntry) => {
  switch (s.degree_level) {
    case "bachelors":
      return "Triennale";
    case "masters":
      return "Magistrale";
    default:
      return s.degree_level;
  }
}

export const formatText = (templates: TextTemplates, count: number, total?: number): string => {
  return count === 1 ? templates.singular(count, total ?? 0) : templates.plural(count, total ?? 0);
}

export const dateFormatter = new Intl.DateTimeFormat('it-IT', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit'
});

export const computeProfessorsBurdens = (
  professorMap: Map<number, SessionProfessor>,
  sessionEntries: GradSessionEntry[]
): Map<number, ProfessorBurden> => {
  let burdens = new Map<number, ProfessorBurden>();

  // Initialize all professors with zero burden
  for (let [professorId] of professorMap) {
    burdens.set(professorId, {asSupervisor: 0, asCounterSupervisor: 0});
  }

  // Loop through session entries and count burdens
  for (let entry of sessionEntries) {
    // Count supervisor
    if (entry.supervisor_id && burdens.has(entry.supervisor_id)) {
      const current = burdens.get(entry.supervisor_id)!;
      current.asSupervisor += 1;
    }

    // Count counter supervisor
    if (entry.counter_supervisor_id && burdens.has(entry.counter_supervisor_id)) {
      const current = burdens.get(entry.counter_supervisor_id)!;
      current.asCounterSupervisor += 1;
    }
  }

  return burdens;
};

// https://blog.logrocket.com/iterate-over-enums-typescript/
export function enumKeys<O extends object, K extends keyof O = keyof O>(obj: O): K[] {
  return Object.keys(obj).filter(k => !Number.isNaN(k)) as K[]
}

export const optimizationTaskStatusFactory = (configuration: OptimizationConfiguration): OptimizationStatus => {
  let status: OptimizationTaskState = "not_started";
  if (configuration.run_lock) {
    const optimizationLog = configuration.optimization_log;
    if (optimizationLog?.error_message && optimizationLog.error_message.length > 0)
      status = "failure"
    else
      status = optimizationLog ? 'ended' : 'running';
  }

  const solutions = configuration.commissions ?? [];

  return {
    status,
    get ended() {
      return this.status === 'ended'
    },
    get running() {
      return this.status === 'running'
    },
    get started() {
      return this.status !== 'not_started'
    },
    get failed() {
      return this.status === 'failure'
    },
    commissions: {
      all: solutions,
      morning: solutions.filter(s => s.morning),
      afternoon: solutions.filter(s => !s.morning),
    }
  }
}

export const computeTimeDifference = (startDate?: Date, endDate?: Date): string => {
  if (!startDate || !endDate) return '?? minuti e ?? secondi';
  const start = DateTime.fromJSDate(startDate)
  const end = DateTime.fromJSDate(endDate)

  return end.setLocale('it').diff(start).toHuman({})
}

export const formatTime = (minutes: number): string => {
  return Duration.fromObject({minutes}, {locale: 'it'}).toHuman();
}