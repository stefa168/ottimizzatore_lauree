import type {ColumnDef} from "@tanstack/table-core";
import type {OptimizationConfiguration} from "@/api/OptimizationConfigurationApi";
import {dateFormatter} from "@/utils";
import {renderComponent} from "@/components/ui/data-table";
import DataTableActions from "./DataTableActions.svelte";

export const columns: (session_id: number) => ColumnDef<OptimizationConfiguration>[] = (session_id) => [
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
    cell: ({row}) => {
      return renderComponent(DataTableActions, {session_id, configuration_id: row.original.id});
    }
  }
]