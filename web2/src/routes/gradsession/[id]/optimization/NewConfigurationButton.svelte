<script lang="ts">
  import {buttonVariants} from "@/components/ui/button/index.js";
  import SuspenseButton from "@/components/suspense/SuspenseButton.svelte";
  import MdiFilePlus from '~icons/mdi/file-plus'
  import MdiLoading from "~icons/mdi/loading";
  import {OptimizationConfigurationApi} from "@/api/OptimizationConfigurationApi.js";
  import {goto} from "$app/navigation";

  interface Props {
    session_id: number;
  }

  const {session_id}: Props = $props();

  const onclick = async () => {
    const newConfig = await OptimizationConfigurationApi(fetch).newOptConf(session_id)
    const basePath = location.pathname.endsWith('/') ? location.pathname.slice(0, -1) : location.pathname;
    await goto(`${basePath}/${newConfig.id}`)
  }
</script>

<SuspenseButton class={[buttonVariants({variant: "ghost"}), 'hover:cursor-pointer']} {onclick}>
  {#snippet children({loading})}
    {#if loading}
      <MdiLoading class="w-6 h-6 ms-4 animate-spin"/>
      Creazione...
    {:else}
      <MdiFilePlus class="size-4"/>
      Nuova Configurazione
    {/if}
  {/snippet}
</SuspenseButton>