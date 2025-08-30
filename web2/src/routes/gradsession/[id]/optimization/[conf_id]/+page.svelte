<script lang="ts">
  import {browser} from "$app/environment";
  import type {PageProps} from './$types';
  import {debugEnabled} from "@/store.svelte";
  import OptimizationConfigurationOptions from "./OptimizationConfigurationOptions.svelte";
  import Inspect from "svelte-inspect-value";
  import type {OptimizationStatus} from "@/types";
  import {optimizationTaskStatusFactory} from "@/utils";
  import {getSessionData} from "../../../SessionData.svelte";
  import OptimizationResultsCard from "./OptimizationResultsCard.svelte";

  let {data}: PageProps = $props();
  let configuration = $derived(data.configuration);

  let optConfForm: OptimizationConfigurationOptions | null = $state(null);
  const sessionData = getSessionData();
  let optStatus: OptimizationStatus = $derived(optimizationTaskStatusFactory(configuration))

  const InspectVals = Inspect.Values.withOptions(() => ({
    expandLevel: 0,
    elementAttributes: {style: 'margin-bottom: calc(var(--spacing) * 4)'} // Directly from tailwind
  }));

  const optimizationStartPreflight = async () => optConfForm !== null && !optConfForm?.hasTaintedFields() && await optConfForm?.isValid()
</script>

{#if browser && $debugEnabled}
  <InspectVals {configuration} {optStatus} {sessionData}/>
{/if}

<OptimizationResultsCard {optStatus} {sessionData} bind:configuration {optimizationStartPreflight}/>

{#key configuration}
  <OptimizationConfigurationOptions bind:this={optConfForm} {optStatus} bind:configuration class="mt-4"/>
{/key}