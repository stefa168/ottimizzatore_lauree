import {PUBLIC_BACKEND_URL} from "@/const";
import type {ApiErrorResponse, CreationUpdateDate} from "@/types";
import type {WithRawDates} from "@/api/RawTypes";

export interface OptimizationConfiguration extends CreationUpdateDate {
  id: number,
  session_id: number,
  title: string,
}

export type RawOptimizationConfiguration = WithRawDates<OptimizationConfiguration>;

export const OptimizationConfigurationApi = (customFetch = fetch) => ({
  getAll: async (session_id: number) => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${session_id}/configuration`);
    if (!response.ok)
      throw await response.json() as ApiErrorResponse;

    return await response.json() as RawOptimizationConfiguration[];
  }
})