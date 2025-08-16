<script lang="ts">
  import * as Select from '@/components/ui/select'
  import type {UniversityRole} from "@/types";
  import {UniversityRoles} from "@/const";
  import SuspenseOverlay from "@/components/SuspenseOverlay.svelte";

  interface Props {
    value: UniversityRole | string;
    onUpdateValue?: (newRole: UniversityRole) => Promise<void>;
  }

  let {value = $bindable(), onUpdateValue}: Props = $props();

  let selectedLabel = $derived(
    UniversityRoles.get(value) ?? {
      value: '',
      label: "Seleziona un ruolo"
    }
  )

  let overlay: SuspenseOverlay;

  const onValueChange = async (v: string) => {
    if (!onUpdateValue) return;
    await overlay.waitFor(onUpdateValue(v as UniversityRole));
  };
</script>

<SuspenseOverlay bind:this={overlay}>
  <Select.Root type="single" bind:value={value} {onValueChange}>
    <Select.Trigger
        style="height: 1.6rem"
        class={{ 'bg-destructive/25': value === 'unspecified' }}
    >
      <span class={{ 'text-destructive': value === 'unspecified' }}>
        {selectedLabel.label}
      </span>
    </Select.Trigger>
    <Select.Content>
      <Select.Group>
        <Select.Label>Ruoli</Select.Label>
        {#each UniversityRoles.values() as role}
          <Select.Item value={role.value} label={role.label} disabled={role.disabled}>
            {role.label}
          </Select.Item>
        {/each}
      </Select.Group>
    </Select.Content>
  </Select.Root>
</SuspenseOverlay>