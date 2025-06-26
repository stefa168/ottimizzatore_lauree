import type {ColumnDef} from "@tanstack/table-core";
import type {GradSession} from "@/types";
import {createRawSnippet} from "svelte";
import {renderComponent, renderSnippet} from "@/components/ui/data-table";
import DataTableActions from "./DataTableActions.svelte";

const dateFormatter = new Intl.DateTimeFormat('it-IT', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit'
});

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