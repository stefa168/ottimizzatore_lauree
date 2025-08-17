<script lang="ts">
  import {defaults, fileProxy, superForm,} from "sveltekit-superforms";
  import {zod} from "sveltekit-superforms/adapters";
  import * as XLSX from 'xlsx';
  import {commissionFormSchema} from "@/schema/CommissionFormSchema";
  import {useQueryClient} from "@tanstack/svelte-query";
  import {GradSessionApiQueries} from "@/api/GradSesssionApi";

  import {EXCEL_MIME_STRING} from "@/const";

  // Shadcn components
  // noinspection ES6UnusedImports
  import * as Dialog from "@/components/ui/dialog";
  // noinspection ES6UnusedImports
  import * as Form from "@/components/ui/form";
  // noinspection ES6UnusedImports
  import * as Alert from "@/components/ui/alert"
  import {Input} from "$lib/components/ui/input";

  // Icons
  import MdiAlertOutline from '~icons/mdi/alert-outline'

  import type {PageProps} from './$types';
  import {goto, invalidate} from "$app/navigation";
  import {toast} from "svelte-sonner";
  import Inspect from "svelte-inspect-value";

  let {data}: PageProps = $props();

  // TSQ
  const queryClient = useQueryClient();
  const gradSessionApiQueries = GradSessionApiQueries(queryClient);

  const uploadNewGSMutation = gradSessionApiQueries.uploadSessionMutation();

  const form = superForm(defaults(zod(commissionFormSchema)), {
    // With this setting we don't depend on a SvelteKit backend for posting or validating.
    // https://superforms.rocks/concepts/events#event-flowchart
    SPA: true,
    validationMethod: "oninput",
    validators: zod(commissionFormSchema),
    // https://superforms.rocks/concepts/events#onupdate
    onUpdate: async function ({form, cancel}) {
      if (!form.valid) {
        cancel();
        return;
      }

      await $uploadNewGSMutation.mutateAsync(form.data)
        .then(s => {
          invalidate((url) => url.href.includes("sessions"));
          toast.success("Commissione creata con successo! Apertura in corso...");
          return s
        })
        .then((s) => goto(`/gradsession/${s.id}`))
        .catch(() => cancel());
    }
  });
  const {form: formData, enhance} = form;
  const file = fileProxy(formData, 'excel')

  let upload_error = $derived($uploadNewGSMutation.error)
  let submitting = $derived($uploadNewGSMutation.isPending)

  let excelRows = $derived.by(async () => {
    const f = $file[0];
    if (!f) return;

    // Parse the workbook
    const data = await f.arrayBuffer();
    const wb = XLSX.read(data, {type: 'array'});

    // Use the first sheet
    const sheetName = wb.SheetNames[0];
    const ws = wb.Sheets[sheetName];

    return XLSX.utils.sheet_to_json(ws, {
      header: 1,   // returns array-of-arrays
      defval: ''   // keep empty cells as ''
    }) as string[][];

  });

  let excelColumns = $derived.by(async () => {
    let rows = (await excelRows)?.[0] ?? [];
    return new Set((rows.map((h) => String(h).trim().toUpperCase())))
  })

  let missingColumns = $derived.by(async () => {
    let columns = await excelColumns;
    if (columns.size <= 0) return new Set<string>();
    return data.expectedColumns.difference(columns);
  })

  let xlsxPreview = $derived.by(async () => {
    // const idxMap = data.expectedColumns.keys().map((c) => (await excelColumns).indexOf(c));
    return (await excelRows)?.slice(1, 11).map(sl => sl.join(", ")) ?? []
  })
</script>

<Inspect.Values {excelRows} {excelColumns} {missingColumns} {xlsxPreview}/>

<div class="border-b-2 mb-6">
  <h2 class="text-3xl mt-4 mb-1"> Nuova Sessione di Laurea </h2>
  <p class="mb-2">Indica qui di seguito i dettagli della commissione di laurea, e carica il file excel contenente i
    candidati.</p>
</div>

<form id="new-commission-form"
      method="post"
      enctype="multipart/form-data"
      use:enhance>
  <fieldset disabled={submitting}>
    {#if upload_error}
      <Alert.Root variant='destructive' class="mb-4">
        <MdiAlertOutline class="me-2 h-4 w-4"/>
        <Alert.Title class="mb-2"><p>Errore (HTTP {upload_error.status_code})</p></Alert.Title>
        <Alert.Description>
          <p>Il server ha restituito il seguente messaggio di errore:</p>
          <p><code>{upload_error.detail}</code></p>
          {#if upload_error.extra?.details}
            <p class="font-mono text-xs">{upload_error.extra.details}</p>
          {/if}
          {#if upload_error.extra?.missing_columns}
            <p>Le seguenti colonne sono mancanti nel file excel:</p>
            <ul class="list-disc list-inside">
              {#each upload_error.extra?.missing_columns as column}
                <li>{column}</li>
              {/each}
            </ul>
          {/if}
        </Alert.Description>
      </Alert.Root>
    {/if}
    <Form.Field {form} name="title">
      <Form.Control>
        {#snippet children({props})}
          <Form.Label>Titolo</Form.Label>
          <Input {...props} bind:value={$formData.title}/>
        {/snippet}
      </Form.Control>
      <Form.Description>Il nome che vuoi assegnare alla commissione.</Form.Description>
      <Form.FieldErrors/>
    </Form.Field>
    <Form.Field {form} name="excel">
      <Form.Control>
        {#snippet children({props})}
          <Form.Label>File</Form.Label>
          <Input {...props}
                 required
                 type="file"
                 bind:files={$file}
                 accept={EXCEL_MIME_STRING}/>
        {/snippet}
      </Form.Control>
      <Form.Description>Il file contenente i dati della commissione che dovrà essere ottimizzata.
      </Form.Description>
      <Form.FieldErrors/>
    </Form.Field>

    {#await missingColumns}
      <!-- Even though it isn't needed, we're using a copy of the button to avoid flashing and pops caused by the form updating -->
      <Form.Button disabled>Invia</Form.Button>
    {:then missing}
      {#if missing.size > 0}
        <Alert.Root variant='destructive' class="mb-4">
          <MdiAlertOutline class="me-2 h-4 w-4"/>
          <Alert.Title class="mb-2">Attenzione, il file è malformato; mancano le seguenti colonne richieste:
          </Alert.Title>
          <Alert.Description>
            <ul class="list-inside list-disc">
              {#each missing as el}
                <li><code>{el}</code></li>
              {/each}
            </ul>
          </Alert.Description>
        </Alert.Root>
      {/if}

      <Form.Button disabled={(missing.size > 0)}>
        Invia
      </Form.Button>
    {/await}
  </fieldset>
</form>