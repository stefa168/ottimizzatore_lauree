<script lang="ts">
    import type {Commission} from "../commission_types";
    import ProfessorsTable from "../commission-professors-table.svelte";

    export let data: { commissionId: string, commissionData: Commission };

    $: commissionProfessors = data.commissionData.entries.flatMap((student) => {
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
</script>

<ProfessorsTable {commissionProfessors}/>