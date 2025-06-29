import type {AvailabilityAndDate, GradSession, ProfessorAvailability, SessionProfessor, UniversityRole} from "@/types";

export interface RawGradSession {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export const transformGradSession = (raw: RawGradSession): GradSession => ({
  ...raw,
  created_at: new Date(raw.created_at),
  updated_at: new Date(raw.updated_at)
});

export interface RawAvailabilityAndDate {
  when: ProfessorAvailability,
  updated_at: string
}

export interface RawSessionProfessor {
  id: number,
  name: string,
  surname: string,
  role: UniversityRole,
  availability: RawAvailabilityAndDate,
}

export const transformSessionProfessor = (raw: RawSessionProfessor): SessionProfessor => {
  const av: AvailabilityAndDate = {when: raw.availability.when, updated_at: new Date(raw.availability.updated_at)};
  return {...raw, availability: av};
}

export const transformSessionProfessorList = (raw: RawSessionProfessor[]): SessionProfessor[] => raw.map(transformSessionProfessor)
