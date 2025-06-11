<script lang="ts">
    import {getProfessorBurden, type Professor} from "./commission_types";
    import {createRender, createTable, Render, Subscribe} from "svelte-headless-table";
    import {writable} from "svelte/store";
    // noinspection TypeScriptCheckImport
    import {env} from "$env/dynamic/public";
    import * as Table from "$lib/components/ui/table"
    import EditableProfessorRole from "./EditableProfessorRole.svelte";
    import type {UniversityRole} from "./commission_types.js";
    import {toast} from "svelte-sonner";
    import StyledFullName from "./StyledFullName.svelte";
    import ProfessorBurden from "./professors/ProfessorBurden.svelte";
    import EditableProfessorAvailability from "./professors/EditableProfessorAvailability.svelte";

    let {commissionProfessors = writable<Professor[]>([])} = $props();
    const table = createTable(commissionProfessors);

    const columns = table.createColumns([
        table.column({
            accessor: 'surname',
            header: 'Cognome',
            cell: ({value}) => createRender(StyledFullName, {surname: value, applyStyle: true})
        }),
        table.column({
            accessor: 'name',
            header: 'Nome',
            cell: ({value}) => createRender(StyledFullName, {name: value, applyStyle: false})
        }),
        table.column({
            accessor: 'role',
            header: 'Ruolo Universitario',
            cell: ({row, value}) => createRender(EditableProfessorRole, {
                row, value, onUpdateValue: updateProfessorField
            })
        }),
        table.column({
            accessor: 'availability',
            header: "Disponibilità",
            cell: ({row, value}) => createRender(EditableProfessorAvailability, {
                row, value, onUpdateValue: updateProfessorField
            })
        }),
        table.column({
            accessor: (p: Professor) => getProfessorBurden(p),
            header: 'Carico',
            cell: ({value}) => {
                return createRender(ProfessorBurden, {burden: value})
            }
        })
    ]);

    const {headerRows, pageRows, tableAttrs, tableBodyAttrs} = table.createViewModel(columns);

    async function updateProfessorField<T extends keyof Professor>(professor: Professor, field: T, newValue: Professor[T]): Promise<boolean> {
        return await fetch(`${env.PUBLIC_API_URL}/professor/${professor.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({[field]: newValue})
        }).then(async (response) => {
            if (response.ok) {
                let data: { professor: Professor, response: string; } = await response.json();

                commissionProfessors.update(professors => {
                    const index = professors.findIndex(p => p.id === professor.id);
                    if (index !== -1) {
                        professors[index] = data.professor;
                    }
                    return professors;
                });

                console.log(`Dettagli del professore aggiornati correttamente`);
                toast.success('Dettagli del professore aggiornati correttamente');
                return true;
            } else {
                throw new Error(`Errore durante l'aggiornamento del campo ${field} del professore (${response.statusText})`);
            }
        }).catch(error => {
            toast.error(`Errore durante l'aggiornamento del ruolo del professore: ${error}`);
            return false;
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