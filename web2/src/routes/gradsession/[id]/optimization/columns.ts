import type {ColumnDef, InitialTableState} from "@tanstack/table-core";
import type {OptimizationConfigurationRecap} from "@/schema/optimization";
import {dateFormatter} from "@/utils";
import {renderComponent} from "@/components/ui/data-table";
import {sortableHeader} from "@/components/table/utils";
import DataTableActions from "./DataTableActions.svelte";
import NewConfigurationButton from "./NewConfigurationButton.svelte";
import ConfigurationTitle from "./ConfigurationTitle.svelte";

export const initialTableState: () => InitialTableState = () => ({
  sorting: [{
    id: 'id',
    desc: false
  }]
});

export const columns: (
  session_id: number,
  // Read when rendering, so the badge follows the session when it's refreshed
  usedConfigurationId: () => number | null
) => ColumnDef<OptimizationConfigurationRecap>[] = (session_id, usedConfigurationId) => [
  {
    accessorKey: "id",
    header: ({column}) => sortableHeader("ID", column)
  },
  {
    accessorKey: 'title',
    header: ({column}) => sortableHeader("Titolo", column),
    cell: ({row}) => renderComponent(ConfigurationTitle, {
      title: row.original.title,
      frozen: row.original.frozen,
      used: row.original.id === usedConfigurationId()
    })
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