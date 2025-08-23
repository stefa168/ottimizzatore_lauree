import type {PageLoad} from './$types';
import {OptimizationConfigurationApi} from "@/api/OptimizationConfigurationApi";

export const load: PageLoad = async ({fetch, params}) => {
  const session_id = Number.parseInt(params.id);
  const config_id = Number.parseInt(params.conf_id);
  return {
    configuration: await OptimizationConfigurationApi(fetch).getComplete(session_id, config_id)
  }
}