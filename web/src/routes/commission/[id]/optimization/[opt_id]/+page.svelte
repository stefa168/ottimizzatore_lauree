<script lang="ts">
    import {debugEnabled, selectedConfiguration} from "$lib/store";
    import {browser} from "$app/environment";
    import {enumKeys} from "$lib/utils";

    import {Separator} from "$lib/components/ui/separator";
    import {Input} from "$lib/components/ui/input";
    import {Button} from "$lib/components/ui/button";
    import {Switch} from "$lib/components/ui/switch";
    import * as Select from "$lib/components/ui/select";
    import * as Form from "$lib/components/ui/form";
    import * as HoverCard from "$lib/components/ui/hover-card";

    import SuperDebug, {defaults, superForm} from "sveltekit-superforms";
    import {zod} from "sveltekit-superforms/adapters";

    import {SolverType} from "../optimization_types";
    import MdiReminder from '~icons/mdi/reminder'
    import MdiChevronRight from '~icons/mdi/chevron-right'
    import MdiCogPlayOutline from '~icons/mdi/cog-play-outline'
    import MdiUndoVariant from '~icons/mdi/undo-variant'
    import MdiCloudArrowUp from '~icons/mdi/cloud-arrow-up'
    import {optimizationConfigurationSchema} from "./schema";

    const form = superForm(
        defaults($selectedConfiguration, zod(optimizationConfigurationSchema)), {
            SPA: true,
            validationMethod: "oninput",
            validators: zod(optimizationConfigurationSchema)
        }
    )
    const {form: formData, enhance} = form;

    // the right way to use superform/formsnap with bits-ui is this:
    // https://formsnap.dev/docs/recipes/bits-ui-select#setup-the-form
    $: selectedSolver = {
        label: String($formData.solver).toUpperCase(),
        value: $formData.solver
    };

    let settingsOpened = false;
    let tainted = form.tainted;
    let tainted_fields_count = 0;
    tainted.subscribe((value) => {
        if (value === undefined) {
            tainted_fields_count = 0;
        } else {
            // Works OK, however Superforms sets fields to undefined if they are not touched
            tainted_fields_count = Object.keys(value).length;
        }
    });
</script>

