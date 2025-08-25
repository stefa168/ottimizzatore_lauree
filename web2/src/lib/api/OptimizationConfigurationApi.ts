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


export const SolutionCommissionSchema = z.object({
  order_key: z.coerce.number().min(0),
  morning: z.coerce.boolean(),
  duration: z.coerce.number().min(0),

  session_id: z.coerce.number(),
  opt_config_id: z.coerce.number(),

  professor_ids: z.array(z.coerce.number()),
  student_ids: z.array(z.coerce.number()),
})

export const OptimizationConfigurationSchema = OptimizationConfigurationRecapSchema.extend({
  max_duration: z.coerce.number().min(0).default(210),
  max_commissions_morning: z.coerce.number().min(0).default(6),
  max_commissions_afternoon: z.coerce.number().min(0).default(6),
  online: z.boolean().default(true),
  run_lock: z.boolean(),

  min_professor_number: z.coerce.number().min(1).default(1),
  min_professor_number_masters: z.coerce.number().min(1).default(1),
  max_professor_number: z.coerce.number().min(1).default(50),

  solver: z.nativeEnum(SolverType).default(SolverType.CPLEX),
  optimization_time_limit: z.coerce.number().min(60).default(60),
  optimization_gap: z.coerce.number().min(0).default(0.005),

  optimization_log: OptimizationLogSchema.optional().nullable(),
  commissions: z.array(SolutionCommissionSchema).optional()
}).passthrough()

// Not using .omit by itself because it is only a schema-side thing and not on the parsing side, so Superforms uses the
// extra fields anyway. The easiest thing to do is just to remove the fields that cause issues with SuperForms.
// https://github.com/colinhacks/zod/discussions/2055
export const OptConfFormSchema = OptimizationConfigurationSchema
  .omit({optimization_log: true, commissions: true})
  .transform(({optimization_log, commissions, ...rest}) => rest);

export type OptimizationLog = z.infer<typeof OptimizationLogSchema>;
export type OptimizationConfigurationRecap = z.infer<typeof OptimizationConfigurationRecapSchema>;
export type OptimizationConfiguration = z.infer<typeof OptimizationConfigurationSchema>;
export type OptimizationConfigurationForm = z.infer<typeof OptConfFormSchema>;
export type SolutionCommission = z.infer<typeof SolutionCommissionSchema>;

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
  },
  updateConfiguration: async (session_id: number, configuration_id: number, updated_configuration: OptimizationConfigurationForm) => {
    console.log(JSON.stringify(updated_configuration))
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${session_id}/configuration/${configuration_id}`, {
      method: 'PATCH',
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(updated_configuration),
    });
    if(!response.ok) throw await response.json() as ApiErrorResponse;

    return OptimizationConfigurationSchema.parse(await response.json());
  }
})