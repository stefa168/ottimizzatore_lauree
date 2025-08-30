import type {ColumnDef, InitialTableState} from "@tanstack/table-core";
import type {OptimizationConfigurationRecap} from "@/api/OptimizationConfigurationApi";
import {dateFormatter} from "@/utils";
import {renderComponent} from "@/components/ui/data-table";
import {sortableHeader} from "@/components/table/utils";
import DataTableActions from "./DataTableActions.svelte";
import NewConfigurationButton from "./NewConfigurationButton.svelte";

export const initialTableState: () => InitialTableState = () => ({
  sorting: [{
    id: 'id',
    desc: false
  }]
});

export const columns: (session_id: number) => ColumnDef<OptimizationConfigurationRecap>[] = (session_id) => [
  {
    accessorKey: "id",
    header: ({column}) => sortableHeader("ID", column)
  },
  {
    accessorKey: 'title',
    header: ({column}) => sortableHeader("Titolo", column)
  },
  {
    accessorKey: "created_at",
    header: ({column}) => sortableHeader("Data di Creazione", column),
    cell: ({row}) => dateFormatter.format(row.original.created_at)
  },
  {
    id: 'actions',
    header: ({}) => renderComponent(NewConfigurationButton, {session_id}),
    cell: ({row}) => renderComponent(DataTableActions, {session_id, configuration_id: row.original.id})
  }
]