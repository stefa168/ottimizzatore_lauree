import type {SolutionCommission} from "@/api/OptimizationConfigurationApi";

export interface ApiErrorResponse<TExtra = never> {
  detail: string,
  extra?: TExtra,
  status_code: number
}

export type PartialExcept<T, K extends keyof T> = Partial<T> & Pick<T, K>;

export interface CreationUpdateDate {
  created_at: Date,
  updated_at: Date
}

// Graduation Session
export interface GradSession extends CreationUpdateDate {
  id: number,
  title: string
}

// Graduation Session Entry
export type DegreeLevel = 'bachelors' | 'masters';

export interface GradSessionEntry extends CreationUpdateDate {
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

// Student
export interface Student extends NameSurname, CreationUpdateDate {
  id: number,
  matriculation_number: number,
  university_email: string,
}

// Professor
export type UniversityRole = 'ordinary' | 'associate' | 'researcher' | 'unspecified';
export type ProfessorAvailability = 'always' | 'morning' | 'afternoon'
export type SessionProfessorRelation = 'original' | 'split' | 'substitute'

export interface Professor extends NameSurname, CreationUpdateDate {
  id: number,
  role: UniversityRole
}

export interface SessionProfessor extends CreationUpdateDate {
  id: number,
  session_id: number,
  professor: Professor
  availability: ProfessorAvailability,
  user_note: string | null,
  derived_from_id: number | null,
  relation: SessionProfessorRelation
}

export interface ProfessorBurden {
  asSupervisor: number,
  asCounterSupervisor: number
}

export type OptimizationTaskState = 'running' | 'ended' | 'not_started' | 'failure';

export interface OptimizationStatus {
  status: OptimizationTaskState;
  running: boolean;
  ended: boolean;
  started: boolean;
  failed: boolean;
  success: boolean;
  commissions: { all: SolutionCommission[], morning: SolutionCommission[], afternoon: SolutionCommission [] };
}

export type TextTemplate = (count: number, total: number) => string;

export type TextTemplates = {
  singular: TextTemplate,
  plural: TextTemplate
};

export type ValueLabelStructure = { value: string, label: string, disabled?: boolean };