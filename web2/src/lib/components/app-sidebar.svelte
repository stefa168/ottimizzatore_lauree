<script lang="ts">
    import * as Sidebar from "$lib/components/ui/sidebar"
    import * as Collapsible from "$lib/components/ui/collapsible"

    // Icons
    import MdiRobotExcited from '~icons/mdi/robot-excited'
    import MdiBookInformationVariant from '~icons/mdi/book-information-variant'
    import MdiCogOutline from '~icons/mdi/cog-outline'
    import MdiBookClock from '~icons/mdi/book-clock'
    import RadixIconsArchive from '~icons/radix-icons/archive'
    import MdiAccountGroup from '~icons/mdi/account-group'

    import type {Component} from "svelte";
    import type {SvelteHTMLElements} from "svelte/elements";
    import AppSettingsDialog from "./app-settings-dialog.svelte";

    interface SidebarItem {
        title: string;
        path: string;
        icon?: Component<SvelteHTMLElements['svg']>;
        isActive?: boolean;
    }

    let settingsDialog: AppSettingsDialog = $state();

    const items: {
        body: SidebarItem [],
        footer: SidebarItem[]
    } = {
        body: [{
            title: "Sessioni attive",
            icon: MdiBookClock,
            path: "/gradsession",
            isActive: true
        }, {
            title: "Sessioni Archiviate",
            icon: RadixIconsArchive,
            path: "/archive",
            isActive: true
        }, {
            title: "Elenco Docenti",
            icon: MdiAccountGroup,
            path: "/professors",
            isActive: true
        }],
        footer: [{
            title: "Stato Solver",
            icon: MdiRobotExcited,
            path: "#",
            isActive: false
        }, {
            title: "Documentazione",
            icon: MdiBookInformationVariant,
            path: "#",
            isActive: false
        }]
    };
</script>

{#snippet sidebarItemSnip(items: SidebarItem[])}
    {#each items as item (item.title)}
        <Sidebar.MenuItem>
            <Sidebar.MenuButton>
                {#snippet child({props})}
                    <a href={item.path} {...props}>
                        <item.icon/>
                        <span>{item.title}</span>
                    </a>
                {/snippet}
            </Sidebar.MenuButton>
        </Sidebar.MenuItem>
    {/each}
{/snippet}

<Sidebar.Root variant="sidebar" collapsible="icon">
    <Sidebar.Header>
        <a href="/" class="flex items-center">
            <img src="/Logo_UniTO_2022_no_testo.svg" class="h-12" alt="Logo Unito"/>
            <h3 class="text-center text-2xl font-semibold
                group-data-[collapsible=icon]:opacity-0
                group-data-[collapsible=icon]:pointer-events-none
                group-data-[collapsible=icon]:select-none">
                Ottimizzatore Lauree
            </h3>
        </a>
    </Sidebar.Header>
    <Sidebar.Content>
        <Sidebar.Menu>

            <Sidebar.Group>
                {@render sidebarItemSnip(items.body)}
            </Sidebar.Group>
        </Sidebar.Menu>
    </Sidebar.Content>
    <Sidebar.Footer>
        {@render sidebarItemSnip(items.footer)}
        <Sidebar.Menu>

            <Sidebar.MenuItem>
                <Sidebar.MenuButton onclick={() => settingsDialog.toggleDialog()}>
                    <MdiCogOutline/>
                    Impostazioni
                </Sidebar.MenuButton>
            </Sidebar.MenuItem>
        </Sidebar.Menu>
    </Sidebar.Footer>
</Sidebar.Root>

<AppSettingsDialog bind:this={settingsDialog}/>