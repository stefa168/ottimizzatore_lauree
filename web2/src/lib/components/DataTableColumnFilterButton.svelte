<script lang="ts" generics="TData">
  import type {ComponentProps} from "svelte";
  import type {Column} from "@tanstack/table-core";
  import {Button, buttonVariants} from "@/components/ui/button";
  import {Badge} from "@/components/ui/badge";
  import * as Select from "$lib/components/ui/select/";
  import {Select as SelectPrimitive} from "bits-ui";
  import LucideFilter from '~icons/lucide/filter'
  import type {ValueLabelStructure} from "@/types";

  type Props = {
    title: string,
    column: Column<TData>
    entriesMap: Map<string, ValueLabelStructure>
  } & ComponentProps<typeof Button>;

  let {variant = "ghost", title, column, entriesMap, ...restProps}: Props = $props();

  let columnValues = $derived<Map<string, number>>(column.getFacetedUniqueValues());
  let value: string[] = $state([]);

  const onValueChange = (value: string[]) => {
    column.setFilterValue(value);
  }

  $effect(() => {
    if (!column.getIsFiltered())
      value = [];
  })
</script>

<Select.Root type="multiple" bind:value {onValueChange}>
  <!-- Had to use the primitive to avoid all the styles -->
  <SelectPrimitive.Trigger>
    <!-- And a button in a button throws an error, so we have to mimic one ourselves -->
    <span class={buttonVariants({ variant: "ghost" })}>
      {title}
      <LucideFilter class={{"text-chart-2": value.length > 0}}/>
    </span>
  </SelectPrimitive.Trigger>
  <Select.Content>
    {#each columnValues as entry}
      <Select.Item value={entry[0]} class="">
        {entriesMap.get(entry[0])?.label}
        <Badge variant="outline">{entry[1]}</Badge>
      </Select.Item>
    {/each}
  </Select.Content>
</Select.Root>