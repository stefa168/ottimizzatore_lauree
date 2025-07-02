export interface ApiErrorResponse<TExtra = never> {
    detail: string,
    extra?: TExtra,
    status_code: number
}

interface GradSession {
    id: number,
    title: string,
    created_at: Date,
    updated_at: Date
}

type DegreeLevel = 'bachelors' | 'masters';

interface GradSessionEntry {
    id: number,
    candidate: Student,
    degree_level: DegreeLevel,
    supervisor_id: number,
    supervisor2_id: number | null,
    supervisor_assistant_id: number | null,
    counter_supervisor_id: number | null
}

interface NameSurname {
    first_name: string,
    surname: string
}

interface Student extends NameSurname {
    id: number,
    matriculation_number: number,
    university_email: string,
}

type UniversityRole = 'ordinary' | 'associate' | 'researcher' | 'unspecified';
type ProfessorAvailability = 'always' | 'morning' | 'afternoon' | 'split'

interface AvailabilityAndDate {
    when: ProfessorAvailability,
    updated_at: Date
}

interface SessionProfessor extends NameSurname{
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