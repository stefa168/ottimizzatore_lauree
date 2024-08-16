<script lang="ts">
    import {onDestroy, onMount} from "svelte";
    import {goto} from "$app/navigation";
    import {page} from "$app/stores";
    import {get} from "svelte/store";
    import {selectedConfiguration, selectedProblem} from "$lib/store";
    import {toast} from "svelte-sonner";
    // noinspection TypeScriptCheckImport
    import {env} from "$env/dynamic/public";

    import type {Selected} from "bits-ui";
    import * as Select from '$lib/components/ui/select'
    import * as Button from '$lib/components/ui/button'

    import MdiFileDocumentPlusOutline from '~icons/mdi/file-document-plus-outline'

    import type {OptimizationConfiguration} from "./optimization_types";

    $: availableConfigurations = $selectedProblem?.optimization_configurations ?? [];

    const newConfigMagicValue = '$$#!#$$newConfig$$!#!$$';

    onMount(() => {
        const problem = get(selectedProblem);

        if (problem === undefined) return;

        const configurations = problem.optimization_configurations;

        // Inside here we will call a goto to redirect the user to the correct configuration.
        // The setting of the configuration store is delegated to the +page in [opt_id].
        if (configurations.length === 0) {
            // This branch is only executed when there are no configurations available, so one is created by default
            fetch(`${env.PUBLIC_API_URL}/commission/${problem.id}/configuration`, {method: 'POST'})
                .then(r => r.json())
                .then((r: { new_config: OptimizationConfiguration }) => {
                    problem.optimization_configurations = [r.new_config];
                    console.log('no configuration found, created new one', r.new_config);
                    toast.info(`Nessuna configurazione trovata, ne ho creata una nuova.`);
                    goto(`/commission/${problem.id}/optimization/${r.new_config.id}`);
                });
        } else if (configurations.length === 1 && $page.params.opt_id === undefined) {
            // This branch is only executed when there is only one configuration available and the user has not selected any
            console.log(`found only one configuration, redirecting to ${configurations[0].id} - ${configurations[0].title}`);
            toast.info(`Ho trovato solo una configurazione, la sto aprendo automaticamente.`);
            goto(`/commission/${problem.id}/optimization/${configurations[0].id}`);
        }
    });

    onDestroy(() => {
        selectedConfiguration.set(undefined);
    });

    const handleConfigurationChoice = (v: Selected<number | string | undefined> | undefined) => {
        if (!v) return;

        if (v.value === newConfigMagicValue) {
            fetch(`${env.PUBLIC_API_URL}/commission/${$selectedProblem?.id}/configuration`, {method: 'POST'})
                .then(r => r.json())
                .then((r: { new_config: OptimizationConfiguration }) => {
                    $selectedProblem?.optimization_configurations.push(r.new_config);
                    console.log('created new configuration', r.new_config);
                    toast.info(`Nuova configurazione creata. Procedo ad aprirla.`);
                    goto(`/commission/${$selectedProblem?.id}/optimization/${r.new_config.id}`);
                });
            return;
        }

        goto(`/commission/${$page.params.id}/optimization/${v.value}`);
    }
</script>

<Select.Root
        selected={{
            value: $selectedConfiguration?.id ?? undefined,
            label: $selectedConfiguration?.title ?? undefined
        }}
        onSelectedChange={handleConfigurationChoice}>
    <Select.Trigger>
        <Select.Value placeholder="Scegli o crea una configurazione"/>
    </Select.Trigger>
    <Select.Content>
        <Select.Item value={newConfigMagicValue}>
            <MdiFileDocumentPlusOutline class="w-4 h-4 me-2"/>
            Crea una nuova configurazione dei parametri
        </Select.Item>
        <Select.Separator/>
        <Select.Group>
            <Select.Label>Configurazioni disponibili</Select.Label>
            {#each availableConfigurations as config}
                <Select.Item value={config.id} label={config.title}>{config.title}</Select.Item>
            {/each}
        </Select.Group>
    </Select.Content>
    <Select.Input name="role"/>
</Select.Root>

<slot/>