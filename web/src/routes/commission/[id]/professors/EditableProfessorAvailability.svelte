<script lang="ts">
    // import {BodyRow, type DataBodyRow, DataColumn} from "svelte-headless-table";
    // import type {Professor, UniversityRole} from "../commission_types";
    import * as Select from '$lib/components/ui/select'
    import type {Selected} from "bits-ui";

/*    export let row: BodyRow<Professor>;
    export let column: DataColumn<Professor>;
    export let value: UniversityRole | string;
    export let onUpdateValue: (rowDataId: Professor, columnId: string, newValue: UniversityRole) => void;*/

    const availabilities = [
        {value: 'day', label: 'Tutto il giorno'},
        {value: 'morning', label: 'Solo la Mattina'},
        {value: 'afternoon', label: 'Solo il Pomeriggio'},
    ];

    $: selected = availabilities[0];

/*    const handleSubmit = (v: Selected<string> | undefined) => {
        if (row.isData()) {
            onUpdateValue(row.original, column.id, (v?.value ?? 'unspecified') as UniversityRole);
        }
        value = v?.value ?? 'unspecified';
    }*/

</script>

<Select.Root {selected}>
    <Select.Trigger>
        <Select.Value placeholder="Indicare la disponibilità"/>
    </Select.Trigger>
    <Select.Content >
        <Select.Group>
            <Select.Label>Periodo disponibile</Select.Label>
            {#each availabilities as a}
                <Select.Item value={a.value} label={a.label}>{a.label}</Select.Item>
            {/each}
        </Select.Group>
    </Select.Content>
    <Select.Input name="availability"/>
</Select.Root>