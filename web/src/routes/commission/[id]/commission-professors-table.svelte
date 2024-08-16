<script lang="ts">
    import type {Professor} from "./commission_types";
    import {createRender, createTable, Render, Subscribe} from "svelte-headless-table";
    import {writable} from "svelte/store";
    // noinspection TypeScriptCheckImport
    import {env} from "$env/dynamic/public";
    import * as Table from "$lib/components/ui/table"
    import EditableProfessorRole from "./EditableProfessorRole.svelte";
    import type {UniversityRole} from "./commission_types.js";
    import {toast} from "svelte-sonner";
    import StyledFullName from "./StyledFullName.svelte";

    export let commissionProfessors = writable<Professor[]>([]);
    const table = createTable(commissionProfessors);

    const columns = table.createColumns([
        table.column({
            accessor: 'surname',
            header: 'Cognome',
            cell: ({value}) => createRender(StyledFullName, {surname: value, applyStyle: false})
        }),
        table.column({
            accessor: 'name',
            header: 'Nome',
            cell: ({value}) => createRender(StyledFullName, {name: value, applyStyle: false})
        }),
        table.column({
            accessor: 'role',
            header: 'Ruolo Universitario',
            cell: ({row, column, value}) => {
                return createRender(EditableProfessorRole, {
                    row,
                    column,
                    value,
                    onUpdateValue: updateData
                })
            }
        })
    ]);

    const {headerRows, pageRows, tableAttrs, tableBodyAttrs} = table.createViewModel(columns);

    async function updateData(professor: Professor, columnId: string, newValue: UniversityRole) {
        const oldValue = professor.role;
        professor.role = newValue;

        await fetch(`${env.PUBLIC_API_URL}/professor/${professor.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({role: newValue})
        }).then(response => {
            if (response.ok) {
                console.log(`Ruolo del professore aggiornato correttamente`);
                toast.success('Ruolo del professore aggiornato correttamente');
            } else {
                // toast.error(`Errore durante l'aggiornamento del ruolo del professore (${response.statusText})`);
                throw new Error(`Errore durante l'aggiornamento del ruolo del professore (${response.statusText})`);
            }

            commissionProfessors.update(p => p)
        }).catch(error => {
            toast.error(`Errore durante l'aggiornamento del ruolo del professore: ${error}`);
            professor.role = oldValue;
        });
    }
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