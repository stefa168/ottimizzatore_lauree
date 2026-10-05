<script lang="ts">
  import {DateTime} from "luxon";
  import {computeTimeDifference, optimizationTaskStatusFactory} from "@/utils.js";
  import type {ApiErrorResponse, OptimizationStatus} from "@/types";
  import type {OptimizationConfiguration} from "@/schema/optimization";
  import {
    setConfigurationFrozen,
    startOptimization as startOptimizationCommand,
    watchConfiguration
  } from "@/api/optimization.remote";
  import {Badge} from "@/components/ui/badge";
  // noinspection ES6UnusedImports
  import * as Dialog from "$lib/components/ui/dialog";
  import {toast} from "svelte-sonner";
  import LucideSnowflake from '~icons/lucide/snowflake'
  import LucideDownload from '~icons/lucide/download'
  import LucideLockOpen from '~icons/lucide/lock-open'
  import LucideLoaderCircle from '~icons/lucide/loader-circle'
  import {toApiError} from "@/errors";
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
  import LucideLogs from '~icons/lucide/logs'
  import LucideChevronRight from '~icons/lucide/chevron-right'

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
    optimizationStartPreflight = async () => true
  }: Props = $props();

  let collapsibleOpen = $state(true);
  let log = $derived(configuration.optimization_log);
  let errorMessage: ApiErrorResponse | undefined = $state(undefined);

  // While the optimization runs, the server streams the configuration until the optimization ends
  let watching = $state(optStatus.running);
  const live = $derived(watching
    ? watchConfiguration({sid: sessionData.session.id, cid: configuration.id})
    : null);

  $effect(() => {
    const latest = live?.current;
    // Only replace the configuration when the status changes, so the page isn't re-rendered every few seconds
    if (latest && optimizationTaskStatusFactory(latest).status !== optStatus.status)
      configuration = latest;
    if (live?.done)
      watching = false;
  });

  // Freezing marks the solution as final: the configuration can't be changed or deleted until it's unfrozen
  let freezeDialogOpen = $state(false);
  let freezing = $state(false);
  const exportUrl = $derived(`/gradsession/${sessionData.session.id}/optimization/${configuration.id}/export`);

  const toggleFrozen = async () => {
    freezing = true;
    const frozen = !configuration.frozen;
    try {
      await setConfigurationFrozen({sid: sessionData.session.id, cid: configuration.id, frozen});
      toast.success(frozen ? "Soluzione congelata: è ora elencata tra le soluzioni finali della sessione." : "Soluzione sbloccata.");
      freezeDialogOpen = false;
    } catch (e) {
      toast.error("Si è verificato un errore", {description: toApiError(e).detail});
    } finally {
      freezing = false;
    }
  };

  const safeStartOptimization = async () => {
    if (await optimizationStartPreflight())
      await startOptimization();
    else
      alert("Attualmente ci sono delle modifiche non salvate nella configurazione. Per continuare, salvarle o annullarle");
  }

  const startOptimization = async () => {
    try {
      await startOptimizationCommand({sid: sessionData.session.id, cid: configuration.id});
    } catch (e) {
      errorMessage = toApiError(e);
      throw e
    }
    optimizationStartCallback?.();
    configuration = {...configuration, run_lock: true}; // Needed to actually trigger reactivity!
    watching = true;
  }
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
            (avviata il {DateTime.fromJSDate(log.start_time).toFormat("d MMMM yyyy 'alle' HH:mm", {locale: 'it'})})
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
    {#if optStatus.success}
      <div class="flex items-center gap-2">
        {#if configuration.frozen}
          <Badge variant="secondary"><LucideSnowflake class="size-3"/> Congelata</Badge>
        {/if}
        <Button variant="outline" size="sm" href={exportUrl} download data-sveltekit-reload>
          <LucideDownload/> Esporta XLS
        </Button>
        <Button variant={configuration.frozen ? "outline" : "default"} size="sm" onclick={() => freezeDialogOpen = true}>
          {#if configuration.frozen}
            <LucideLockOpen/> Sblocca soluzione
          {:else}
            <LucideSnowflake/> Congela soluzione
          {/if}
        </Button>
      </div>
    {:else if optStatus.running}
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

            <Collapsible.Root>
              <Collapsible.Trigger>
                {#snippet child({props})}
                  <Button
                    {...props}
                    variant="ghost"
                    size="sm"
                    class="group w-full justify-start transition-none hover:bg-accent hover:text-accent-foreground"
                  >
                    <LucideLogs/>
                    <LucideChevronRight class="transition-transform group-data-[state=open]:rotate-90" />
                    Apri il log
                  </Button>
                {/snippet}
              </Collapsible.Trigger>
              <Collapsible.Content>
                <table class="font-mono text-sm w-full">
                  <tbody>
                  {#each configuration.optimization_log?.log.split(/\n/g) as line, row }
                    <tr class="hover:bg-amber-200">
                      <td class="text-end pe-1 border-r">{row + 1}</td>
                      <td class="ps-2">
                        <pre class="m-0 inline">{line}</pre>
                      </td>
                    </tr>
                  {/each}
                  </tbody>
                </table>
              </Collapsible.Content>
            </Collapsible.Root>
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

<Dialog.Root bind:open={freezeDialogOpen}>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>{configuration.frozen ? "Sbloccare la soluzione?" : "Congelare la soluzione?"}</Dialog.Title>
      <Dialog.Description>
        {#if configuration.frozen}
          La configurazione tornerà modificabile ed eliminabile, e non sarà più elencata tra le soluzioni finali.
        {:else}
          La soluzione verrà considerata definitiva: sarà elencata tra le soluzioni finali della sessione e la
          configurazione non potrà essere modificata né eliminata finché non verrà sbloccata.
        {/if}
      </Dialog.Description>
    </Dialog.Header>
    <Dialog.Footer>
      <Button variant="outline" onclick={() => freezeDialogOpen = false} disabled={freezing}>Annulla</Button>
      <Button onclick={toggleFrozen} disabled={freezing}>
        {#if freezing}<LucideLoaderCircle class="animate-spin"/>{/if}
        {configuration.frozen ? "Sblocca" : "Congela"}
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
