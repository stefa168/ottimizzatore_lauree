<script lang="ts">
  import type {LayoutProps} from "./$types";
  import {ModeWatcher} from 'mode-watcher';

  import '../app.css';

  import AppNavbar from "@/components/AppNavbar.svelte";
  import {Toaster} from "@/components/ui/sonner";

  let {children}: LayoutProps = $props();
</script>

<svelte:head>
  <title>Ottimizzatore Lauree</title>
</svelte:head>

<!-- For dark/light mode -->
<ModeWatcher/>
<Toaster closeButton richColors/>

<div class="flex min-h-screen w-full flex-col">
  <AppNavbar/>
  <main class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 mt-4">
    <!-- Pages await remote queries; their errors (e.g. backend unreachable) are shown by the +error pages -->
    {@render children?.()}
  </main>
</div>
