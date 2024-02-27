<script lang="ts">
    import * as Dialog from "$lib/components/ui/dialog";
    import * as Form from "$lib/components/ui/form";
    import {Button} from "$lib/components/ui/button";
    import MdiCalendarPlusOutline from '~icons/mdi/calendar-plus-outline'
    import {type Infer, type SuperForm, superForm, superValidate, type SuperValidated} from "sveltekit-superforms";
    import {zod} from "sveltekit-superforms/adapters";
    import {Input} from "$lib/components/ui/input";
    import {commissionFormSchema} from "../routes/schema";

    let isShown = false;

    function changeDialogState(isOpen: boolean) {
        isShown = isOpen;
    }

    export let data: SuperValidated<Infer<typeof commissionFormSchema>>

    const form = superForm(data, {
        validators: zod(commissionFormSchema)
    });

    const {form: formData, enhance} = form;

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
        <form use:enhance method="post" enctype="multipart/form-data">
            <fieldset disabled>

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
                        <!--                    bind:value={$formData.excel}-->
                        <!--suppress JSValidateTypes -->
                        <Input {...attrs}
                               on:input={(e)=>($formData.excel = e.currentTarget.files?.item(0) ?? null)}
                               type="file"
                               accept="application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/>
                    </Form.Control>
                    <Form.Description>Il file contenente i dati della commissione che dovrà essere ottimizzata
                    </Form.Description>
                    <Form.FieldErrors/>
                </Form.Field>

            </fieldset>
        </form>
        <Dialog.Footer>
            <Button type="submit">Conferma</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>