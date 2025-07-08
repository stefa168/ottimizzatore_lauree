<script lang="ts">

  import type {ComponentProps} from "svelte";
  import {Button} from "@/components/ui/button";
  import {ArrowUpDownIcon, ArrowUpIcon, ArrowDownIcon} from "@lucide/svelte";

  import {type Column} from "@tanstack/table-core";

  type Props = {
    title: string,
    column: Column<any>
  } & ComponentProps<typeof Button>;

  let {variant = "ghost", title, column, ...restProps}: Props = $props();
  let sortDirection = $derived(column.getIsSorted());
</script>

{#if column.getCanSort()}
  <Button {variant} {...restProps}>
    {title}
    {#if sortDirection === "asc"}
      <ArrowUpIcon class="ml-2"/>
    {:else if sortDirection === "desc"}
      <ArrowDownIcon class="ml-2"/>
    {:else}
      <ArrowUpDownIcon class="ml-2"/>
    {/if}

  </Button>
{:else}
  {title}
{/if}
