<script lang="ts">
    import {selectedConfiguration} from "$lib/store";
    import {Separator} from "$lib/components/ui/separator";
    import {Input} from "$lib/components/ui/input";
    import {Label} from "$lib/components/ui/label";
    import * as Form from "$lib/components/ui/form";
    import {Switch} from "$lib/components/ui/switch";
    import {z} from "zod";
    import {SolverType} from "../optimization_types";
    import SuperDebug, {defaults, superForm, superValidate} from "sveltekit-superforms";
    import {zod} from "sveltekit-superforms/adapters";
    import {browser} from "$app/environment";
    import MdiReminder from '~icons/mdi/reminder'

    const optimizationConfigurationSchema = z.object({
        title: z.string().min(1).max(256),
        max_duration: z.coerce.number().min(0).default(210),
        max_commissions_morning: z.coerce.number().min(0).default(6),
        max_commissions_afternoon: z.coerce.number().min(0).default(6),
        online: z.boolean().default(false),

        min_professor_number: z.coerce.number().min(1).nullable().default(null),
        min_professor_number_masters: z.coerce.number().min(1).nullable().default(null),
        max_professor_number: z.coerce.number().min(1).nullable().default(null),

        solver: z.nativeEnum(SolverType).default(SolverType.CPLEX),
        optimization_time_limit: z.coerce.number().min(60).default(60),
        optimization_gap: z.coerce.number().min(0).default(0.005),
    }).refine((data) => {
        // If online, then the minimum number of professors must be defined
        return data.online ? data.min_professor_number !== null : true;
    }, {
        message: "Il numero minimo di professori deve essere definito se la commissione è online",
        path: ["min_professor_number"]
    }).refine((data) => {
        // If online, then the minimum number of professors for the master's degree must be defined
        return data.online ? data.min_professor_number_masters !== null : true;
    }, {
        message: "Il numero minimo di professori per il corso di laurea magistrale deve essere definito se la commissione è online",
        path: ["min_professor_number_masters"]
    }).refine((data) => {
        // If online, then the maximum number of professors must be defined
        return data.online ? data.max_professor_number !== null : true;
    }, {
        message: "Il numero massimo di professori deve essere definito se la commissione è online",
        path: ["max_professor_number"]
    }).refine((data) => {
        // If online, then the minimum number of professors must be less than or equal to the maximum number of professors
        if (data.online && data.min_professor_number !== null && data.max_professor_number !== null) {
            return data.min_professor_number <= data.max_professor_number;
        } else {
            return true;
        }
    }, {
        message: "Il numero minimo di professori deve essere minore o uguale al numero massimo di professori se la commissione è online",
        path: ["min_professor_number", "max_professor_number"]
    }).refine((data) => {
        // If online, then the minimum number of professors must be less than or equal to the maximum number of professors
        if (data.online && data.min_professor_number !== null && data.max_professor_number !== null) {
            return data.min_professor_number <= data.max_professor_number;
        } else {
            return true;
        }
    }, {
        message: "Il numero minimo di professori deve essere minore o uguale al numero massimo di professori se la commissione è online",
        path: ["min_professor_number_masters", "max_professor_number"]
    });

    const form = superForm(
        defaults($selectedConfiguration, zod(optimizationConfigurationSchema)), {
            SPA: true,
            validationMethod: "oninput",
            validators: zod(optimizationConfigurationSchema)
        }
    )
    const {form: formData, enhance} = form;

</script>

{#if $selectedConfiguration}
    <h2 class="mt-4 mb-2 text-xl">{$selectedConfiguration.title}</h2>
    <form id="optimizationDetailsEditor"
          method="post"
          enctype="multipart/form-data"
          use:enhance>
        <!-- Todo add feedback sections if errors occur -->
        <div class="rounded-lg border p-4">
            <h3 class="text-lg">Impostazioni Generali</h3>
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
            <h3 class="text-lg">Massimo numero di commissioni</h3>
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
                    Se le commissioni di laurea saranno svolte online
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
                    <Input type="select" {...attrs} bind:value={$formData.solver}>
                        <option value={SolverType.CPLEX}>CPLEX</option>
                        <option value={SolverType.GUROBI}>GUROBI</option>
                    </Input>
                </Form.Control>
                <Form.Description>Il solver da utilizzare per l'ottimizzazione</Form.Description>
                <Form.FieldErrors/>
            </Form.Field>

            <Form.Field {form} name="optimization_time_limit">
                <Form.Control let:attrs>
                    <Form.Label>Limite di tempo per l'ottimizzazione</Form.Label>
                    <Input {...attrs} bind:value={$formData.optimization_time_limit}/>
                </Form.Control>
                <Form.Description>Il limite di tempo massimo per l'ottimizzazione in secondi</Form.Description>
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

        {#if browser}
            <SuperDebug data={$formData}/>
        {/if}
    </form>
{/if}