<script lang="ts">
  // noinspection ES6UnusedImports
  import * as Form from "$lib/components/ui/form";
  // noinspection ES6UnusedImports
  import * as Select from "$lib/components/ui/select";
  // noinspection ES6UnusedImports
  import * as Alert from "$lib/components/ui/alert";
  // noinspection ES6UnusedImports
  import * as Collapsible from "$lib/components/ui/collapsible/";
  import {Separator} from "@/components/ui/separator";
  import {Input} from "@/components/ui/input";
  import {Button} from "@/components/ui/button";
  import IcBaselineErrorOutline from '~icons/ic/baseline-error-outline'
  import MdiCogPlayOutline from '~icons/mdi/cog-play-outline'
  import MdiChevronRight from '~icons/mdi/chevron-right'
  import MdiReminder from '~icons/mdi/reminder'
  import MdiContentDuplicate from '~icons/mdi/content-duplicate'
  import MdiUndoVariant from '~icons/mdi/undo-variant'
  import MdiCloudArrowUpOutline from '~icons/mdi/cloud-arrow-up-outline'

  import {zod} from "sveltekit-superforms/adapters";
  import {defaults, superForm} from "sveltekit-superforms";
  import {
    OptConfFormSchema,
    type OptimizationConfiguration, OptimizationConfigurationApi, SolverType
  } from "@/api/OptimizationConfigurationApi";
  import {enumKeys} from "@/utils";
  import {browser} from "$app/environment";
  import {debugEnabled} from "@/store.svelte";
  import Inspect from "svelte-inspect-value";
  import type {ApiErrorResponse} from "@/types";
  import {toast} from "svelte-sonner";
  import type {ClassValue} from "clsx";

  interface Props {
    configuration: OptimizationConfiguration,
    class?: ClassValue
  }

  let {configuration = $bindable(), class: className}: Props = $props();

  let updatePromise = $state<Promise<OptimizationConfiguration> | null>(null)
  let errorMessage = $state<ApiErrorResponse | null>(null);

  const form = superForm(defaults(OptConfFormSchema.parse(configuration), zod(OptConfFormSchema)), {
    SPA: true,
    validationMethod: "oninput",
    validators: zod(OptConfFormSchema),
    taintedMessage: "La configurazione è stata modificata. Confermi di voler perdere le modifiche non salvate?",
    autoFocusOnError: true,
    async onUpdate({form, cancel}) {
      if (updatePromise || !form.valid) return;

      updatePromise = OptimizationConfigurationApi(fetch).updateConfiguration(configuration.session_id, configuration.id, form.data);
      try {
        configuration = await updatePromise;
      } catch (e: unknown) {
        console.log(e);
        errorMessage = e as ApiErrorResponse;
        toast.error(`Si è verificato un errore durante il salvataggio della configurazione (${errorMessage.status_code})\n${errorMessage.detail}`);
        cancel();
      } finally {
        updatePromise = null;
      }
    }
  });
  const {form: formData, enhance, validateForm, tainted} = form;

  export const submitForm = () => form.submit();
  export const resetForm = () => {
    errorMessage = null;
    form.reset();
  }
  export const isValid = async () => await validateForm({focusOnError: true}).then(v => v.valid)
  const taintedFieldCount = $derived($tainted ? Object.keys($tainted).length : 0);

  let collapsibleOpen = $state(true);
</script>

<Collapsible.Root
    class={[
      "bg-card text-card-foreground flex flex-col gap-4 rounded-lg border p-4 shadow-sm",
      className
    ]}
    bind:open={collapsibleOpen}
