<script lang="ts">
  import {Badge} from "@/components/ui/badge";
  import LucideSnowflake from '~icons/lucide/snowflake'

  let {title, frozen}: { title: string, frozen: boolean } = $props();
</script>

<span class="flex items-center gap-2">
  {title}
  {#if frozen}
    <Badge variant="secondary" title="Soluzione finale"><LucideSnowflake class="size-3"/> Congelata</Badge>
  {/if}
</span>
