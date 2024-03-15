import type {Professor, Student} from "../commission_types";

type SolverType = 'cplex' | 'gurobi' | 'glpk';

interface OptimizationConfiguration {
    id: number,
    commission_id: number,
    max_duration: number,
    max_commissions_morning: number,
    max_commissions_afternoon: number,
    online: boolean,

    min_professor_number: number | null,
    min_professor_number_masters: number | null,
    max_professor_numer: number | null,

    solver: SolverType,
    optimization_time_limit: number,
    optimization_gap: number
}

interface SolutionCommission {
    id: number,
    order: number,
    morning: boolean,
    commission_id: number,
    opt_config_id: number,
    duration: number,
    version_hash: string,
    professors: Professor[],
    students: Student[]
}

export type {SolverType, OptimizationConfiguration, SolutionCommission};