<script lang="ts">
    import * as Alert from "$lib/components/ui/alert";

    import {writable} from "svelte/store";
    import {selectedProblem} from "$lib/store";
    import {capitalizeProfessor} from "$lib/utils";
    import type {Professor} from "../commission_types";
    import ProfessorsTable from "../commission-professors-table.svelte";
    import IcOutlineReportProblem from '~icons/ic/outline-report-problem'

    export let commissionProfessors = writable<Professor[]>(
        $selectedProblem?.entries.flatMap((student) => {
            let professors = [student.supervisor];
            if (student.supervisor_assistant != null) {
                professors.push(student.supervisor_assistant);
            }
            if (student.counter_supervisor != null) {
                professors.push(student.counter_supervisor);
            }
            return professors;
        }).filter((professor, index, self) => {
            return index === self.findIndex((p) => p.id === professor.id);
        }).sort((a, b) => {
            return a.surname.localeCompare(b.surname);
        }) ?? []
    );

    $: professorsWithoutRole = $commissionProfessors?.filter((professor) => {
        return professor.role === 'unspecified';
    }) ?? [];

</script>

<Alert.Root variant="destructive" class="mb-4">
    <Alert.Title>
        <h3 class="text-lg flex items-center">
                <IcOutlineReportProblem class="text-destructive"/>
            <span class="ms-2">Rilevati problemi con i Docenti della sessione</span>
        </h3>
    </Alert.Title>
    <Alert.Description>
        <ul class="list-disc list-outside ms-4">
            <li hidden={professorsWithoutRole.length <= 0}>
                {#if professorsWithoutRole.length === 1}
                    <span class="font-bold"> {capitalizeProfessor(professorsWithoutRole[0])} </span>
                    non ha un ruolo didattico assegnato.
                {:else}
                    <span>I seguenti Docenti non hanno un ruolo didattico assegnato:</span>
                    <ul class="list-disc list-outside ms-4">
                        {#each professorsWithoutRole as p}
                            <li class="font-bold">{capitalizeProfessor(p)}</li>
                        {/each}
                    </ul>
                {/if}
            </li>
        </ul>
    </Alert.Description>
</Alert.Root>

<ProfessorsTable {commissionProfessors}/>