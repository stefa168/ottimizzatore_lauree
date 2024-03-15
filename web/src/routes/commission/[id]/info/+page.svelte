<script lang="ts">
    import type {Commission} from "../commission_types";

    export let data: { commissionId: string, commissionData: Commission };

    $: commission = data.commissionData
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

<h2 class="">Informazioni sulla commissione</h2>
<ul class="list-disc ms-4">
    <li>Sessione composta da {commission.entries.length} studenti</li>
    <li>Commissione composta da {commissionProfessors.length} docenti</li>
</ul>