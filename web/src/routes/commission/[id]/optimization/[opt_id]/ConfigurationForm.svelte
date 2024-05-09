<script lang="ts">
    import {debugEnabled, selectedProblem} from "$lib/store";
    import {enumKeys} from "$lib/utils";
    import {browser} from "$app/environment";

    import {type OptimizationConfiguration, SolverType} from "../optimization_types";

    import * as Form from "$lib/components/ui/form";
    import * as Select from "$lib/components/ui/select";
    import {Input} from "$lib/components/ui/input";
    import {Switch} from "$lib/components/ui/switch";
    import {Separator} from "$lib/components/ui/separator";

    import SuperDebug, {defaults, superForm} from "sveltekit-superforms";
    import {generateForForm, optimizationConfigurationSchema} from "./schema";
    import {zod} from "sveltekit-superforms/adapters";
    import {derived, type Writable} from "svelte/store";
    // noinspection TypeScriptCheckImport
    import {env} from '$env/dynamic/public';

    import type {OptimizationStatus} from "./types";

    // Icons
    import MdiReminder from '~icons/mdi/reminder'

    export let optStatus: OptimizationStatus;
    export let selectedConfiguration: Writable<OptimizationConfiguration | undefined>;

    let submitting = false;
    console.log("Loading form");
    const form = superForm(defaults(generateForForm($selectedConfiguration), zod(optimizationConfigurationSchema)), {
            SPA: true,
            validationMethod: "oninput",
            validators: zod(optimizationConfigurationSchema),
            taintedMessage: "La configurazione è stata modificata. Confermi di voler perdere le modifiche non salvate?",
            async onUpdate({form, cancel}) {
                submitting = true;
                if (form.valid) {
                    const cid = $selectedConfiguration!.commission_id;
                    const conf_id = $selectedConfiguration!.id;
                    await fetch(`${env.PUBLIC_API_URL}/commission/${cid}/configuration/${conf_id}`, {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify(form.data)
                    }).then(async (response) => {
                        if (response.ok) {
                            // todo update the new data now that the fields have been updated on the server-side
                            await response.json().then((data: {
                                success: string,
                                updated_config: OptimizationConfiguration
                            }) => {
                                const newConf = data.updated_config;

                                console.log(newConf);
                                selectedProblem.update((p) => {
                                    if(!p) return undefined;

                                    const index = p.optimization_configurations.findIndex((c) => c.id === newConf.id);
                                    p.optimization_configurations[index] = newConf;

                                    return p;
                                });
                                selectedConfiguration.set(newConf);
                            });
                        } else {
                            await response.json().then((data) => {
                                console.error(data);
                                cancel();
                                // todo show error message
                            });
                        }
                    }).catch((error) => {
                        console.error(error);
                    }).finally(() => {
                        submitting = false;
                    });
                } else {
                    submitting = false;
                }
            }
        }
    )
    const {form: formData, enhance} = form;

    // the right way to use superform/formsnap with bits-ui is this:
    // https://formsnap.dev/docs/recipes/bits-ui-select#setup-the-form
    $: selectedSolver = {
        label: String($formData.solver).toUpperCase(),
        value: $formData.solver
    };

    // noinspection JSUnusedGlobalSymbols
    export const tainted_fields_count = derived(form.tainted, (tainted) => {
        return tainted ? Object.keys(tainted).length : 0;
    });

    export function reset() {
        form.reset();
    }

    export function submit() {
        form.submit();
    }
</script>

{#if $selectedConfiguration !== undefined}
    <form id="optimizationDetailsEditor"
          method="post"
          enctype="multipart/form-data"
          use:enhance>
        <!-- Todo add feedback sections if errors occur -->
        <fieldset
                disabled={submitting || $optStatus.configurationLocked || $optStatus.solutions.all.length > 0}>
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
                        <Input type="number" {...attrs} bind:value={$formData.max_duration}/>
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
                            <Input type="number" {...attrs} bind:value={$formData.max_commissions_morning}/>
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
                            <Form.Label class="text-lg">Sessione online</Form.Label>
                            <Switch {...attrs} bind:checked={$formData.online} class="ms-3 justify-self-end"/>
                        </div>
                    </Form.Control>
                    <Form.Description class="{$selectedConfiguration.run_lock ? 'hidden' : ''}">
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
                                <Input type="number" {...attrs} bind:value={$formData.min_professor_number}/>
                            </Form.Control>
                            <Form.Description>
                                Il numero minimo di professori necessari per una commissione
                            </Form.Description>
                            <Form.FieldErrors/>
                        </Form.Field>

                        <Form.Field {form} name="max_professor_number">
                            <Form.Control let:attrs>
                                <Form.Label>Numero massimo di professori</Form.Label>
                                <Input type="number" {...attrs} bind:value={$formData.max_professor_number}/>
                            </Form.Control>
                            <Form.Description>
                                Il numero massimo di professori necessari per una commissione
                            </Form.Description>
                            <Form.FieldErrors/>
                        </Form.Field>
                    </div>

                    <Form.Field {form} name="min_professor_number_masters">
                        <Form.Control let:attrs>
                            <Form.Label>Numero minimo di professori per il corso di laurea magistrale
                            </Form.Label>
                            <Input type="number" {...attrs}
                                   bind:value={$formData.min_professor_number_masters}/>
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
                            <Input type="number" {...attrs} bind:value={$formData.optimization_time_limit}/>
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
        </fieldset>

        {#if browser && $debugEnabled}
            <div class="my-4">
                <SuperDebug data={$formData} theme="vscode" status={false}/>
            </div>
        {/if}
    </form>
{/if}