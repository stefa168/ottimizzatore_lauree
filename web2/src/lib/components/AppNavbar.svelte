<script lang="ts">
    import {page} from "$app/state";
    import type {Component} from "svelte";
    import type {SvelteHTMLElements} from "svelte/elements";

    import MdiRobotExcited from '~icons/mdi/robot-excited'
    import MdiBookInformationVariant from '~icons/mdi/book-information-variant'
    import MdiCogOutline from '~icons/mdi/cog-outline'
    import MdiBookClock from '~icons/mdi/book-clock'
    import RadixIconsArchive from '~icons/radix-icons/archive'
    import MdiAccountGroup from '~icons/mdi/account-group'
    import AppSettingsDialog from "@/components/app-settings-dialog.svelte";

    let sectionName = $derived.by(() => {
        const first = page.url.pathname.split('/').at(1);
        return first ? `/${first}` : '/';
    });

    let settingsDialog: AppSettingsDialog;

    type Section = { caption: string, path: string, icon?: Component<SvelteHTMLElements['svg']> }
    const navigationSections: Section[] = [
        {
            caption: "Sessioni attive",
            icon: MdiBookClock,
            path: "/gradsession",
        }, {
            caption: "Sessioni Archiviate",
            icon: RadixIconsArchive,
            path: "/archive",
        }, {
            caption: "Elenco Docenti",
            icon: MdiAccountGroup,
            path: "/professors",
        }
    ];

    const systemSections: Section[] = [
        {
            caption: "Stato Solver",
            icon: MdiRobotExcited,
            path: "#",
        }, {
            caption: "Documentazione",
            icon: MdiBookInformationVariant,
            path: "#",
        }, {
            caption: "Impostazioni",
            icon: MdiCogOutline,
            path: "#"
        }
    ];
</script>

{#snippet sectionGroup(ss: Section[])}
    {#each ss as s}
        <a href={s.path}
           class="{sectionName === s.path ? 'text-foreground' : 'text-muted-foreground'}
                  hover:text-foreground transition-colors flex items-center">
            <s.icon class="me-2"/>
            <span>{s.caption}</span>
        </a>
    {/each}
{/snippet}

<header class="bg-background sticky top-0 flex h-16 items-center gap-4 border-b px-4 md:px-6">
    <nav class="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6 h-full">
        <header class="h-full">
            <a class="flex items-center gap-2 text-lg font-semibold md:text-base h-full" href="/">
                <img src="/Logo_UniTO_2022_no_testo.svg" class="h-[80%] w-auto" alt="Logo Unito"/>
                <span class="flex flex-col items-center text-center">
                    <span>Ottimizzatore</span>
                    <span>Lauree</span>
                </span>
            </a>
        </header>
        {@render sectionGroup(navigationSections)}
    </nav>

    <div class="flex justify-end items-center gap-4 md:ml-auto md:gap-2 lg:gap-4 text-muted-foreground">
        <a href="#" class="hover:text-foreground transition-colors flex items-center">
            <MdiRobotExcited class="me-2"/>
            <span>Stato Solver</span>
        </a>
        <a href="#" class="hover:text-foreground transition-colors flex items-center">
            <MdiBookInformationVariant class="me-2"/>
            <span>Documentazione</span>
        </a>
        <button class="hover:cursor-pointer hover:text-foreground transition-colors flex items-center"
                onclick={() => settingsDialog.toggleDialog()}>
            <MdiCogOutline/>
            <span>Impostazioni</span>
        </button>
    </div>

    <AppSettingsDialog bind:this={settingsDialog}/>
</header>