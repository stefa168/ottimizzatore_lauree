import {PUBLIC_BACKEND_URL} from "@/const";
import type {ApiErrorResponse, CreationUpdateDate} from "@/types";
import {z} from "zod";

export enum SolverType {
  CPLEX = "CPLEX",
  GUROBI = "GUROBI",
  GLPK = "GLPK"
}

export const CreationUpdateDateSchema = z.object({
  created_at: z.coerce.date(),
  updated_at: z.coerce.date(),
});

export const OptimizationConfigurationRecapSchema = CreationUpdateDateSchema.extend({
  id: z.number(),
  session_id: z.number(),
  title: z.string().min(1).max(256),
}).passthrough();

export const OptimizationLogSchema = CreationUpdateDateSchema.extend({
  opt_config_id: z.number(),

  start_time: z.coerce.date(),
  end_time: z.coerce.date(),

  success: z.boolean(),
  solver_reached_optimality: z.boolean(),
  solver_time_limit_reached: z.boolean(),
  error_message: z.string().nullable(),
  log: z.string(),
}).passthrough();


export const OptimizationConfigurationSchema = OptimizationConfigurationRecapSchema.extend({
  max_duration: z.coerce.number().min(0).default(210),
  max_commissions_morning: z.coerce.number().min(0).default(6),
  max_commissions_afternoon: z.coerce.number().min(0).default(6),
  online: z.boolean().default(true),
  run_lock: z.boolean(),

  min_professor_number: z.coerce.number().min(1).nullable().default(null),
  min_professor_number_masters: z.coerce.number().min(1).nullable().default(null),
  max_professor_number: z.coerce.number().min(1).nullable().default(null),

  solver: z.nativeEnum(SolverType).default(SolverType.CPLEX),
  optimization_time_limit: z.coerce.number().min(60).default(60),
  optimization_gap: z.coerce.number().min(0).default(0.005),

  optimization_log: OptimizationLogSchema.nullable(),
}).passthrough()
  .refine((data) => {
    // If online, then the minimum number of professors must be defined
    return data.online ? data.min_professor_number !== null : true;
  }, {
    message: "Il numero minimo di professori deve essere definito se sono abilitate le impostazioni aggiuntive",
    path: ["min_professor_number"]
  }).refine((data) => {
    // If online, then the minimum number of professors for the master's degree must be defined
    return data.online ? data.min_professor_number_masters !== null : true;
  }, {
    message: "Il numero minimo di professori per il corso di laurea magistrale deve essere definito se sono abilitate le impostazioni aggiuntive",
    path: ["min_professor_number_masters"]
  }).refine((data) => {
    // If online, then the maximum number of professors must be defined
    return data.online ? data.max_professor_number !== null : true;
  }, {
    message: "Il numero massimo di professori deve essere definito se sono abilitate le impostazioni aggiuntive",
    path: ["max_professor_number"]
  }).refine((data) => {
    // If online, then the minimum number of professors must be less than or equal to the maximum number of professors
    if (data.online && data.min_professor_number && data.max_professor_number)
      return data.min_professor_number <= data.max_professor_number;
    return true;
  }, {
    message: "Il numero minimo di professori deve essere minore o uguale al numero massimo di professori se sono abilitate le impostazioni aggiuntive",
    path: ["min_professor_number", "max_professor_number"]
  }).refine((data) => {
    // If online, then the minimum number of professors must be less than or equal to the maximum number of professors
    if (data.online && data.min_professor_number && data.max_professor_number)
      return data.min_professor_number <= data.max_professor_number;
    return true;
  }, {
    message: "Il numero minimo di professori deve essere minore o uguale al numero massimo di professori se sono abilitate le impostazioni aggiuntive",
    path: ["min_professor_number_masters", "max_professor_number"]
  }).refine((data) => {
    // If online, then the minimum number of professors for the master's degree must be less than or equal to the maximum number of professors
    if (data.online && data.min_professor_number_masters && data.max_professor_number)
      return data.min_professor_number_masters <= data.max_professor_number;

    return true;
  });

export type OptimizationLog = z.infer<typeof OptimizationLogSchema>;
export type OptimizationConfigurationRecap = z.infer<typeof OptimizationConfigurationRecapSchema>;
export type OptimizationConfiguration = z.infer<typeof OptimizationConfigurationSchema>;

export const OptimizationConfigurationApi = (customFetch = fetch) => ({
  getAll: async (session_id: number) => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${session_id}/configuration`);
    if (!response.ok) throw await response.json() as ApiErrorResponse;

    return z.array(OptimizationConfigurationRecapSchema).parse(await response.json());
  },
  getComplete: async (session_id: number, configuration_id: number) => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${session_id}/configuration/${configuration_id}`);
    if (!response.ok) throw await response.json() as ApiErrorResponse;

    return OptimizationConfigurationSchema.parse(await response.json());
  }
})