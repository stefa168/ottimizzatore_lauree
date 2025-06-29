import type {LayoutLoad} from "./$types";
import {GradSessionApi} from "@/api/GradSesssionApi";
import {transformGradSession, transformSessionProfessor} from "@/api/RawTypes";

export const load: LayoutLoad = async ({params, parent, fetch}) => {
  const session_id = Number.parseInt(params.id);
  let api = GradSessionApi(fetch);

  return {
    session_id: session_id,
    // todo add svelte error page
    session: await api.getById(session_id).then(transformGradSession),
    student_entries: await api.getStudents(session_id),
    professors: await api.getProfessors(session_id).then(lst => lst.map(transformSessionProfessor))
  };
}