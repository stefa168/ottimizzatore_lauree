import type {PageLoad} from './$types';
import {OptimizationConfigurationApi} from "@/api/OptimizationConfigurationApi";
import {z} from "zod";

export const load: PageLoad = async ({parent, fetch, params}) => {
  const session_id = Number.parseInt(params.id);

  return {
    configurations: await OptimizationConfigurationApi(fetch).getAll(session_id)
  }
}