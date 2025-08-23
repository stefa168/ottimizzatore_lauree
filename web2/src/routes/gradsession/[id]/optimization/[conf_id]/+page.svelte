<script lang="ts">
  import type {PageProps} from './$types';
  import Inspect from "svelte-inspect-value";
  import {Button} from "@/components/ui/button";
  import * as Collapsible from "$lib/components/ui/collapsible/";

  import MdiCogPlayOutline from '~icons/mdi/cog-play-outline'
  import MdiChevronRight from '~icons/mdi/chevron-right'
  import MdiReminder from '~icons/mdi/reminder'
  import MdiContentDuplicate from '~icons/mdi/content-duplicate'
  import OptimizationConfigurationOptions from "./OptimizationConfigurationOptions.svelte";

  let {data}: PageProps = $props();
  let collapsibleOpen = $state(true);

  let tainted_fields_count = 0

</script>


<Inspect value={data.configuration}/>

<Collapsible.Root bind:open={collapsibleOpen}>
  <div class="flex items-center justify-between">
    <Collapsible.Trigger class="mt-4 mb-4 text-xl flex items-center cursor-pointer">
      <MdiCogPlayOutline class="w-6 h-6 me-2"/>
      <span>Parametri dell'Ottimizzatore</span>
      <MdiChevronRight
          class="w-6 h-6 ms-2 transition-transform duration-200"
          aria-hidden="true"
      />
    </Collapsible.Trigger>
    <!--<div class="transition-all duration-150 ease-in-out {tainted_fields_count > 0 ? 'opacity-100' : 'opacity-0 invisible'}"
         role="group">
      <Button variant="ghost"
              onclick={() => formComponent.reset()}
              disabled={tainted_fields_count === 0}>
        <MdiUndoVariant class="h-4 w-4 me-2"/>
        <span>Annulla le modifiche</span>
      </Button>

      <Button variant="ghost"
              onclick={() => formComponent.submit()}
              disabled={tainted_fields_count === 0}>
        <MdiCloudArrowUp class="h-4 w-4 me-2"/>
        <span>Salva le modifiche</span>
      </Button>
    </div>-->
  </div>

<!--  <div class="transition-all duration-300 ease-in-out overflow-hidden max-w-full">-->
  <Collapsible.Content>
    {#if true /*$optStatus.configurationLocked || $optStatus.solutions.all.length > 0*/}
      <div class="flex items-center mt-2 mb-4 text-[0.8rem] text-yellow-600 group dark:text-yellow-400">
        <MdiReminder class="w-5 h-5"/>
        <!-- todo we are expecting that the optimization doesn't fail, but that could be the case sometimes -->
        <span class="flex items-center justify-start ms-2">
          {#if false /*$optStatus.solutions.all.length > 0*/}
              La configurazione è già stata usata per trovare una soluzione.
          {:else}
              La configurazione è stata inviata per l'ottimizzazione.
          {/if}
          Non è possibile modificarla.
          Puoi sempre
          <button class="flex ms-[2px] hover:underline">
              <!--todo-->
              <MdiContentDuplicate class="h-4 w-4 me-[2px]"/> duplicarla
          </button>
          .
        </span>
      </div>
    {/if}
    <OptimizationConfigurationOptions/>
<!--      <ConfigurationForm
          {optStatus}
          selectedConfiguration={selectedConfiguration}
          bind:this={formComponent}
      />-->
  </Collapsible.Content>
</Collapsible.Root>