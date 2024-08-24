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
type ProfessorAvailability = 'always' | 'morning' | 'afternoon'

interface Professor {
    id: number,
    name: string,
    surname: string,
    role: UniversityRole,
    availability: ProfessorAvailability
}

interface ProfessorBurden {
    asSupervisor: number,
    asCounterSupervisor: number
}

export function getProfessorBurden(p: Professor): ProfessorBurden {
    let entries = get(selectedProblem)?.entries ?? [];
    let asSupervisor = 0, asCounterSupervisor = 0;

    for (let e of entries) {
        if (e.supervisor.id === p.id) {
            asSupervisor += 1;
        }
        if (e.counter_supervisor?.id === p.id) {
            asCounterSupervisor += 1;
        }
    }
    console.log(p, asSupervisor, asCounterSupervisor);

    return {asSupervisor, asCounterSupervisor}
}

export type {
    Commission,
    CommissionEntry,
    DegreeLevel,
    Professor,
    ProfessorBurden,
    Student,
    UniversityRole,
    ProfessorAvailability
};
