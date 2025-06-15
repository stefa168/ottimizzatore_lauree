<script lang="ts">
    import '../app.css';

    import * as Sidebar from "$lib/components/ui/sidebar"
    import AppSidebar from '@/components/app-sidebar.svelte';
	import { ModeWatcher } from 'mode-watcher';

    let {children} = $props();
</script>

<svelte:head>
    <title>Ottimizzatore Lauree</title>
</svelte:head>

<!-- For dark/light mode -->
<ModeWatcher/>

<Sidebar.Provider>
    <AppSidebar/>

    <main>
        <Sidebar.Trigger/>
        {@render children?.()}
    </main>
</Sidebar.Provider>