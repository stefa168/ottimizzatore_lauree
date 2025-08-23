<script lang="ts">
  // noinspection ES6UnusedImports
  import * as Form from "$lib/components/ui/form";
  // noinspection ES6UnusedImports
  import * as Select from "$lib/components/ui/select";
  import {Separator} from "@/components/ui/separator";
  import {Input} from "@/components/ui/input";

  import {zod} from "sveltekit-superforms/adapters";
  import {defaults, superForm} from "sveltekit-superforms";
  import {OptimizationConfigurationSchema, SolverType} from "@/api/OptimizationConfigurationApi";
  import {enumKeys} from "@/utils";
  import {browser} from "$app/environment";
  import {debugEnabled} from "@/store.svelte";
  import Inspect from "svelte-inspect-value";

  const form = superForm(defaults(zod(OptimizationConfigurationSchema)));
  const {form: formData, enhance, validateForm} = form;
</script>

<form method="post"
      enctype="multipart/form-data"
      use:enhance
>
  <!-- General optimization configuration attributes -->
  <div class="rounded-lg border p-4">
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

  <div class="rounded-lg border p-4 mt-4">
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

  <div class="rounded-lg border p-4 mt-4">
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
    <div class="my-4">
      <Inspect value={$formData} name="Form Data"/>
    </div>
  {/if}
</form>