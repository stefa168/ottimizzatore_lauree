<script lang="ts">
  import {SuspenseManager} from "@/components/suspense/base.svelte";
  import type {Snippet} from "svelte";

  export type a = never;

  interface Props {
    children: Snippet<[{
      loading: boolean
    }]>;
    onclick?: (event: MouseEvent) => Promise<void>
  }

  let {children, onclick}: Props = $props();

  let manager = new SuspenseManager<unknown>();
  let loading = $derived(manager.running);

  export const clickEvent = async (event: MouseEvent) => {
    if (onclick) await manager.waitFor(onclick(event))
  }
</script>

<button onclick={clickEvent} disabled={(loading)}>
  <!--{@render children({loading})}-->
  {@render children({loading})}
</button>