<script lang="ts">
  import {DateTime} from "luxon";
  import {computeTimeDifference} from "@/utils.js";
  import type {OptimizationStatus} from "@/types";
  import type {OptimizationConfiguration} from "@/api/OptimizationConfigurationApi";
  import type {SessionData} from "../../../SessionData.svelte";

  // Components
  // noinspection ES6UnusedImports
  import * as Collapsible from "$lib/components/ui/collapsible/";
  // noinspection ES6UnusedImports
  import * as Alert from "$lib/components/ui/alert/";
  import {Button} from "@/components/ui/button/";
  import Inspect from "svelte-inspect-value";
  import CommissionCard from "./CommissionCard.svelte";

  // Icons
  import MdiChevronRight from '~icons/mdi/chevron-right'
  import MdiData from '~icons/mdi/data'
  import MdiCheckDecagram from '~icons/mdi/check-decagram'
  import MdiAlertDecagramOutline from '~icons/mdi/alert-decagram-outline'
  import MdiLoading from "~icons/mdi/loading";
  import MdiExclamation from '~icons/mdi/exclamation'
  import MdiCubeSend from '~icons/mdi/cube-send'
  import MdiFlagCheckered from '~icons/mdi/flag-checkered'
  import MdiFlagVariantOffOutline from '~icons/mdi/flag-variant-off-outline'
  import MdiAlertOctagramOutline from '~icons/mdi/alert-octagram-outline'
  import MdiAlarm from '~icons/mdi/alarm'
  import MdiTimerOutline from '~icons/mdi/timer-outline'

  interface Props {
    optStatus: OptimizationStatus;
    configuration: OptimizationConfiguration;
    sessionData: SessionData
  }

  let {optStatus, configuration, sessionData}: Props = $props();

  let collapsibleOpen = $state(true);
  let log = $derived(configuration.optimization_log);
</script>

<Collapsible.Root
    class="bg-card text-card-foreground flex flex-col gap-4 rounded-lg border p-4 shadow-sm"
    bind:open={collapsibleOpen}
>
  <div class="flex items-center justify-between">
    <Collapsible.Trigger class="text-xl flex items-center cursor-pointer">
      {#if optStatus.ended}
        <MdiCheckDecagram class="w-6 h-6 me-2 text-green-600"/>
      {:else if optStatus.status === 'failure'}
        <MdiAlertDecagramOutline class="w-6 h-6 me-2 text-destructive"/>
      {:else}
        <MdiData class="w-6 h-6 me-2"/>
      {/if}

      <span>
        Risultati dell'Ottimizzazione
        {#if log}
          <span class="text-muted-foreground">
            (avviata il {DateTime.fromJSDate(log.start_time).toFormat("d MMMM yy 'alle' HH:mm", {locale: 'it'})})
          </span>
        {/if}
      </span>
      <MdiChevronRight
          class={["w-6 h-6 ms-2 transition-transform duration-200", collapsibleOpen && 'rotate-90']}
          aria-hidden="true"
      />
    </Collapsible.Trigger>
    {#if optStatus.running}
      <div class="flex items-center justify-center">
        <MdiLoading class="w-6 h-6 ms-4 animate-spin" style="animation-duration: 2s"/>
        <span class="ms-2">Ottimizzazione in corso</span>
      </div>
    {/if}
  </div>
  <Collapsible.Content>
    {#if optStatus.ended && log}
      {@const commissions = optStatus.commissions}
      <h3 class="border-b mb-4 pe-2 pb-1 pt-2">Dettagli dell'esecuzione</h3>
      <div>
        <ul class="ps-2 flex flex-col gap-y-1.5">
          <li class="flex items-center">
            {#if log.solver_reached_optimality}
              <MdiFlagCheckered class="w-6 h-6 me-1"/>
            {:else}
              <MdiFlagVariantOffOutline class="w-6 h-6 me-1"/>
            {/if}
            <span>
              L'ottimizzatore
              <strong class={['font-bold', log.solver_reached_optimality ? 'text-green-600' : 'text-destructive']}>
                 {log.solver_reached_optimality ? '' : 'non'} ha trovato
              </strong>
              una soluzione ottimale.
            </span>
          </li>
          <li class="flex items-center">
            <MdiAlarm class="w-6 h-6 me-1"/>
            <span>
              L'ottimizzazione è terminata
              <span class={['font-bold', log.solver_reached_optimality ? 'text-green-600' : 'text-destructive']}>
                {!configuration.solver_reached_time_limit ? 'prima' : 'col raggiungimento'}
                del tempo limite di esecuzione
              </span>
              .
            </span>
          </li>
          <li class="flex items-center">
            <MdiTimerOutline class="w-6 h-6 me-1"/>
            <span>
              L'elaborazione ha richiesto <strong>{computeTimeDifference(log.start_time, log.end_time)}</strong>.
            </span>
          </li>
          {#if log.error_message}
            <li class="flex items-center">
              <MdiAlertOctagramOutline class="size-6 text-destructive me-1"/>
              Errore: {log.error_message}.
            </li>
          {/if}
          <li>
            <Inspect
                class="my-inspect-theme"
                value={configuration.optimization_log?.log}
                expandLevel={0}
                heading="Log dell'ottimizzatore"
                search="filter"
                theme=""
                borderless={true}
                showTypes={false}
                noanimate={true}
            />
          </li>
        </ul>
      </div>

      {#if commissions.morning.length > 0}
        <h3 class="border-b mb-4 pe-2 pb-1 pt-2">Commissioni Mattutine</h3>
        <div class="flex flex-wrap justify-center gap-y-4 gap-x-6 pb-2">
          {#each commissions.morning as commission}
            <CommissionCard {commission} {sessionData}/>
          {/each}
        </div>
      {/if}

      {#if optStatus.commissions.afternoon.length > 0}
        <h3 class="border-b mb-4 pe-2 pb-1 pt-2">Commissioni Pomeridiane</h3>
        <div class="flex flex-wrap justify-center gap-y-4 gap-x-6 pb-2">
          {#each commissions.afternoon as commission}
            <CommissionCard {commission} {sessionData}/>
          {/each}
        </div>
      {/if}
    {:else}
      {#if log?.error_message}
        <Alert.Root variant="destructive">
          <Alert.Title>Attenzione</Alert.Title>
          <Alert.Description>{log.error_message}</Alert.Description>
        </Alert.Root>
      {/if}
      <!-- We still have to start the optimization -->
      <div class="flex items-center flex-col">
        <div class="flex items-center self-center mt-4">
          <MdiExclamation class="w-8 h-8"/>
          <span>Ottimizzazione non ancora avviata</span>
        </div>
        <Button class="mt-2">
          <MdiCubeSend class="h-4 w-4 me-2"/>
          <span>Avvia l'ottimizzazione</span>
        </Button>
      </div>
    {/if}

  </Collapsible.Content>
</Collapsible.Root>

<style>
  .my-inspect-theme {
    --base00: #000000;
    --base01: #000000;
    --base02: #000000;
    --base03: #000000;
    --base04: #000000;
    --base05: #000000;
    --base06: #000000;
    --base07: #000000;
    --base08: #000000;
    --base09: #000000;
    --base0A: #000000;
    --base0B: #000000;
    --base0C: #000000;
    --base0D: #000000;
    --base0E: #000000;
    --base0F: #000000;
  }
</style>