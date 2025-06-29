import type {LayoutLoad} from "./$types";

export const load: LayoutLoad = ({params}) => {
  const session_id = Number.parseInt(params.id);
  return {session_id}
}