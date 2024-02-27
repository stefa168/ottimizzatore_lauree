<script lang="ts">
    // noinspection ES6UnusedImports
    import * as Dialog from "$lib/components/ui/dialog";
    // noinspection ES6UnusedImports
    import * as Form from "$lib/components/ui/form";
    // noinspection ES6UnusedImports
    import * as Alert from "$lib/components/ui/alert"
    import {Button} from "$lib/components/ui/button";
    import MdiCalendarPlusOutline from '~icons/mdi/calendar-plus-outline'
    import MdiAlertOutline from '~icons/mdi/alert-outline'
    import {defaults, superForm,} from "sveltekit-superforms";
    import {zod} from "sveltekit-superforms/adapters";
    import {Input} from "$lib/components/ui/input";
    import {commissionFormSchema} from "../routes/schema";
    import {createEventDispatcher} from "svelte";

    interface UploadErrorResponse {
        error: string;
        details?: string;
        missing_columns?: string[];
    }

    const dispatch = createEventDispatcher();

    const form = superForm(defaults(zod(commissionFormSchema)), {
        // With this setting we don't depend on a SvelteKit backend for posting or validating.
        // https://superforms.rocks/concepts/events#event-flowchart
        SPA: true,
        validationMethod: "oninput",
        validators: zod(commissionFormSchema),
        // https://superforms.rocks/concepts/events#onupdate
        async onUpdate({form, cancel}) {
            submitting = true;
            if (form.valid) {
                let data = new FormData();
                // The not null check should never happen: we have a LOT of checks in place before arriving here.
                // See: schema.ts
                data.append('file', form.data.excel!);
                data.append('title', form.data.title);

                // submit_commission(form.data.title, form.data.excel);
                await fetch('http://localhost:5000/upload', {
                    method: 'POST',
                    body: data
                }).then(async (response) => {
                    if (response.ok) {
                        // Return a promise that resolves with the parsed JSON body
                        let json = await response.json();
                        dispatch('commission-created', json);
                        changeDialogState(false);
                    } else {
                        // Return a promise that rejects with the parsed JSON body
                        let json1 = await response.json();
                        return Promise.reject(json1);
                    }
                }).catch((error: UploadErrorResponse) => {
                    upload_error = error;
                    cancel();
                }).finally(() => {
                    submitting = false;
                });
            }
        },
    });
    const {form: formData, enhance} = form;

    // Dialog activation features
    let isShown = false;

    function changeDialogState(isOpen: boolean) {
        isShown = isOpen;
        if (!isOpen) {
            form.reset();
            upload_error = undefined;
            submitting = false;
        }
    }

    let upload_error: UploadErrorResponse | undefined = undefined;
    let submitting = false;

</script>

<Button on:click={() => changeDialogState(true)}
        variant="ghost"
        class="px-3 w-full justify-start">
    <MdiCalendarPlusOutline class="me-2 h-4 w-4"/>
    Nuovo Problema
</Button>

<Dialog.Root
        open={isShown}
        onOpenChange={changeDialogState}
        preventScroll={true}
        closeOnOutsideClick={false}
        closeOnEscape={false}>
    <Dialog.Content>
        <Dialog.Header>
            <Dialog.Title>
                Nuova Commissione
            </Dialog.Title>
            <Dialog.Description>
                <p>Indica qui di seguito i dettagli della commissione di laurea, e carica il file excel
                    contenente i candidati.</p>
            </Dialog.Description>
        </Dialog.Header>
        <form id="new-commission-form"
              method="post"
              enctype="multipart/form-data"
              use:enhance>
            <fieldset disabled={submitting}>
                {#if upload_error}
                    <Alert.Root variant='destructive' class="mb-4">
                        <MdiAlertOutline class="me-2 h-4 w-4"/>
                        <Alert.Title><p>Errore</p></Alert.Title>
                        <Alert.Description>
                            {#if upload_error.details}
                                <p>Dettagli:</p>
                                <p>{upload_error.details}</p>
                            {/if}
                            {#if upload_error.missing_columns}
                                <p>Le seguenti colonne sono mancanti nel file excel:</p>
                                <ul class="list-disc ms-4">
                                    {#each upload_error.missing_columns as column}
                                        <li>{column}</li>
                                    {/each}
                                </ul>
                            {/if}
                        </Alert.Description>
                    </Alert.Root>
                {/if}
                <Form.Field {form} name="title">
                    <Form.Control let:attrs>
                        <Form.Label>Titolo</Form.Label>
                        <Input {...attrs} bind:value={$formData.title}/>
                    </Form.Control>
                    <Form.Description>Il nome che vuoi assegnare alla commissione.</Form.Description>
                    <Form.FieldErrors/>
                </Form.Field>
                <Form.Field {form} name="excel">
                    <Form.Control let:attrs>
                        <Form.Label>File</Form.Label>
                        <Input {...attrs}
                               on:input={(e)=>($formData.excel = e.currentTarget.files?.item(0) ?? null)}
                               type="file"
                               accept="application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/>
                    </Form.Control>
                    <Form.Description>Il file contenente i dati della commissione che dovrà essere ottimizzata.
                    </Form.Description>
                    <Form.FieldErrors/>
                </Form.Field>

            </fieldset>
        </form>
        <Dialog.Footer>
            <Button type="submit"
                    form="new-commission-form">
                Invia
            </Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>