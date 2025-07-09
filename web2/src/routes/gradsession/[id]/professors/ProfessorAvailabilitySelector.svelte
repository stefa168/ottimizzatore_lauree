<script lang="ts">
  import * as Select from '@/components/ui/select'
  import type {ProfessorAvailability} from "@/types";
  import {AvailabilityOptions} from "@/const";

  interface Props {
    value: ProfessorAvailability | string;
    onUpdateValue?: (newAvailability: ProfessorAvailability) => Promise<void>;
  }

  let {value = $bindable(), onUpdateValue}: Props = $props();

  let selectedLabel = $derived(AvailabilityOptions.get(value) ?? AvailabilityOptions.values().next().value!);

  const onValueChange = async (v: string) => {
    if (!onUpdateValue)
      return;

    await onUpdateValue(v as ProfessorAvailability);
  };
</script>

<Select.Root type="single" bind:value={value} {onValueChange}>
  <Select.Trigger style="height: 1.6rem">
    <span>{selectedLabel.label}</span>
  </Select.Trigger>
  <Select.Content>
    <Select.Group>
      <Select.Label>Disponibilità</Select.Label>
      {#each AvailabilityOptions.values() as opt}
        <Select.Item value={opt.value} label={opt.label} disabled={opt.disabled}>{opt.label}</Select.Item>
      {/each}
    </Select.Group>
  </Select.Content>
</Select.Root>