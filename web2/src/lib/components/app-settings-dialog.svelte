<script lang="ts">
    import * as Dialog from "@/components/ui/dialog";
    import * as Select from "@/components/ui/select";
    import * as Switch from "@/components/ui/switch";
    import {Separator} from "@/components/ui/separator";

    import {userPrefersMode, setMode, mode} from "mode-watcher";
    import type {Selected} from "bits-ui";

    import {debugEnabled} from "@/store.svelte";

    const themes: Selected<string>[] = [
        {value: "light", label: "Chiaro"},
        {value: "dark", label: "Scuro"},
        {value: "system", label: "Sistema"}
    ];

    interface Props {
        open?: boolean
    }

    let {open = $bindable(false)}: Props = $props();

    export function toggleDialog() {
        open = !open
    }

    const handleThemeChange = (value: string) => {
        const theme = value;
        if (theme !== "system" && theme !== "light" && theme !== "dark") return;
        setMode(theme);
    }

    let currentTheme = $derived(themes.find(t=>t.value===userPrefersMode.current))
</script>

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
                            type="single"
                            onValueChange={handleThemeChange}
                            value={currentTheme?.value}>
                        <!--                            selected={themes.find(t => t.value === userPrefersMode.current)}>-->
                        <Select.Trigger class="w-[180px]" placeholder="Tema">
                            {currentTheme?.label}
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