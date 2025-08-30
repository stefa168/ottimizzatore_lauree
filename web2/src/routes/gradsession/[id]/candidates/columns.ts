import type {ColumnDef, InitialTableState} from "@tanstack/table-core";
import type {GradSessionEntry, SessionProfessor} from "@/types";
import {renderComponent} from "@/components/ui/data-table";
import StyledFullName from "@/components/StyledFullName.svelte";
import {fullName, getDegreeLevelString} from "@/utils";
import LucideHash from '~icons/lucide/hash'
import {sortableHeader} from "@/components/table/utils";
import DataTableColumnFilterButton from "@/components/DataTableColumnFilterButton.svelte";
import {DegreeLevels} from "@/const";

export const initialTableState: () => InitialTableState = () => ({
  sorting: [{
    id: 'candidate',
    desc: false
  }]
});

// Using row instead of getValue because for some reason it results to be unknown 🤔
// https://tanstack.com/table/v8/docs/guide/column-defs#cell-formatting
export const columns: (professorMap: Map<number, SessionProfessor>) => ColumnDef<GradSessionEntry>[] = (professorMap) => [
  {
    id: "id",
    accessorFn: entry => entry.id,
    header: ({column}) => sortableHeader("ID", column),
    cell: ({row}) => row.index + 1,
  },
  {
    id: "candidate",
    accessorFn: entry => fullName(entry.candidate),
    header: ({column}) => sortableHeader("Candidato", column),
    cell: ({row}) => renderComponent(StyledFullName, {fullName: row.original.candidate})
  },
  {
    id: "degree_level",
    accessorFn: entry => entry.degree_level,
    header: ({column}) => renderComponent(DataTableColumnFilterButton<GradSessionEntry>, {
      title: 'Tipo di Laurea',
      entriesMap: DegreeLevels,
      column
    }),
    cell: ({row}) => getDegreeLevelString(row.original),
  },
  {
    id: "supervisor",
    header: ({column}) => sortableHeader("Relatore", column),
    accessorFn: entry => fullName(professorMap.get(entry.supervisor_id)?.professor),
    cell: ({row}) => renderComponent(StyledFullName, {fullName: professorMap.get(row.original.supervisor_id)?.professor})
  },
  {
    id: "supervisor_assistant",
    header: ({column}) => sortableHeader("Co-Relatore", column),
    accessorFn: entry => fullName(professorMap.get(entry.supervisor_assistant_id ?? -1)?.professor),
    cell: ({row}) => renderComponent(StyledFullName, {fullName: professorMap.get(row.original.supervisor_assistant_id ?? -1)?.professor})
  },
  {
    id: "counter_supervisor",
    header: ({column}) => sortableHeader("Controrelatore", column),
    accessorFn: entry => fullName(professorMap.get(entry.counter_supervisor_id ?? -1)?.professor),
    cell: ({row}) => renderComponent(StyledFullName, {fullName: professorMap.get(row.original.counter_supervisor_id ?? -1)?.professor})
  }
]