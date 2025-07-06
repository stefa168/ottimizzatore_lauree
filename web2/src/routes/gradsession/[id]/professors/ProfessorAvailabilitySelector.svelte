<script lang="ts">
  import * as Select from '@/components/ui/select'
  import type {ProfessorAvailability} from "@/types";

  interface Props {
    value: ProfessorAvailability | string;
    onUpdateValue?: (newAvailability: ProfessorAvailability) => Promise<void>;
  }

  let {value = $bindable(), onUpdateValue}: Props = $props();

  const options: { value: string, label: string, disabled?: boolean }[] = [
    {value: 'always', label: 'Tutto il giorno'},
    {value: 'morning', label: 'Solo la Mattina'},
    {value: 'afternoon', label: 'Solo il Pomeriggio'},
    {value: 'split', label: 'Sdoppia il docente'},
  ];

  let selectedLabel = $derived(options.find(el => el.value === value) ?? options[0]);

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
      {#each options as opt}
        <Select.Item value={opt.value} label={opt.label} disabled={opt.disabled}>{opt.label}</Select.Item>
      {/each}
    </Select.Group>
  </Select.Content>
</Select.Root>