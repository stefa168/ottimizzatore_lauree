import {z} from "zod";
import {SolverType} from "../optimization_types";

export const optimizationConfigurationSchema = z.object({
    title: z.string().min(1).max(256),
    max_duration: z.coerce.number().min(0).default(210),
    max_commissions_morning: z.coerce.number().min(0).default(6),
    max_commissions_afternoon: z.coerce.number().min(0).default(6),
    online: z.boolean().default(false),

    min_professor_number: z.coerce.number().min(1).nullable().default(null),
    min_professor_number_masters: z.coerce.number().min(1).nullable().default(null),
    max_professor_number: z.coerce.number().min(1).nullable().default(null),

    solver: z.nativeEnum(SolverType).default(SolverType.CPLEX),
    optimization_time_limit: z.coerce.number().min(60).default(60),
    optimization_gap: z.coerce.number().min(0).default(0.005),
}).refine((data) => {
    // If online, then the minimum number of professors must be defined
    return data.online ? data.min_professor_number !== null : true;
}, {
    message: "Il numero minimo di professori deve essere definito se la commissione è online",
    path: ["min_professor_number"]
}).refine((data) => {
    // If online, then the minimum number of professors for the master's degree must be defined
    return data.online ? data.min_professor_number_masters !== null : true;
}, {
    message: "Il numero minimo di professori per il corso di laurea magistrale deve essere definito se la commissione è online",
    path: ["min_professor_number_masters"]
}).refine((data) => {
    // If online, then the maximum number of professors must be defined
    return data.online ? data.max_professor_number !== null : true;
}, {
    message: "Il numero massimo di professori deve essere definito se la commissione è online",
    path: ["max_professor_number"]
}).refine((data) => {
    // If online, then the minimum number of professors must be less than or equal to the maximum number of professors
    if (data.online && data.min_professor_number !== null && data.max_professor_number !== null) {
        return data.min_professor_number <= data.max_professor_number;
    } else {
        return true;
    }
}, {
    message: "Il numero minimo di professori deve essere minore o uguale al numero massimo di professori se la commissione è online",
    path: ["min_professor_number", "max_professor_number"]
}).refine((data) => {
    // If online, then the minimum number of professors must be less than or equal to the maximum number of professors
    if (data.online && data.min_professor_number !== null && data.max_professor_number !== null) {
        return data.min_professor_number <= data.max_professor_number;
    } else {
        return true;
    }
}, {
    message: "Il numero minimo di professori deve essere minore o uguale al numero massimo di professori se la commissione è online",
    path: ["min_professor_number_masters", "max_professor_number"]
}).refine((data) => {
    // If online, then the minimum number of professors for the master's degree must be less than or equal to the maximum number of professors
    if (data.online && data.min_professor_number_masters !== null && data.max_professor_number !== null) {
        return data.min_professor_number_masters <= data.max_professor_number;
    } else {
        return true;
    }
});