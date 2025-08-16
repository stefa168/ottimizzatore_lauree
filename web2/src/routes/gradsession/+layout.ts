import type {LayoutLoad} from './$types';
import {GradSessionApi} from "@/api/GradSesssionApi";
import {fromRawList} from "@/api/RawTypes";
import type {GradSession} from "@/types";

export const load: LayoutLoad = ({fetch}) => {
  return {
    sessions: GradSessionApi(fetch).getAll().then(fromRawList<GradSession>)
  }
}