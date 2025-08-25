<script lang="ts">
  import {browser} from "$app/environment";
  import type {PageProps} from './$types';
  import {debugEnabled} from "@/store.svelte";
  import OptimizationConfigurationOptions from "./OptimizationConfigurationOptions.svelte";
  import Inspect from "svelte-inspect-value";

  let {data}: PageProps = $props();
  let configuration = $derived(data.configuration);

  let optConfForm: OptimizationConfigurationOptions | null = $state(null);
</script>

{#if browser && $debugEnabled}
  <Inspect value={data.configuration} expandLevel={0}/>
{/if}

{#key configuration}
  <OptimizationConfigurationOptions bind:this={optConfForm} bind:configuration/>
{/key}