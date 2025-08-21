import type {PageLoad} from './$types';
import {type OptimizationConfiguration, OptimizationConfigurationApi} from "@/api/OptimizationConfigurationApi";
import {fromRawList} from "@/api/RawTypes";

export const load: PageLoad = async ({parent, fetch}) => {
  const p = await parent();
  return {
    configurations: await OptimizationConfigurationApi(fetch).getAll(p.session_id).then(fromRawList<OptimizationConfiguration>)
  }
}