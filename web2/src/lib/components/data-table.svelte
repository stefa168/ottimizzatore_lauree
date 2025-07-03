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
  import * as Select from "@/components/ui/select"
  import {Button} from "@/components/ui/button";

  import {LucideChevronsLeft, LucideChevronsRight, LucideChevronLeft, LucideChevronRight} from "@lucide/svelte";
  import ButtonGroup from "@/components/ButtonGroup.svelte";
  import type {TextTemplates} from "@/types";
  import {formatText} from "@/utils";

  type DataTableProps<TData, TValue> = {
    columns: ColumnDef<TData, TValue>[];
    data: TData[];
    singlePlural?: TextTemplates;
  };

  let {data, columns, singlePlural = {
    singular: (n: number) => "È presente un solo elemento.",
    plural: (n: number) => `Sono presenti un totale di ${n} elementi.`
  }}: DataTableProps<TData, TValue> = $props();

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
  <div class="flex items-center justify-between px-2 py-4">
    <div class="text-muted-foreground flex-1 text-sm">
      <!--{table.getFilteredSelectedRowModel().rows.length} of-->
      <!--{table.getFilteredRowModel().rows.length} row(s) selected.-->
      {formatText(singlePlural, table.getFilteredRowModel().rows.length)}
    </div>
    <div class="flex items-center space-x-6 lg:space-x-8">
      <div class="flex items-center space-x-2">
        <p class="text-sm font-medium">Righe per pagina</p>
        <Select.Root
            allowDeselect={false}
            type="single"
            value={`${table.getState().pagination.pageSize}`}
            onValueChange={(value) => {
						table.setPageSize(Number(value));
					}}
        >
          <Select.Trigger class="h-8 w-[70px]">
            {String(table.getState().pagination.pageSize)}
          </Select.Trigger>
          <Select.Content side="top">
            {#each [10, 20, 30, 40, 50] as pageSize (pageSize)}
              <Select.Item value={`${pageSize}`}>
                {pageSize}
              </Select.Item>
            {/each}
          </Select.Content>
        </Select.Root>
      </div>
      <div class="flex w-[100px] items-center justify-center text-sm font-medium">
        Pagina {table.getState().pagination.pageIndex + 1} di {table.getPageCount()}
      </div>
      <ButtonGroup>
        <Button
            variant="outline"
            class="hidden size-8 p-0 lg:flex"
            onclick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
        >
          <span class="sr-only">Torna alla prima pagina</span>
          <LucideChevronsLeft/>
        </Button>
        <Button
            variant="outline"
            class="size-8 p-0"
            onclick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
        >
          <span class="sr-only">Torna alla pagina precedente</span>
          <LucideChevronLeft/>
        </Button>
        <Button
            variant="outline"
            class="size-8 p-0"
            onclick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
        >
          <span class="sr-only">Vai alla pagina successiva</span>
          <LucideChevronRight/>
        </Button>
        <Button
            variant="outline"
            class="hidden size-8 p-0 lg:flex"
            onclick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
        >
          <span class="sr-only">Vai all'ultima pagina</span>
          <LucideChevronsRight/>
        </Button>
      </ButtonGroup>
    </div>
  </div>
</div>