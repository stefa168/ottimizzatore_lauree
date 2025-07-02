import {clsx, type ClassValue} from "clsx";
import {twMerge} from "tailwind-merge";
import type {GradSessionEntry, TextTemplates} from "@/types";

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