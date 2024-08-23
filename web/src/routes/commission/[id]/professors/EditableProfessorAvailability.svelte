<script lang="ts">
    import {BodyRow, type DataBodyRow, DataColumn} from "svelte-headless-table";
    import type {Professor, ProfessorAvailability,} from "../commission_types";
    import * as Select from '$lib/components/ui/select'
    import type {Selected} from "bits-ui";

    export let row: BodyRow<Professor>;
    export let value: ProfessorAvailability | string;
    export let onUpdateValue: <T extends keyof Professor> (p: Professor, field: T, newValue: Professor[T]) => Promise<boolean>;

    type Selectable = { value: string, label: string, disabled?: boolean };

    const options: Selectable[] = [
        {value: 'always', label: 'Tutto il giorno'},
        {value: 'morning', label: 'Solo la Mattina'},
        {value: 'afternoon', label: 'Solo il Pomeriggio'},
    ];

    function getSelectedOption(s: ProfessorAvailability | string, options: Selectable[]): Selectable {
        return options.find(a => a.value == s) ?? options[0];
    }

    let lastUpdateErrored = false;

    $: selected = getSelectedOption(value, options);

    const handleSubmit = async (v: Selected<string> | undefined) => {
        const new_value = v?.value ?? 'always';
        if (row.isData()) {
            let r = await onUpdateValue(row.original, "availability", new_value as ProfessorAvailability);

            if (r) {
                value = new_value;
            } else {
                selected = getSelectedOption(value, options);
            }

            lastUpdateErrored = !r;
        }
    }

</script>

<Select.Root {selected} onSelectedChange={handleSubmit}>
    <Select.Trigger class="{lastUpdateErrored ? 'bg-warning/25' : ''}">
        <Select.Value class="{lastUpdateErrored ? 'text-warning' : ''}" placeholder="Indicare la disponibilità" />
    </Select.Trigger>
    <Select.Content>
        <Select.Group>
            <Select.Label>Periodo disponibile</Select.Label>
            {#each options as o}
                <Select.Item value={o.value} label={o.label} disabled={o.disabled}>{o.label}</Select.Item>
            {/each}
        </Select.Group>
    </Select.Content>
    <Select.Input name="availability"/>
</Select.Root>