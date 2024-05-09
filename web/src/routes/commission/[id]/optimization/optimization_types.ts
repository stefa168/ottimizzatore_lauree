import type {Professor, Student} from "../commission_types";

export enum SolverType{
    CPLEX = "cplex",
    GUROBI = "gurobi",
    GLPK = "glpk"
}

export interface OptimizationConfiguration {
    id: number,
    title: string
    commission_id: number,
    max_duration: number,
    max_commissions_morning: number,
    max_commissions_afternoon: number,
    online: boolean,
    run_lock: boolean,

    min_professor_number: number | null,
    min_professor_number_masters: number | null,
    max_professor_number: number | null,

    solver: SolverType,
    optimization_time_limit: number,
    optimization_gap: number,

    solution_commissions: SolutionCommission[]
    execution_details: ExecutionDetails[]
}

export interface ExecutionDetails {
    id: number,
    commission_id: number,
    opt_config_id: number,
    start_time: string,
    end_time: string,
    success: boolean,
    solver_reached_optimality: boolean,
    solver_reached_time_limit: boolean,
    error_message: string | null,
    optimizer_log: string | null,
}

export interface SolutionCommission {
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