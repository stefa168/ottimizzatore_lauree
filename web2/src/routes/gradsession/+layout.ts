import type {LayoutLoad} from './$types';
import {GradSessionApi} from "@/api/GradSesssionApi";
import {transformGradSession} from "@/api/RawTypes";

export const load: LayoutLoad = ({fetch}) => {
  return {
    sessions: GradSessionApi(fetch).getAll().then(raw => raw.map(transformGradSession))
  }
}