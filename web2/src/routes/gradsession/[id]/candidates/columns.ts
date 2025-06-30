import type {ColumnDef} from "@tanstack/table-core";
import type {GradSessionEntry} from "@/types";
import {renderComponent} from "@/components/ui/data-table";
import StyledFullName from "@/components/StyledFullName.svelte";

/*
export const columns: ColumnDef<GradSession>[] = [
  {
    accessorKey: "title",
    header: "Nome Sessione"
  }, {
    accessorKey: "created_at",
    header: "Data dell'Upload",
    cell: ({row}) => dateFormatter.format(row.original.created_at)
  }, {
    id: "actions",
    cell: ({row}) => {
      return renderComponent(DataTableActions, {id: row.original.id})
    }
  }
];
*/

export const columns: ColumnDef<GradSessionEntry>[] = [
  {
    id: "candidate",
    header: "Candidato",
    cell: ({row}) => {
      const s = row.original.candidate;
      return renderComponent(StyledFullName, {name: })
    }
  }
]