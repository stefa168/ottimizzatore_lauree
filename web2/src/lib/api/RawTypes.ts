import type {
  CreationUpdateDate,
  GradSession, GradSessionEntry, Professor,
  SessionProfessor, Student,
} from "@/types";

export type UpdateSessonProfessor = Pick<SessionProfessor, 'availability' | 'user_note'>
// Generic date helpers
export type OmitDateFields<T> = Omit<T, keyof CreationUpdateDate>;
export type RawDateFields = { created_at: string; updated_at: string };
export type WithRawDates<T extends CreationUpdateDate> = OmitDateFields<T> & RawDateFields;

// Generic transformers
export const fromRawDates = <T extends CreationUpdateDate>(raw: WithRawDates<T>): T => {
  const {created_at, updated_at, ...rest} = raw as RawDateFields & Record<string, unknown>;
  return {
    ...(rest as Omit<T, keyof CreationUpdateDate>),
    created_at: new Date(created_at),
    updated_at: new Date(updated_at),
  } as T;
};

export const fromRawList = <T extends CreationUpdateDate>(rawArr: WithRawDates<T>[]): T[] =>
  rawArr.map(fromRawDates);


export type RawGradSession = WithRawDates<GradSession>;
export type RawGradSessionEntry = WithRawDates<GradSessionEntry>;
export type RawSessionProfessor = WithRawDates<SessionProfessor>;
export type RawStudent = WithRawDates<Student>;
export type RawProfessor = WithRawDates<Professor>;