>
  <div class="flex items-center justify-between">
    <Collapsible.Trigger class="text-xl flex items-center cursor-pointer">
      <MdiCogPlayOutline class="w-6 h-6 me-2"/>
      <span>Parametri dell'Ottimizzatore</span>
      <MdiChevronRight
          class={[
            "w-6 h-6 ms-2 transition-transform duration-200",
            collapsibleOpen ? 'rotate-90' : ''
          ]}
          aria-hidden="true"
      />
    </Collapsible.Trigger>
    <div class={[
        "transition-all duration-150 ease-in-out",
        collapsibleOpen ? 'opacity-100' : 'opacity-0 invisible'
      ]}
         role="group">
      <Button variant="ghost"
              class="hover:cursor-pointer"
              onclick={resetForm}
              disabled={taintedFieldCount <= 0}>
        <MdiUndoVariant class="h-4 w-4 me-2"/>
        <span>Annulla le modifiche</span>
      </Button>

      <Button variant="ghost"
              class="hover:cursor-pointer"
              onclick={submitForm}
              disabled={taintedFieldCount <= 0}>
        <MdiCloudArrowUpOutline class="h-4 w-4 me-2"/>
        <span>Salva le modifiche</span>
      </Button>
    </div>
  </div>

  {#if true /*$optStatus.configurationLocked || $optStatus.solutions.all.length > 0*/}
    <div class="flex items-center mb-4 text-[0.8rem] text-yellow-600 group dark:text-yellow-400">
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
          <button class="flex ms-[2px] hover:underline hover:cursor-pointer">
              <!--todo-->
              <MdiContentDuplicate class="h-4 w-4 me-[2px]"/> duplicarla
          </button>
          .
        </span>
    </div>
  {/if}

  <Collapsible.Content>
    {#if errorMessage}
      <Alert.Root class="mb-4 w-full" variant="destructive">
        <IcBaselineErrorOutline class="w-4 h-4"/>
        <Alert.Title>Il server ha restituito un messaggio di errore ({errorMessage.status_code})</Alert.Title>
        <Alert.Description>
          <p class="font-mono">{errorMessage.detail}</p>
        </Alert.Description>
      </Alert.Root>
    {/if}

    <form method="post"
          enctype="multipart/form-data"
          use:enhance
    >
      <fieldset
          disabled={(updatePromise !== null)}
          class="flex flex-col gap-4"
      >
        <!-- General optimization configuration attributes -->
        <div>
          <h3 class="text-lg font-medium">Impostazioni Generali</h3>
          <Separator decorative={true} class="mt-2 mb-4"/>

          <Form.Field {form} name="title" class="mb-4">
            <Form.Control>
              {#snippet children({props})}
                <Form.Label>Titolo</Form.Label>
                <Input {...props} bind:value={$formData.title}/>
              {/snippet}
            </Form.Control>
            <Form.Description>Un titolo utile per distinguere questa configurazione</Form.Description>
            <Form.FieldErrors/>
          </Form.Field>

          <Form.Field {form} name="max_duration">
            <Form.Control>
              {#snippet children({props})}
                <Form.Label>Durata massima</Form.Label>
                <Input {...props} bind:value={$formData.max_duration}/>
              {/snippet}
            </Form.Control>
            <Form.Description>La durata massima della singola commissione (in minuti)</Form.Description>
            <Form.FieldErrors/>
          </Form.Field>
        </div>

        <div>
          <h3 class="text-lg font-medium">Vincoli di composizione delle Commissioni</h3>
          <Separator decorative={true} class="mt-2 mb-4"/>

          <div class="grid grid-cols-2 gap-4 mt-4">
            <Form.Field {form} name="min_professor_number">
              <Form.Control>
                {#snippet children({props})}
                  <Form.Label>Numero minimo di professori</Form.Label>
                  <Input type="number" {...props} bind:value={$formData.min_professor_number}/>
                {/snippet}
              </Form.Control>
              <Form.Description>
                Il numero minimo di professori necessari per una commissione
              </Form.Description>
              <Form.FieldErrors/>
            </Form.Field>

            <Form.Field {form} name="max_professor_number">
              <Form.Control>
                {#snippet children({props})}
                  <Form.Label>Numero massimo di professori</Form.Label>
                  <Input type="number" {...props} bind:value={$formData.max_professor_number}/>
                {/snippet}
              </Form.Control>
              <Form.Description>
                Il numero massimo di professori necessari per una commissione
              </Form.Description>
              <Form.FieldErrors/>
            </Form.Field>
          </div>

          <Form.Field {form} name="min_professor_number_masters">
            <Form.Control>
              {#snippet children({props})}
                <Form.Label>Numero minimo di professori per il corso di laurea magistrale
                </Form.Label>
                <Input type="number" {...props} bind:value={$formData.min_professor_number_masters}/>
              {/snippet}
            </Form.Control>
            <Form.Description>
              Il numero minimo di professori necessari per una commissione magistrale
            </Form.Description>
            <Form.FieldErrors/>
          </Form.Field>
        </div>

        <div>
          <h3 class="text-lg font-medium">Configurazione dell'Ottimizzatore</h3>
          <Separator decorative={true} class="mt-2 mb-4"/>
          <Form.Field {form} name="solver">
            <Form.Control>
              {#snippet children({props})}
                <Form.Label>Solver</Form.Label>
                <Select.Root type="single" bind:value={$formData.solver} name={props.name}>
                  <Select.Trigger {...props}>
                    {$formData.solver}
                  </Select.Trigger>
                  <Select.Content>
                    {#each enumKeys(SolverType) as solverItem}
                      <Select.Item value={solverItem} label={solverItem} disabled={(solverItem !== SolverType.CPLEX)}/>
                    {/each}
                  </Select.Content>
                </Select.Root>
              {/snippet}
            </Form.Control>
            <Form.Description>Il solver da utilizzare per l'ottimizzazione</Form.Description>
            <Form.FieldErrors/>
          </Form.Field>

          <div class="grid grid-cols-2 gap-4 mt-4">
            <Form.Field {form} name="optimization_time_limit">
              <Form.Control>
                {#snippet children({props})}
                  <Form.Label>Limite di tempo per l'ottimizzazione</Form.Label>
                  <Input type="number" {...props} bind:value={$formData.optimization_time_limit}/>
                {/snippet}
              </Form.Control>
              <Form.Description>Il limite di tempo massimo per l'ottimizzazione (in secondi)
              </Form.Description>
              <Form.FieldErrors/>
            </Form.Field>

            <Form.Field {form} name="optimization_gap">
              <Form.Control>
                {#snippet children({props})}
                  <Form.Label>Gap di ottimizzazione</Form.Label>
                  <Input {...props} bind:value={$formData.optimization_gap}/>
                {/snippet}
              </Form.Control>
              <Form.Description>Il gap di ottimizzazione massimo accettabile</Form.Description>
              <Form.FieldErrors/>
            </Form.Field>
          </div>
        </div>

        {#if browser && $debugEnabled}
          <Inspect value={$formData} expandLevel={0} name="Form Data"/>
        {/if}
      </fieldset>
    </form>

  </Collapsible.Content>
</Collapsible.Root>