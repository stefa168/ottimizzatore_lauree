import {clsx, type ClassValue} from "clsx";
import {twMerge} from "tailwind-merge";
import type {GradSessionEntry, ProfessorBurden, SessionProfessor, TextTemplates} from "@/types";

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

export const formatText = (templates: TextTemplates, count: number): string => {
  return count === 1 ? templates.singular(count) : templates.plural(count);
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