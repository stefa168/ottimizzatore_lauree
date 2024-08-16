<script lang="ts">
    import ProfessorsTable from "../commission-professors-table.svelte";
    import {selectedProblem} from "$lib/store";
    import { writable } from "svelte/store";
    import type {Professor} from "../commission_types";

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
</script>

<ProfessorsTable {commissionProfessors}/>