<script lang="ts">
  import {Input} from "@/components/ui/input";
  import SuspenseOverlay from "@/components/suspense/SuspenseOverlay.svelte";

  interface Props {
    value: number;
    onSave: (value: number) => Promise<void>;
    label: string;
    min?: number;
    max?: number;
    step?: number;
    // Shown after the input, e.g. "min"
    suffix?: string;
  }

  let {value, onSave, label, min = 0, max = 1000, step = 1, suffix}: Props = $props();

  let overlay: SuspenseOverlay;

  const save = async (e: Event) => {
    const input = e.currentTarget as HTMLInputElement;
    const next = Math.min(max, Math.max(min, Math.round(Number(input.value) || 0)));
    input.value = String(next);
    if (next !== value)
      // A failure is already shown by the overlay and the caller's toast
      await overlay.waitFor(onSave(next)).catch(() => undefined);
  };
</script>

<SuspenseOverlay bind:this={overlay}>
  <div class="flex items-center gap-1">
    <Input type="number" class="h-7 w-20" {min} {max} {step} {value} onchange={save} aria-label={label}/>
    {#if suffix}
      <span class="text-xs text-muted-foreground">{suffix}</span>
    {/if}
  </div>
</SuspenseOverlay>
