<script lang="ts">
  import type {Snippet} from "svelte";
  import {SuspenseManager} from "@/components/suspense/base.svelte";

  interface Props {
    children: Snippet,
  }

  let {children}: Props = $props();

  let manager = new SuspenseManager();
  export const waitFor = <U>(p: Promise<U>) => manager.waitFor(p);
</script>

<div class="relative inline-block">
  {@render children()}

  {#if manager.updatePromise}
    <div class="absolute inset-0 z-10 grid place-items-center bg-background/60 backdrop-blur-sm pointer-events-auto">
      {#await manager.updatePromise}
        <!-- Pending overlay -->
        <div class="flex items-center gap-2 text-sm text-muted-foreground">
          <span class="size-4 rounded-full border-2 border-current border-l-transparent animate-spin"></span>
          <span>Salvataggio…</span>
        </div>
      {:then _}
        <!-- Success overlay -->
        <div class="text-green-600 text-sm">
          Aggiornato!
        </div>
      {:catch e}
        <!-- Error overlay -->
        <div class="text-destructive text-sm text-center">
          Errore durante il salvataggio
        </div>
      {/await}
    </div>
  {/if}
</div>