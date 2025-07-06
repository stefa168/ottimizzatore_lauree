import type {
  AvailabilityAndDate,
  GradSession,
  Professor,
  ProfessorAvailability,
  SessionProfessor,
} from "@/types";

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
  availability: ProfessorAvailability,
  updated_at: string
}

export interface RawSessionProfessor extends Professor {
  availability: RawAvailabilityAndDate,
}

export const transformAvailabilityAndDate = (raw: RawAvailabilityAndDate): AvailabilityAndDate => ({
  when: raw.availability,
  updated_at: new Date(raw.updated_at)
})

export const transformSessionProfessor = (raw: RawSessionProfessor): SessionProfessor => {
  return {...raw, availability: transformAvailabilityAndDate(raw.availability)};
}

export const transformSessionProfessorList = (raw: RawSessionProfessor[]): SessionProfessor[] => raw.map(transformSessionProfessor)
