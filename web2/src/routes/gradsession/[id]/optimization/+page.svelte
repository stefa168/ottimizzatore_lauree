<script lang="ts">
  import type {PageProps} from './$types';
  import DataTable from "@/components/data-table.svelte";
  import {columns} from "./columns";
  import {initialTableState} from "./columns";
  import type {OptimizationConfigurationRecap} from "@/schema/optimization";
  import {getConfigurations} from "@/api/optimization.remote";

  let {params}: PageProps = $props();
  const sessionId = $derived(Number(params.id));
  const configurations = $derived(await getConfigurations(sessionId));

  let t: DataTable<OptimizationConfigurationRecap, string> | undefined = $state();
  let table = $derived(t?.table)
</script>

<DataTable
    bind:this={t}
    data={configurations}
    columns={columns(sessionId)}
    initialState={initialTableState()}
/>