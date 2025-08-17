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
  // noinspection ES6UnusedImports
  import * as RadioGroup from "@/components/ui/radio-group";
  import {Input} from "$lib/components/ui/input";

  // Icons
  import MdiAlertOutline from '~icons/mdi/alert-outline'

  import type {PageProps} from './$types';
  import {goto, invalidate} from "$app/navigation";
  import {toast} from "svelte-sonner";
  // noinspection ES6UnusedImports
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
  const _file = fileProxy(formData, 'excel') // Needed for proper functioning of zod

  // Excel file handling.
  // We are NOT (and will not) using the above `_file` const because the fileProxy sends an update
  // every time any of the values of the form are updated. This causes annoying flashing of the UI to the user, which
  // is preferable to avoid.
  let excelFile: File | undefined = $state()
  const onExcelChange = (e: Event) => {
    const input = e.target as HTMLInputElement;
    excelFile = input.files?.[0];
  }

  let upload_error = $derived($uploadNewGSMutation.error)
  let submitting = $derived($uploadNewGSMutation.isPending)

  let excelRows = $derived.by(async () => {
    console.debug("Tried to recompute EXCEL file")
    if (!excelFile) return;

    // Parse the workbook
    const data = await excelFile.arrayBuffer();
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
    return rows.map((h) => String(h).trim().toUpperCase())
  })

  let missingColumns = $derived.by(async () => {
    let columns = await excelColumns;
    if (columns.length <= 0) return new Set<string>();
    return data.expectedColumns.difference(new Set<string>(columns));
  })

  let xlsxPreview = $derived.by(async () => {
    // const idxMap = data.expectedColumns.keys().map((c) => (await excelColumns).indexOf(c));
    return (await excelRows)?.slice(1, 11).map(sl => sl.join(", ")) ?? []
  })

  let isMixedGradSession = $derived.by(async () => {
    const rows = await excelRows;
    if (rows === undefined) return new Set<string>(); // Early return to avoid iterating

    let columns = await excelColumns;
    const idx = columns.findIndex(colName => colName === "TIPO_CORSO_DESCRIZIONE");
    if (idx < 0) return new Set<string>(); // We might not find the column.

    const uniqueDegreeTypes = new Set<string>();
    for (let i = 1; (i < rows.length - 1) && uniqueDegreeTypes.size < 2; i++) {
      const colValue = rows[i][idx];
      if (!uniqueDegreeTypes.has(colValue)) {
        uniqueDegreeTypes.add(colValue);
      }
    }

    return uniqueDegreeTypes;
  })
</script>

<Inspect.Values {excelRows} {excelColumns} {missingColumns} {xlsxPreview} {isMixedGradSession}/>

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

    <Form.Field {form} name="excel" class="mt-4">
      <Form.Control>
        {#snippet children({props})}
          <Form.Label>File</Form.Label>
          <Input {...props}
                 required
                 type="file"
                 bind:files={$_file}
                 onchange={onExcelChange}
                 accept={EXCEL_MIME_STRING}
          />
        {/snippet}
      </Form.Control>
      <Form.Description>
        Il file contenente i dati della commissione che dovrà essere ottimizzata.
      </Form.Description>
      <Form.FieldErrors/>
    </Form.Field>

    {#await isMixedGradSession then mixed}
      {@const mixedCount = mixed.size}
      <Form.Fieldset {form} name="only" class="mt-4" disabled={(mixedCount < 2)}>
        <Form.Legend>Filtraggio dei candidati</Form.Legend>
        <Form.Description>
          {#if mixedCount <= 0}
            Selezione disabilitata, per favore indicare un file valido per l'upload
          {:else if mixedCount === 1}
            {@const test = mixed.values().some(v => v.toLowerCase().includes('magistrale'))}
            La selezione è disabilitata in quanto il file della sessione contiene solo
            <strong>studenti {test ? 'Magistrali' : 'Triennali'}</strong>.
          {:else}
            Dal momento che il file della sessione contiene sia studenti Triennali sia Magistrali, è necessario
            scegliere se si intende caricare tutti gli studenti, o solo quelli che afferiscono a uno dei due livelli di
            laurea.
          {/if}
        </Form.Description>
        <RadioGroup.Root
            bind:value={$formData.only}
            class="flex flex-col space-y-1 ps-2"
            name="only"
        >
          <div class="flex items-center space-x-3 space-y-0">
            <Form.Control>
              {#snippet children({props})}
                <RadioGroup.Item value="both" {...props}/>
                <Form.Label class="font-normal">Studenti Triennali e Magistrali</Form.Label>
              {/snippet}
            </Form.Control>
          </div>
          <div class="flex items-center space-x-3 space-y-0">
            <Form.Control>
              {#snippet children({props})}
                <RadioGroup.Item value="bachelors" {...props}/>
                <Form.Label class="font-normal">Solo Studenti Triennali</Form.Label>
              {/snippet}
            </Form.Control>
          </div>
          <div class="flex items-center space-x-3 space-y-0">
            <Form.Control>
              {#snippet children({props})}
                <RadioGroup.Item value="masters" {...props}/>
                <Form.Label class="font-normal">Solo Studenti Magistrali</Form.Label>
              {/snippet}
            </Form.Control>
          </div>
        </RadioGroup.Root>
        <Form.FieldErrors/>
      </Form.Fieldset>
    {/await}

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