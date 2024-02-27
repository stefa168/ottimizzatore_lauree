<script>
    import "../app.css";
    import {ModeWatcher} from "mode-watcher";
    import {Toaster} from "$lib/components/ui/sonner/";

    // https://kit.svelte.dev/docs/single-page-apps
    export const ssr = false;
</script>

<ModeWatcher/>
<Toaster closeButton/>
<slot />