{#if $selectedConfiguration}
    <div>
        <div class="flex items-center justify-between">
            <button class="mt-4 mb-4 text-xl flex items-center cursor-pointer"
                    on:click={() => settingsOpened = !settingsOpened}>
                <MdiCogPlayOutline class="w-6 h-6 me-2"/>
                <span>Impostazioni</span>
                <MdiChevronRight
                        class="w-6 h-6 ms-2 transition-transform duration-200 {settingsOpened ? 'rotate-90' : ''}"
                        aria-hidden="true"
                />
            </button>
            <div class="transition-all duration-150 ease-in-out {tainted_fields_count > 0 ? 'opacity-100' : 'opacity-0 invisible'}"
                 role="group">
                <Button variant="ghost"
                        on:click={() => form.reset()}
                        disabled={tainted_fields_count === 0}>
                    <MdiUndoVariant class="h-4 w-4 me-2"/>
                    <span>Annulla le modifiche</span>
                </Button>

                <Button variant="ghost"
                        on:click={() => form.submit()}
                        disabled={tainted_fields_count === 0}>
                    <MdiCloudArrowUp class="h-4 w-4 me-2"/>
                    <span>Salva le modifiche</span>
                </Button>
            </div>
        </div>

        <div class="transition-all duration-300 ease-in-out overflow-hidden max-w-full {settingsOpened ? 'max-h-[20000px]' : 'max-h-0'}">
            <form id="optimizationDetailsEditor"
                  method="post"
                  enctype="multipart/form-data"
                  use:enhance>
                <!-- Todo add feedback sections if errors occur -->
                <div class="rounded-lg border p-4">
                    <h3 class="text-lg">Generali</h3>
                    <Separator decorative={true} class="mt-2 mb-4"/>
                    <Form.Field {form} name="title">
                        <Form.Control let:attrs>
                            <Form.Label>Titolo</Form.Label>
                            <Input {...attrs} bind:value={$formData.title}/>
                        </Form.Control>
                        <Form.Description>Un titolo utile per distinguere questa configurazione</Form.Description>
                        <Form.FieldErrors/>
                    </Form.Field>

                    <Form.Field {form} name="max_duration">
                        <Form.Control let:attrs>
                            <Form.Label>Durata massima</Form.Label>
                            <Input {...attrs} bind:value={$formData.max_duration}/>
                        </Form.Control>
                        <Form.Description>La durata massima della singola commissione (in minuti)</Form.Description>
                        <Form.FieldErrors/>
                    </Form.Field>
                </div>

                <div class="rounded-lg border p-4 mt-4">
                    <h3 class="text-lg">Numero massimo di commissioni</h3>
                    <Separator decorative={true} class="mt-2 mb-4"/>
                    <div class="grid grid-cols-2 gap-4">
                        <Form.Field {form} name="max_commissions_morning">
                            <Form.Control let:attrs>
                                <Form.Label>Di mattina</Form.Label>
                                <Input {...attrs} bind:value={$formData.max_commissions_morning}/>
                            </Form.Control>
                            <Form.Description>
                                Il massimo numero di commissioni che possono essere svolte di mattina
                            </Form.Description>
                            <Form.FieldErrors/>
                        </Form.Field>

                        <Form.Field {form} name="max_commissions_afternoon">
                            <Form.Control let:attrs>
                                <Form.Label>Di pomeriggio</Form.Label>
                                <Input type="number" {...attrs} bind:value={$formData.max_commissions_afternoon}/>
                            </Form.Control>
                            <Form.Description>
                                Il massimo numero di commissioni che possono essere svolte di pomeriggio
                            </Form.Description>
                            <Form.FieldErrors/>
                        </Form.Field>
                    </div>
                </div>

                <div class="rounded-lg border p-4 mt-4">
                    <Form.Field {form} name="online">
                        <Form.Control let:attrs>
                            <div class="flex items-center justify-between">
                                <Form.Label class="text-lg">Commissione online</Form.Label>
                                <Switch {...attrs} bind:checked={$formData.online} class="ms-3 justify-self-end"/>
                            </div>
                        </Form.Control>
                        <Form.Description>
                            Attiva lo switch a destra se le commissioni di laurea saranno svolte online
                        </Form.Description>
                        <!-- Probably not needed -->
                        <!-- <Form.FieldErrors style="margin-top: 0"/>-->
                    </Form.Field>

                    <div class="transition-all duration-300 ease-in-out overflow-hidden max-w-full {$formData.online ? 'max-h-screen' : 'max-h-0'}">
                        <Separator decorative={true} class="mt-2 mb-4"/>
                        <div class="flex items-center mt-2 text-[0.8rem] text-yellow-600 group dark:text-yellow-400">
                            <MdiReminder class="w-5 h-5"/>
                            <span class="justify-start ms-2"> Se le commissioni saranno svolte online, è necessario specificare il numero minimo e massimo di professori necessari</span>
                        </div>

                        <div class="grid grid-cols-2 gap-4 mt-4">
                            <Form.Field {form} name="min_professor_number">
                                <Form.Control let:attrs>
                                    <Form.Label>Numero minimo di professori</Form.Label>
                                    <Input {...attrs} bind:value={$formData.min_professor_number}/>
                                </Form.Control>
                                <Form.Description>
                                    Il numero minimo di professori necessari per una commissione
                                </Form.Description>
                                <Form.FieldErrors/>
                            </Form.Field>

                            <Form.Field {form} name="max_professor_number">
                                <Form.Control let:attrs>
                                    <Form.Label>Numero massimo di professori</Form.Label>
                                    <Input {...attrs} bind:value={$formData.max_professor_number}/>
                                </Form.Control>
                                <Form.Description>
                                    Il numero massimo di professori necessari per una commissione
                                </Form.Description>
                                <Form.FieldErrors/>
                            </Form.Field>
                        </div>

                        <Form.Field {form} name="min_professor_number_masters">
                            <Form.Control let:attrs>
                                <Form.Label>Numero minimo di professori per il corso di laurea magistrale</Form.Label>
                                <Input {...attrs} bind:value={$formData.min_professor_number_masters}/>
                            </Form.Control>
                            <Form.Description>
                                Il numero minimo di professori necessari per una commissione magistrale
                            </Form.Description>
                            <Form.FieldErrors/>
                        </Form.Field>
                    </div>
                </div>

                <div class="rounded-lg border p-4 mt-4">
                    <h3 class="text-lg">Impostazioni avanzate</h3>
                    <Separator decorative={true} class="mt-2 mb-4"/>
                    <Form.Field {form} name="solver">
                        <Form.Control let:attrs>
                            <Form.Label>Solver</Form.Label>
                            <Select.Root
                                    selected={selectedSolver}
                                    onSelectedChange={(v) => {
                                        v && ($formData.solver = v.value)
                                    }}>
                                <Select.Input name={attrs.name}/>
                                <Select.Trigger {...attrs}>
                                    <Select.Value placeholder="Seleziona un solver"/>
                                </Select.Trigger>
                                <Select.Content>
                                    {#each enumKeys(SolverType) as type}
                                        <Select.Item value={SolverType[type]}>{type}</Select.Item>
                                    {/each}
                                </Select.Content>
                            </Select.Root>
                        </Form.Control>
                        <Form.Description>Il solver da utilizzare per l'ottimizzazione</Form.Description>
                        <Form.FieldErrors/>
                    </Form.Field>

                    <div class="grid grid-cols-2 gap-4 mt-4">
                        <Form.Field {form} name="optimization_time_limit">
                            <Form.Control let:attrs>
                                <Form.Label>Limite di tempo per l'ottimizzazione</Form.Label>
                                <Input {...attrs} bind:value={$formData.optimization_time_limit}/>
                            </Form.Control>
                            <Form.Description>Il limite di tempo massimo per l'ottimizzazione (in secondi)
                            </Form.Description>
                            <Form.FieldErrors/>
                        </Form.Field>

                        <Form.Field {form} name="optimization_gap">
                            <Form.Control let:attrs>
                                <Form.Label>Gap di ottimizzazione</Form.Label>
                                <Input {...attrs} bind:value={$formData.optimization_gap}/>
                            </Form.Control>
                            <Form.Description>Il gap di ottimizzazione massimo accettabile</Form.Description>
                            <Form.FieldErrors/>
                        </Form.Field>
                    </div>
                </div>

                {#if browser && $debugEnabled}
                    <div class="my-4">
                        <SuperDebug data={$formData} theme="vscode" status={false}/>
                    </div>
                {/if}
            </form>
        </div>
    </div>

    <Separator decorative={true}/>
{/if}