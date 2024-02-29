<script lang="ts">
    import type {Professor} from "./commission_types";
    import {createTable, Render, Subscribe} from "svelte-headless-table";
    import {readable} from "svelte/store";
    import * as Table from "$lib/components/ui/table"

    export let commissionProfessors: Professor[];
    const table = createTable(readable(commissionProfessors));

    const columns = table.createColumns([
        table.column({
            accessor: 'name',
            header: 'Nome'
        }),
        table.column({
            accessor: 'surname',
            header: 'Cognome'
        }),
        table.column({
            accessor: 'role',
            header: 'Ruolo Universitario'
        })
    ]);

    const {headerRows, pageRows, tableAttrs, tableBodyAttrs} = table.createViewModel(columns);
</script>

<div class="rounded-md border">
    <Table.Root {...$tableAttrs}>
        <Table.Header>
            {#each $headerRows as headerRow}
                <Subscribe rowAttrs={headerRow.attrs()}>
                    <Table.Row>
                        {#each headerRow.cells as cell (cell.id)}
                            <Subscribe attrs={cell.attrs()} let:attrs props={cell.props()}>
                                <Table.Head {...attrs}>
                                    <Render of={cell.render()}/>
                                </Table.Head>
                            </Subscribe>
                        {/each}
                    </Table.Row>
                </Subscribe>
            {/each}
        </Table.Header>
        <Table.Body {...$tableBodyAttrs}>
            {#each $pageRows as row (row.id)}
                <Subscribe rowAttrs={row.attrs()} let:rowAttrs>
                    <Table.Row {...rowAttrs}>
                        {#each row.cells as cell (cell.id)}
                            <Subscribe attrs={cell.attrs()} let:attrs>
                                <Table.Cell {...attrs}>
                                    <Render of={cell.render()}/>
                                </Table.Cell>
                            </Subscribe>
                        {/each}
                    </Table.Row>
                </Subscribe>
            {/each}
        </Table.Body>
    </Table.Root>
</div>