<script>
    import "../app.css";
    import {ModeWatcher} from "mode-watcher";

    // https://kit.svelte.dev/docs/single-page-apps
    export const ssr = false;
</script>

<ModeWatcher/>
<slot />