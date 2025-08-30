<script lang="ts">
  import {DateTime} from "luxon";
  import {computeTimeDifference, optimizationTaskStatusFactory} from "@/utils.js";
  import type {ApiErrorResponse, OptimizationStatus} from "@/types";
  import {type OptimizationConfiguration, OptimizationConfigurationApi} from "@/api/OptimizationConfigurationApi";
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
  import IcBaselineErrorOutline from '~icons/ic/baseline-error-outline'
  import {onDestroy, onMount} from "svelte";
  import {pollUntil} from "@/pollingUtility";

  interface Props {
    optStatus: OptimizationStatus;
    configuration: OptimizationConfiguration;
    sessionData: SessionData;
    optimizationStartCallback?: () => Promise<void>,
    optimizationStartPreflight?: () => Promise<boolean>
  }

  let {
    optStatus,
    configuration = $bindable(),
    sessionData,
    optimizationStartCallback,
    optimizationStartPreflight = () => true
  }: Props = $props();

  let collapsibleOpen = $state(true);
  let log = $derived(configuration.optimization_log);
  const abortController = new AbortController();
  let pollingPromise: Promise<void> | null = $state(null);
  let errorMessage: ApiErrorResponse | undefined = $state(undefined);

  const safeStartOptimization = async () => {
    if (await optimizationStartPreflight())
      await startOptimization();
    else
      alert("Attualmente ci sono delle modifiche non salvate nella configurazione. Per continuare, salvarle o annullarle");
  }

  const startOptimization = async () => {
    try {
      await OptimizationConfigurationApi(fetch).startOptimization(sessionData.session.id, configuration.id)
    } catch (e) {
      errorMessage = e as ApiErrorResponse;
      throw e
    }
    optimizationStartCallback?.();
    configuration = {...configuration, run_lock: true}; // Needed to actually trigger reactivity!
    await pollForOptimizationEnd();
  }

  // Can be called in the `onMount` lifecycle hook, or by the `startOptimization` function. Will throw if called twice.
  async function pollForOptimizationEnd() {
    if (pollingPromise) throw new Error("Should not call the polling twice");

    const p = pollUntil(
      async (signal) => OptimizationConfigurationApi(fetch).getComplete(sessionData.session.id, configuration.id, {signal}), {
        signal: abortController.signal,
        retries: Number.POSITIVE_INFINITY,
        isDone(result) {
          let status = optimizationTaskStatusFactory(result);
          console.debug(JSON.stringify(status));
          return ['ended', 'failed'].includes(status.status);
        }
      }
    ).catch(e => console.warn(e)) // Just to silence the error thrown
      .then(r => {
        configuration = r!

      })
      .finally(() => pollingPromise = null);

    pollingPromise = p;
    return await p;
  }

  onMount(async () => {
    if (optStatus.running) {
      await pollForOptimizationEnd();
    }
  });

  onDestroy(() => {
    abortController.abort();
  })
</script>

<Collapsible.Root
    class="bg-card text-card-foreground flex flex-col gap-4 rounded-lg border p-4 shadow-sm"
    bind:open={collapsibleOpen}
>
  <div class="flex items-center justify-between">
    <Collapsible.Trigger class="text-xl flex items-center enabled:cursor-pointer" disabled={(!optStatus.started)}>
      {#if optStatus.success}
        {@const absoluteWin = log && !log.solver_time_limit_reached && log.solver_reached_optimality }
        <MdiCheckDecagram class={["w-6 h-6 me-2", absoluteWin ? 'text-green-600' : 'text-amber-500']}/>
      {:else if optStatus.failed}
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
          class={[
            "w-6 h-6 ms-2 transition-transform duration-200",
            collapsibleOpen && 'rotate-90',
            optStatus.ended || optStatus.failed ? 'visible' : 'invisible'
          ]}
          aria-hidden="true"
      />
    </Collapsible.Trigger>
    {#if optStatus.running}
      <div class="flex items-center justify-center">
        <MdiLoading class="w-6 h-6 ms-4 animate-spin" style="animation-duration: 2s"/>
        <span class="ms-2">Ottimizzazione in corso</span>
      </div>
    {:else if !optStatus.started}
      <div class="flex items-center justify-center">
        <MdiExclamation class="w-6 h-6 ms-4"/>
        <span>Ottimizzazione non ancora avviata</span>
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
              <span class={['font-bold', !log.solver_time_limit_reached ? 'text-green-600' : 'text-destructive']}>
                {!log.solver_time_limit_reached ? 'prima' : 'col raggiungimento'}
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
                quotes="none"
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

      {#if errorMessage}
        <Alert.Root class="mb-4 w-full" variant="destructive">
          <IcBaselineErrorOutline class="w-4 h-4"/>
          <Alert.Title>Il server ha restituito un messaggio di errore ({errorMessage.status_code})</Alert.Title>
          <Alert.Description>
            <p class="font-mono">{errorMessage.detail}</p>
          </Alert.Description>
        </Alert.Root>
      {/if}

      <!-- We still have to start the optimization -->
      {#if !optStatus.started}
        <div class="flex items-center flex-col">
          <Button class="hover:cursor-pointer" onclick={safeStartOptimization}>
            <MdiCubeSend class="h-4 w-4 me-2"/>
            <span>Avvia l'ottimizzazione</span>
          </Button>
        </div>
      {/if}
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