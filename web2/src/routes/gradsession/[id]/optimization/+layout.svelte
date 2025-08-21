<script lang="ts">
  import type {LayoutProps} from "./$types";
  let {children, data}: LayoutProps = $props();
</script>

{@render children?.()}