<script lang="ts">
    import type {LayoutProps} from "./$types";
    import {ModeWatcher} from 'mode-watcher';

    import '../app.css';

    import {QueryClientProvider} from "@tanstack/svelte-query";
    import {SvelteQueryDevtools} from "@tanstack/svelte-query-devtools";
    import AppNavbar from "@/components/AppNavbar.svelte";

    let {data, children}: LayoutProps = $props();
</script>

<svelte:head>
    <title>Ottimizzatore Lauree</title>
</svelte:head>

<!-- For dark/light mode -->
<ModeWatcher/>

<QueryClientProvider client={data.queryClient}>
    <div class="flex min-h-screen w-full flex-col">
        <AppNavbar/>
        <main class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 mt-4">
            {@render children?.()}
        </main>
    </div>
    <SvelteQueryDevtools buttonPosition="bottom-left"/>
</QueryClientProvider>