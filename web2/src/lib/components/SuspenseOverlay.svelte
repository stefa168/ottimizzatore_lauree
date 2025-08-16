<script lang="ts">
  import type {Snippet} from "svelte";

  interface Props {
    children: Snippet,
  }

  let {children}: Props = $props();

  let updatePromise = $state<Promise<unknown> | null>(null)
  let lastError: unknown = $state(null)

  export async function waitFor<U>(p: Promise<U>): Promise<U | undefined> {
    lastError = null;

    updatePromise = p;

    try {
      return await p;
    } catch (e) {
      lastError = e;
    } finally {
      const delay = lastError ? 2500 : 800
      setTimeout(() => {
        if (updatePromise === p) {
          updatePromise = null;
        }
      }, delay);
    }
  }
</script>

<div class="relative inline-block">
  {@render children()}

  {#if updatePromise}
    <div
        class="absolute inset-0 z-10 grid place-items-center bg-background/60 backdrop-blur-sm pointer-events-auto"
    >
      {#await updatePromise}
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