<script lang="ts">
    import type {Commission} from "../commission_types";
    import {createTable, Subscribe, Render, createRender} from "svelte-headless-table";
    import {readable} from "svelte/store";
    import * as Table from "$lib/components/ui/table"
    import StyledFullName from "../StyledFullName.svelte";

    interface Props {
        commission: Commission;
    }

    let {commission}: Props = $props();
    const table = createTable(readable(commission.entries));

    function getFullNameIfPresent(value: { name: string, surname: string } | null) {
        if (value === null) {
            return createRender(StyledFullName, {name: null, surname: null})
        } else {
            return createRender(StyledFullName, {name: value.name, surname: value.surname})
        }
    }

    const columns = table.createColumns([
        table.column({
            accessor: 'candidate',
            header: "Candidato",
            cell: ({value}) => getFullNameIfPresent(value)
        }),
        table.column({
            accessor: 'degree_level',
            header: "Tipo di Laurea",
            cell: ({value}) => {
                switch (value) {
                    case "bachelors":
                        return "Triennale";
                    case "masters":
                        return "Magistrale";
                    default:
                        return value;
                }
            }
        }),
        table.column({
            accessor: 'supervisor',
            header: 'Relatore',
            cell: ({value}) => getFullNameIfPresent(value)
        }),
        table.column({
            accessor: 'supervisor_assistant',
            header: 'Co-Relatore',
            cell: ({value}) => getFullNameIfPresent(value)
        }),
        table.column({
            accessor: 'counter_supervisor',
            header: 'Contro-Relatore',
            cell: ({value}) => getFullNameIfPresent(value)
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
                            <Subscribe attrs={cell.attrs()} props={cell.props()}>
                                {#snippet children({attrs})}
                                    <Table.Head {...attrs}>
                                        <Render of={cell.render()}/>
                                    </Table.Head>
                                {/snippet}
                            </Subscribe>
                        {/each}
                    </Table.Row>
                </Subscribe>
            {/each}
        </Table.Header>
        <Table.Body {...$tableBodyAttrs}>
            {#each $pageRows as row (row.id)}
                <Subscribe rowAttrs={row.attrs()}>
                    {#snippet children({rowAttrs})}
                        <Table.Row {...rowAttrs}>
                            {#each row.cells as cell (cell.id)}
                                <Subscribe attrs={cell.attrs()}>
                                    {#snippet children({attrs})}
                                        <Table.Cell {...attrs}>
                                            <Render of={cell.render()}/>
                                        </Table.Cell>
                                    {/snippet}
                                </Subscribe>
                            {/each}
                        </Table.Row>
                    {/snippet}
                </Subscribe>
            {/each}
        </Table.Body>
    </Table.Root>
</div>