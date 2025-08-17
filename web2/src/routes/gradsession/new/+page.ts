import type {PageLoad} from "./$types";
import {GradSessionApi} from "@/api/GradSesssionApi";

export const load: PageLoad = async ({parent, fetch}) => {
  return {
    expectedColumns: await GradSessionApi(fetch).getRequiredColumns()
  }
}