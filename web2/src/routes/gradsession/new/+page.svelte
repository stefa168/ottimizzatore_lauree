<script lang="ts">
  import {defaults, fileProxy, superForm,} from "sveltekit-superforms";
  import {zod} from "sveltekit-superforms/adapters";
  import {commissionFormSchema, type UploadErrorDetails} from "@/schema/CommissionFormSchema";
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
  import {goto, invalidate} from "$app/navigation";
  import {toast} from "svelte-sonner";

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
          goto(`/gradsession/${s.id}`);
        })
        .catch(() => cancel());
    }
  });
  const {form: formData, enhance} = form;
  const file = fileProxy(formData, 'excel')

  let upload_error = $derived($uploadNewGSMutation.error)
  let submitting = $derived($uploadNewGSMutation.isPending)
</script>

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
        <Alert.Title class="mb-2"><p>Errore</p></Alert.Title>
        <Alert.Description>
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
    <Form.Button>Invia</Form.Button>
  </fieldset>
</form>