export interface ApiErrorResponse<TExtra = never> {
  detail: string,
  extra?: TExtra,
  status_code: number
}

export type PartialExcept<T, K extends keyof T> = Partial<T> & Pick<T, K>;

export interface GradSession {
  id: number,
  title: string,
  created_at: Date,
  updated_at: Date
}

export type DegreeLevel = 'bachelors' | 'masters';

export interface GradSessionEntry {
  id: number,
  candidate: Student,
  degree_level: DegreeLevel,
  supervisor_id: number,
  supervisor2_id: number | null,
  supervisor_assistant_id: number | null,
  counter_supervisor_id: number | null
}

export interface NameSurname {
  first_name: string,
  surname: string
}

export interface Student extends NameSurname {
  id: number,
  matriculation_number: number,
  university_email: string,
}

export type UniversityRole = 'ordinary' | 'associate' | 'researcher' | 'unspecified';
export type ProfessorAvailability = 'always' | 'morning' | 'afternoon' | 'split'

export interface AvailabilityAndDate {
  when: ProfessorAvailability,
  updated_at: Date
}

export interface Professor extends NameSurname {
  id: number,
  role: UniversityRole
}

export interface SessionProfessor extends Professor {
  availability: AvailabilityAndDate,
}

export type TextTemplate = (count: number, total: number) => string;

export type TextTemplates = {
  singular: TextTemplate,
  plural: TextTemplate
};

export interface ProfessorBurden {
  asSupervisor: number,
  asCounterSupervisor: number
}

export type ValueLabelStructure = { value: string, label: string, disabled?: boolean };