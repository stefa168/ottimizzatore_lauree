export interface ApiErrorResponse<TExtra = never> {
    detail: string,
    extra?: TExtra,
    status_code: number
}

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

export interface SessionProfessor extends NameSurname{
    id: number,
    role: UniversityRole,
    availability: AvailabilityAndDate,
}

export type {
    NameSurname,
    GradSession,
    GradSessionEntry,
    Student,
    DegreeLevel,
    SessionProfessor,
    UniversityRole,
    ProfessorAvailability,
    AvailabilityAndDate
}