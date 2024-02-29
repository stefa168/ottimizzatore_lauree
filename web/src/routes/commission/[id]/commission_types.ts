interface Commission {
    id: number,
    title: string
    entries: CommissionEntry[]
}

type DegreeLevel = 'bachelors' | 'masters';

interface CommissionEntry {
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

interface Professor {
    id: number,
    name: string,
    surname: string,
    role: UniversityRole
}

export type {Commission, CommissionEntry, DegreeLevel, Professor, Student, UniversityRole};