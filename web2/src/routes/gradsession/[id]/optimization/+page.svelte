<script lang="ts">
  import type {PageProps} from './$types';
  import DataTable from "@/components/data-table.svelte";
  import {columns} from "./columns";
  import {initialTableState} from "./columns";
  import type {OptimizationConfigurationRecap} from "@/api/OptimizationConfigurationApi";

  let {data}: PageProps = $props();

  let t: DataTable<OptimizationConfigurationRecap, string> | undefined = $state();
  let table = $derived(t?.table)
</script>

<DataTable
    bind:this={t}
    data={data.configurations}
    columns={columns(data.session_id)}
    initialState={initialTableState()}
/>