<script lang="ts">
    import DataTable from './commission-table.svelte'
    export let data;

    $: commission = data.commissionData
</script>


<div class="container mx-auto py-10">
    <h1 class="text-2xl mb-4">{commission.title}</h1>
    <DataTable {commission}/>
</div>