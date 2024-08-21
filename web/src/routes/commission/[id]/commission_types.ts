import type {OptimizationConfiguration} from "./optimization/optimization_types";
import {selectedProblem} from "$lib/store";
import {get} from "svelte/store";

interface Commission {
    id: number,
    title: string
    entries: CommissionEntry[]
    optimization_configurations: OptimizationConfiguration[]
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

interface ProfessorBurden {
    asSupervisor: number,
    asCounterSupervisor: number
}

export function getProfessorBurden(p: Professor): ProfessorBurden {
    let entries = get(selectedProblem)?.entries ?? [];
    let asSupervisor = 0, asCounterSupervisor = 0;

    for (const e of entries) {
        if (e.supervisor == p) {
            asSupervisor += 1;
        }
        if (e.counter_supervisor == p) {
            asCounterSupervisor += 1;
        }
    }

    return {asSupervisor, asCounterSupervisor}
}

export type {Commission, CommissionEntry, DegreeLevel, Professor, ProfessorBurden, Student, UniversityRole};
