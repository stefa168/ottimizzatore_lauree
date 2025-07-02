<script lang="ts" generics="TData, TValue">
  import {
    type ColumnDef,
    getCoreRowModel,
    getPaginationRowModel,
    type PaginationState,
    type Table as TableType
  } from "@tanstack/table-core";
  import {createSvelteTable, FlexRender} from "@/components/ui/data-table";
  import * as Table from "@/components/ui/table";
  import {Button} from "@/components/ui/button";

  type DataTableProps<TData, TValue> = {
    columns: ColumnDef<TData, TValue>[];
    data: TData[];
  };

  let {data, columns}: DataTableProps<TData, TValue> = $props();

  let pagination = $state<PaginationState>({pageIndex: 0, pageSize: 10});

  const table = createSvelteTable({
    get data() {
      return data;
    },
    columns,
    state: {
      get pagination() {
        return pagination;
      },
    },
    onPaginationChange: (updater) => {
      if (typeof updater === 'function') {
        pagination = updater(pagination);
      } else {
        pagination = updater
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  })
</script>



<div>
  <div class="rounded-md border">
    <Table.Root>
      <Table.Header>
        {#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
          <Table.Row>
            {#each headerGroup.headers as header (header.id)}
              <Table.Head>
                {#if !header.isPlaceholder}
                  <FlexRender
                      content={header.column.columnDef.header}
                      context={header.getContext()}
                  />
                {/if}
              </Table.Head>
            {/each}
          </Table.Row>
        {/each}
      </Table.Header>
      <Table.Body>
        {#each table.getRowModel().rows as row (row.id)}
          <Table.Row data-state={row.getIsSelected() && "selected"}>
            {#each row.getVisibleCells() as cell (cell.id)}
              <Table.Cell>
                <FlexRender
                    content={cell.column.columnDef.cell}
                    context={cell.getContext()}
                />
              </Table.Cell>
            {/each}
          </Table.Row>
        {:else}
          <Table.Row>
            <Table.Cell colspan={columns.length} class="h-24 text-center">
              No results.
            </Table.Cell>
          </Table.Row>
        {/each}
      </Table.Body>
    </Table.Root>
  </div>
  <div class="flex items-center justify-end space-x-2 py-4">
    <Button
        variant="outline"
        size="sm"
        onclick={() => table.previousPage()}
        disabled={!table.getCanPreviousPage()}>
      Precedente
    </Button>
    <Button
        variant="outline"
        size="sm"
        onclick={() => table.nextPage()}
        disabled={!table.getCanNextPage()}
    >
      Successivo
    </Button>
  </div>
</div>