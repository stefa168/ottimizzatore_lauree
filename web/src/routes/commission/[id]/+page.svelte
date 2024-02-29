<script lang="ts">
    import * as Tabs from "$lib/components/ui/tabs";
    import StudentsTable from './commission-students-table.svelte'
    import ProfessorsTable from './commission-professors-table.svelte'
    import type {Commission} from "./commission_types";

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


<div class="container mx-auto py-10">
    <h1 class="text-2xl mb-4">{commission.title}</h1>
    <Tabs.Root value="candidates">
        <div id="toolbar" class="w-full">
            <Tabs.List class="content-center">
                <Tabs.Trigger value="candidates">Studenti Candidati</Tabs.Trigger>
                <Tabs.Trigger value="professors">Docenti della Commissione</Tabs.Trigger>
                <Tabs.Trigger value="optimization">Ottimizzazione</Tabs.Trigger>
            </Tabs.List>
        </div>
        <Tabs.Content value="candidates">
            <StudentsTable {commission}/>
        </Tabs.Content>
        <Tabs.Content value="professors" class="text-center">
            <ProfessorsTable {commissionProfessors}/>
        </Tabs.Content>
        <Tabs.Content value="optimization" class="text-center">
            Ottimizzazione
        </Tabs.Content>
    </Tabs.Root>

</div>