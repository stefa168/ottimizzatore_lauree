<script lang="ts">
  import {SuspenseManager} from "@/components/suspense/base.svelte";
  import type {Snippet} from "svelte";
  import type {ClassValue} from "clsx";

  export type a = never;

  interface Props {
    children?: Snippet<[{
      loading: boolean
    }]>;
    onclick?: (event: MouseEvent) => Promise<void>,
    class?: ClassValue,
  }

  let {children, onclick, class: className}: Props = $props();

  let manager = new SuspenseManager<unknown>();
  let loading = $derived(manager.running);

  export const clickEvent = async (event: MouseEvent) => {
    loading = true;
    if (onclick) await manager.waitFor(onclick(event))
  }
</script>

<button onclick={clickEvent} disabled={(loading)} class={[className]} data-loading={(loading)}>
  {@render children?.({loading})}
</button>