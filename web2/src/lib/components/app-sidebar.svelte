<script lang="ts">
    import * as Sidebar from "$lib/components/ui/sidebar"
    import * as Collapsible from "$lib/components/ui/collapsible"

    // Icons
    import MdiAlertCircleOutline from '~icons/mdi/alert-circle-outline'
    import MdiRobotExcited from '~icons/mdi/robot-excited'
    import MdiBookInformationVariant from '~icons/mdi/book-information-variant'
    import MdiCogOutline from '~icons/mdi/cog-outline'
    import MdiBookClock from '~icons/mdi/book-clock'
    import MdiChevronDown from '~icons/mdi/chevron-down'
    import MdiPlus from '~icons/mdi/plus'
    import RadixIconsTrash from '~icons/radix-icons/trash'
    import RadixIconsArchive from '~icons/radix-icons/archive'
    import RadixIconsPencil2 from '~icons/radix-icons/pencil-2'
    import MdiAccountGroup from '~icons/mdi/account-group'

    // Replace with your real data / store
    const commissions = [
        {id: 1, title: "Commission Spring 2025", url: "/commissions/1"},
        {id: 2, title: "Commission Fall 2025", url: "/commissions/2"}
    ];
</script>

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
        <Sidebar.Group>
            <Sidebar.Menu>
                <Sidebar.MenuItem>
                    <Sidebar.MenuButton>
                        <MdiBookClock/>
                        <span>Sessioni attive</span>
                    </Sidebar.MenuButton>
                </Sidebar.MenuItem>
                <Sidebar.MenuItem>
                    <Sidebar.MenuButton>
                        <RadixIconsArchive/>
                        <span>Sessioni Archiviate</span>
                    </Sidebar.MenuButton>
                </Sidebar.MenuItem>
                <Sidebar.MenuItem>
                    <Sidebar.MenuButton>
                        <MdiAccountGroup/>
                        <span>Elenco Docenti</span>
                    </Sidebar.MenuButton>
                </Sidebar.MenuItem>
            </Sidebar.Menu>
        </Sidebar.Group>
    </Sidebar.Content>
    <Sidebar.Footer>
        <Sidebar.Menu>
            <Sidebar.MenuItem>
                <Sidebar.MenuButton>
                    <MdiRobotExcited/>
                    <span>Stato Solver</span>
                </Sidebar.MenuButton>
            </Sidebar.MenuItem>
            <Sidebar.MenuItem>
                <Sidebar.MenuButton>
                    <MdiCogOutline/>
                    <span>Impostazioni</span>
                </Sidebar.MenuButton>
            </Sidebar.MenuItem>
            <Sidebar.MenuItem>
                <Sidebar.MenuButton>
                    <MdiBookInformationVariant/>
                    <span>Documentazione</span>
                </Sidebar.MenuButton>
            </Sidebar.MenuItem>
        </Sidebar.Menu>
    </Sidebar.Footer>
</Sidebar.Root>