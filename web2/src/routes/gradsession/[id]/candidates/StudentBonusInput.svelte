<script lang="ts">
  import {Input} from "@/components/ui/input";
  import SuspenseOverlay from "@/components/suspense/SuspenseOverlay.svelte";

  interface Props {
    value: number;
    onSave: (minutes: number) => Promise<void>;
  }

  let {value, onSave}: Props = $props();

  const MAX_BONUS = 120;
  let overlay: SuspenseOverlay;

  const save = async (e: Event) => {
    const input = e.currentTarget as HTMLInputElement;
    const minutes = Math.min(MAX_BONUS, Math.max(0, Math.round(Number(input.value) || 0)));
    input.value = String(minutes);
    if (minutes !== value)
      // A failure is already shown by the overlay and the caller's toast
      await overlay.waitFor(onSave(minutes)).catch(() => undefined);
  };
</script>

<SuspenseOverlay bind:this={overlay}>
  <div class="flex items-center gap-1">
    <Input type="number" class="h-7 w-20" min="0" max={MAX_BONUS} step="5"
           {value} onchange={save}
           aria-label="Tempo bonus in minuti"/>
    <span class="text-xs text-muted-foreground">min</span>
  </div>
</SuspenseOverlay>
