<script lang="ts">
    import StudentsTable from '../commission-students-table.svelte';
    import type {Commission} from "../commission_types";

    export let data: { commissionId: string, commissionData: Commission };

    $: commission = data.commissionData
</script>

<StudentsTable {commission}/>