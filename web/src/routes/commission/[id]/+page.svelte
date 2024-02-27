<script lang="ts">
    import * as Tabs from "$lib/components/ui/tabs";
    import DataTable from './commission-table.svelte'
    export let data;

    $: commission = data.commissionData
</script>


<div class="container mx-auto py-10">
    <h1 class="text-2xl mb-4">{commission.title}</h1>
    <Tabs.Root value="candidates">
        <div id="toolbar" class="w-full">
            <Tabs.List class="content-center">
                <Tabs.Trigger value="candidates">Candidati</Tabs.Trigger>
                <Tabs.Trigger value="professors">Docenti</Tabs.Trigger>
                <Tabs.Trigger value="optimization">Ottimizzazione</Tabs.Trigger>
            </Tabs.List>
        </div>
        <Tabs.Content value="candidates">
            <DataTable {commission}/>
        </Tabs.Content>
        <Tabs.Content value="professors" class="text-center">
            Change your password here.
        </Tabs.Content>
        <Tabs.Content value="optimization" class="text-center">
            Ottimizzazione
        </Tabs.Content>
    </Tabs.Root>

</div>