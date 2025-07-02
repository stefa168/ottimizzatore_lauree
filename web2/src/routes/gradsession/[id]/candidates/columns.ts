import type {ColumnDef} from "@tanstack/table-core";
import type {GradSessionEntry, SessionProfessor} from "@/types";
import {renderComponent} from "@/components/ui/data-table";
import StyledFullName from "@/components/StyledFullName.svelte";
import {getDegreeLevelString} from "@/utils";
import LucideHash from '~icons/lucide/hash'

// Using row instead of getValue because for some reason it results to be unknown 🤔
// https://tanstack.com/table/v8/docs/guide/column-defs#cell-formatting
export const columns: (professorMap: Map<number, SessionProfessor>) => ColumnDef<GradSessionEntry>[] = (professorMap) => [
  {
    id: "id",
    header: () => renderComponent(LucideHash),
    cell: ({row}) => row.index + 1,
  },
  {
    id: "candidate",
    header: "Candidato",
    cell: ({row}) => renderComponent(StyledFullName, {fullName: row.original.candidate})
  },
  {
    id: "degree_level",
    header: "Tipo di Laurea",
    cell: ({row}) => getDegreeLevelString(row.original),
  },
  {
    id: "supervisor",
    header: "Relatore",
    accessorKey: "supervisor_id",
    cell: ({row}) => renderComponent(StyledFullName, {fullName: professorMap.get(row.original.supervisor_id)})
  },
  {
    id: "supervisor_assistant",
    header: "Co-Relatore",
    accessorKey: "supervisor_assistant_id",
    cell: ({row}) => renderComponent(StyledFullName, {fullName: professorMap.get(row.original.supervisor_assistant_id ?? -1)})
  },
  {
    id: "counter_supervisor",
    header: "Controrelatore",
    accessorKey: "counter_supervisor_id",
    cell: ({row}) => renderComponent(StyledFullName, {fullName: professorMap.get(row.original.counter_supervisor_id ?? -1)})
  }
]