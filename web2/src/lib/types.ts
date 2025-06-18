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
    supervisor: Professor,
    supervisor_assistant: Professor | null,
    counter_supervisor: Professor | null
}

interface Student {
    id: number,
    matriculation_number: number,
    name: string,
    surname: string,
    phone_number: string,
    personal_email: string,
    university_email: string,
}

type UniversityRole = 'ordinary' | 'associate' | 'researcher' | 'unspecified';
type ProfessorAvailability = 'always' | 'morning' | 'afternoon' | 'split'

interface Professor {
    id: number,
    name: string,
    surname: string,
    role: UniversityRole
}

export type {
    GradSession,
    GradSessionEntry,
    Student,
    DegreeLevel,
    Professor,
    UniversityRole
}