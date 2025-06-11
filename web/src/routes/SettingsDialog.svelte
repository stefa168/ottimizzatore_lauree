<script lang="ts">
    import * as Dialog from "$lib/components/ui/dialog";
    import * as Select from "$lib/components/ui/select";
    import * as Switch from "$lib/components/ui/switch";
    import {Separator} from "$lib/components/ui/separator/index.js";

    import {get} from "svelte/store";
    import type {Selected} from "bits-ui";
    import {userPrefersMode} from "mode-watcher";
    import {debugEnabled} from "$lib/store";
    import MdiCogOutline from '~icons/mdi/cog-outline'

    interface Props {
        open?: boolean;
    }

    let {open = $bindable(false)}: Props = $props();

    const handleThemeChange = (value: Selected<string> | undefined) => {
        const theme = value?.value;
        if (theme !== "system" && theme !== "light" && theme !== "dark") return;
        userPrefersMode.set(theme);
    }

    const themes: Selected<string>[] = [
        {value: "light", label: "Chiaro"},
        {value: "dark", label: "Scuro"},
        {value: "system", label: "Sistema"}
    ];
</script>

<button class="flex items-center transition dark:hover:text-white"
        onclick={() => open = !open}>
    <MdiCogOutline/>
    <span class="ms-1.5">Impostazioni</span>
</button>

<Dialog.Root bind:open>
    <Dialog.Content>
        <Dialog.Header class="mb-2">
            <Dialog.Title>
                Impostazioni dell'Interfaccia
            </Dialog.Title>
        </Dialog.Header>
        <div class="flex flex-row items-center justify-between px-4">
            <div class="space-y-0.5">
                <div class="flex items-center justify-between">
                    <div class="text-sm font-medium leading-none mb-2">
                        Tema
                    </div>
                    <Select.Root
                            onSelectedChange={handleThemeChange}
                            selected={themes.find(t => t.value === get(userPrefersMode))}>
                        <Select.Trigger class="w-[180px]">
                            <Select.Value placeholder="Tema"/>
                        </Select.Trigger>
                        <Select.Content>
                            {#each themes as theme (theme.value)}
                                <Select.Item value={theme.value}>
                                    {theme.label}
                                </Select.Item>
                            {/each}
                        </Select.Content>
                    </Select.Root>
                </div>
                <div class="text-[0.8rem] text-muted-foreground mt-2">
                    È possibile scegliere tra un'interfaccia chiara e una scura. In alternativa, è
                    possibile lasciare che il sistema scelga automaticamente in base alle impostazioni
                    del sistema operativo.
                </div>
            </div>

        </div>
        <Separator decorative={true}/>
        <div class="flex flex-row items-center justify-between px-4">
            <div class="space-y-0.5">
                <div class="text-sm font-medium leading-none mb-2">
                    Debug
                </div>
                <div class="text-[0.8rem] text-muted-foreground">
                    Attivando questa impostazione verranno mostrati, dove predisposti, una serie di dati
                    aggiuntivi utili per lo sviluppo.
                </div>
            </div>
            <Switch.Root bind:checked={$debugEnabled}/>
        </div>
    </Dialog.Content>
</Dialog.Root>