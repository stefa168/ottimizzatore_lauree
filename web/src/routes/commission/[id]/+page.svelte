<script lang="ts">
    import IcOutlineChecklist from '~icons/ic/outline-checklist'
    import IcRoundReportProblem from '~icons/ic/round-report-problem'
    import IcBaselineInfo from '~icons/ic/baseline-info'
    import IcOutlineKeyboardDoubleArrowRight from '~icons/ic/outline-keyboard-double-arrow-right'

    import {selectedProblem} from "$lib/store.js";
    import {goto} from "$app/navigation";

    $: commissionProfessors = $selectedProblem?.entries.flatMap((student) => {
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
    }) ?? [];

    $: professorsWithoutRole = commissionProfessors?.filter((professor) => {
        return professor.role === 'unspecified';
    }) ?? [];

    $: problemsPresent = professorsWithoutRole.length > 0;

    $: bachelorStudents = $selectedProblem?.entries.filter((student) => student.degree_level === "bachelors") ?? [];
    $: masterStudents = $selectedProblem?.entries.filter((student) => student.degree_level === "masters") ?? [];
</script>

<div>
    <h2 class="text-2xl border-b-2 mt-6 mb-4 flex items-center">
        <IcBaselineInfo class="align-baseline"/>
        <span class="ms-2">Informazioni sulla sessione</span>
    </h2>
    <ul class="list-disc list-outside ms-4">
        <li>
            Sessione di {$selectedProblem?.entries.length} laureandi, composta da:
            <ul class="ps-4 list-disc list-outside">
                <li hidden={bachelorStudents.length <=0}>
                    <p>{bachelorStudents.length} studenti triennali</p>
                    <p>Di questi, {bachelorStudents.filter((s) => s.supervisor_assistant !== null).length} hanno un
                        co-relatore</p>
                </li>
                <li>
                    <p>{masterStudents.length} studenti magistrali</p>
                    <p>Di questi {masterStudents.filter((s) => s.supervisor_assistant !== null).length} hanno un
                        co-relatore e {masterStudents.filter((s) => s.counter_supervisor !== null).length} hanno un
                        controrelatore.</p>
                </li>
            </ul>
        </li>
        <li>Alla commissione parteciperanno {commissionProfessors?.length} docenti.</li>
    </ul>
</div>

<div>
    <h2 class="text-2xl border-b-2 mt-6 mb-4 flex items-center">
        {#if problemsPresent}
            <IcRoundReportProblem class="text-destructive"/>
        {:else}
            <IcOutlineChecklist class="text"/>
        {/if}
        <span class="ms-2">Problemi</span>
    </h2>
    {#if problemsPresent}
        <ul class="list-disc list-outside ms-4">
            <li hidden={professorsWithoutRole.length <= 0}>
                {#if professorsWithoutRole.length === 1}
                    <span class="text-destructive"> {professorsWithoutRole.length} docente </span> non ha un ruolo
                    didattico assegnato.
                {:else}
                    <span class="text-destructive"> {professorsWithoutRole.length} docenti </span> non hanno un ruolo
                    didattico assegnato.
                {/if}
                <button class="inline-flex items-center justify-center text-blue-500 hover:underline"
                        on:click={() => goto(`/commission/${$selectedProblem?.id}/professors/`)}>
                    Vai alla sezione
                    <IcOutlineKeyboardDoubleArrowRight/>
                </button>
            </li>
        </ul>
    {:else}
        <p>Non è stato rilevato alcun problema relativo alla sessione di laurea.</p>
    {/if}
</div>