<script lang="ts">
    import {selectedProblem} from "$lib/store.js";

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
    });

    $: bachelorStudents = $selectedProblem?.entries.filter((student) => student.degree_level === "bachelors") ?? [];
    $: masterStudents = $selectedProblem?.entries.filter((student) => student.degree_level === "masters") ?? [];
</script>

<h2 class="text-2xl border-b-2 mt-6 mb-4">Informazioni sulla commissione</h2>
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
                <p>Di questi, {masterStudents.filter((s) => s.supervisor_assistant !== null).length} hanno un
                    co-relatore, e {masterStudents.filter((s) => s.counter_supervisor !== null).length} hanno un
                    controrelatore.</p>
            </li>
        </ul>
    </li>
    <li>Alla commissione parteciperanno {commissionProfessors?.length} docenti.</li>
</ul>