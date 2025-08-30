import type {Column} from "@tanstack/table-core";
import {renderComponent} from "@/components/ui/data-table";
import DataTableColumnButton from "@/components/DataTableColumnButton.svelte";

export function sortableHeader<T>(title: string, column: Column<T>) {
  return renderComponent(DataTableColumnButton, {
    title, column,
    onclickcapture: column.getToggleSortingHandler(),
  });
}