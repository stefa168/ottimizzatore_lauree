import type {ColumnDef} from "@tanstack/table-core";
import type {OptimizationConfigurationRecap} from "@/api/OptimizationConfigurationApi";
import {dateFormatter} from "@/utils";
import {renderComponent, renderSnippet} from "@/components/ui/data-table";
import DataTableActions from "./DataTableActions.svelte";
import NewConfigurationButton from "./NewConfigurationButton.svelte";

export const columns: (session_id: number) => ColumnDef<OptimizationConfigurationRecap>[] = (session_id) => [
  {
    accessorKey: "id",
    header: "ID"
  },
  {
    accessorKey: 'title',
    header: "Titolo"
  },
  {
    accessorKey: "created_at",
    header: "Data di Creazione",
    cell: ({row}) => dateFormatter.format(row.original.created_at)
  },
  {
    id: 'actions',
    header: ({}) => renderComponent(NewConfigurationButton, {session_id}),
    cell: ({row}) => renderComponent(DataTableActions, {session_id, configuration_id: row.original.id})
  }
]