<script lang="ts">
    // Icons
    import MdiChartPie from '~icons/mdi/chart-pie'
    import MdiArchive from '~icons/mdi/archive'
    import MdiRobotExcited from '~icons/mdi/robot-excited'
    import MdiCogOutline from '~icons/mdi/cog-outline'
    import MdiBookInformationVariant from '~icons/mdi/book-information-variant'

    // Components
    import DropdownButton from "$lib/DropdownButton.svelte";

    // Behaviour

    let fileInput: HTMLInputElement | null;

    async function handle_new_file_submit(event: SubmitEvent) {
        try {
            let excel = fileInput?.files?.[0];

            if (excel == undefined) {
                return;
            }
            if (!(excel.name.endsWith('xlsx') || excel.name.endsWith('xls'))) {
                alert("Sono solo accettati file XLSX o XLS.");
                return;
            }

            let data = new FormData();
            data.append('file', excel)

            const response = await fetch('http://localhost:5000/upload', {
                method: 'POST',
                body: data
            });

            console.log(await response.json());
        } catch (error) {
            console.error("Error:", error)
        }
    }
</script>

<aside id="sidebar"
       class="flex flex-col fixed top-0 left-0 z-40 w-64 h-full transition-transform -translate-x-full sm:translate-x-0 bg-gray-50 dark:bg-gray-800"
       aria-label="Sidebar">
    <!-- Titolo -->
    <header id="sidebar-logo"
            class="px-3 py-4">
        <a href="/" class="flex items-center ">
            <img src="/Logo_UniTO_2022_no_testo.svg" class="h-12" alt="Logo Unito"/>
            <span class="self-center text-center text-xl dark:text-white">Ottimizzatore Lauree</span>
        </a>
    </header>
    <nav id="sidebar-problems-navigator"
         class="flex-grow flex flex-col px-3 pt-4 overflow-y-scroll ">

        <ul class="space-y-2 font-medium">
            <li>
                <DropdownButton buttonText="Problemi Attivi" open={true}>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-blue-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Ottobre 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-red-400 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Dicembre 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                    <li>
                        <a href="#"
                           class="flex items-center p-2 text-gray-900 pl-6 group dark:text-white hover:underline">
                            <span class="bg-purple-600 rounded w-4 h-4"></span>
                            <span class="ms-1.5">Lauree Aprile 2023</span>
                        </a>
                    </li>
                </DropdownButton>
            </li>
            <li class="mt-4 pb-4 ">
                <a href="/"
                   class="flex items-center p-2 text-gray-900 rounded-lg dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 group">
                    <MdiArchive
                            class="flex-shrink-0 w-5 h-5 text-gray-500 transition duration-75 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white"/>
                    <span class="ms-3">Problemi Archiviati</span>
                </a>
            </li>
        </ul>
    </nav>
    <footer id="sidebar-footer"
            class="flex-shrink-0 p-4 w-full z-60 bottom-0 start-0 pt-4 border-t border-gray-700">
        <ul class="ps-0.5 space-y-0.5 text-md text-gray-500 dark:text-gray-400">
            <li>
                <a href="#"
                   class="flex items-center transition dark:hover:text-white">
                    <MdiRobotExcited/>
                    <span class="ms-1.5">Stato Solver</span>
                </a>
            </li>
            <li>
                <a href="#"
                   class="flex items-center transition dark:hover:text-white">
                    <MdiCogOutline/>
                    <span class="ms-1.5">Impostazioni</span>
                </a>
            </li>
            <li>
                <a href="#"
                   class="flex items-center transition dark:hover:text-white">
                    <MdiBookInformationVariant/>
                    <span class="ms-1.5">Documentazione</span>
                </a>
            </li>
        </ul>
    </footer>
</aside>


<main class="p-4 sm:ml-64">
    <h2 class="text-2xl mb-1.5">Carica una nuova lista di candidati</h2>
    <form on:submit|preventDefault={handle_new_file_submit}>
        <input type="file" name="file" bind:this={fileInput}><br>
        <input class="shadow-neutral-400 " type="submit" value="Upload">
    </form>
    <div class="relative overflow-x-auto shadow-md sm:rounded-lg">
        <table class="w-full text-sm text-left rtl:text-right text-gray-500 dark:text-gray-400">
            <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
            <tr>
                <th scope="col" class="p-4">
                    <div class="flex items-center">
                        <input id="checkbox-all-search" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-all-search" class="sr-only">checkbox</label>
                    </div>
                </th>
                <th scope="col" class="px-6 py-3">
                    Product name
                </th>
                <th scope="col" class="px-6 py-3">
                    Color
                </th>
                <th scope="col" class="px-6 py-3">
                    Category
                </th>
                <th scope="col" class="px-6 py-3">
                    Accessories
                </th>
                <th scope="col" class="px-6 py-3">
                    Available
                </th>
                <th scope="col" class="px-6 py-3">
                    Price
                </th>
                <th scope="col" class="px-6 py-3">
                    Weight
                </th>
                <th scope="col" class="px-6 py-3">
                    Action
                </th>
            </tr>
            </thead>
            <tbody>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-1" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-1" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    Apple MacBook Pro 17"
                </th>
                <td class="px-6 py-4">
                    Silver
                </td>
                <td class="px-6 py-4">
                    Laptop
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    $2999
                </td>
                <td class="px-6 py-4">
                    3.0 lb.
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-2" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-2" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    Microsoft Surface Pro
                </th>
                <td class="px-6 py-4">
                    White
                </td>
                <td class="px-6 py-4">
                    Laptop PC
                </td>
                <td class="px-6 py-4">
                    No
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    $1999
                </td>
                <td class="px-6 py-4">
                    1.0 lb.
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-3" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-3" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    Magic Mouse 2
                </th>
                <td class="px-6 py-4">
                    Black
                </td>
                <td class="px-6 py-4">
                    Accessories
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    No
                </td>
                <td class="px-6 py-4">
                    $99
                </td>
                <td class="px-6 py-4">
                    0.2 lb.
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-3" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-3" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    Apple Watch
                </th>
                <td class="px-6 py-4">
                    Black
                </td>
                <td class="px-6 py-4">
                    Watches
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    No
                </td>
                <td class="px-6 py-4">
                    $199
                </td>
                <td class="px-6 py-4">
                    0.12 lb.
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-3" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-3" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    Apple iMac
                </th>
                <td class="px-6 py-4">
                    Silver
                </td>
                <td class="px-6 py-4">
                    PC
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    $2999
                </td>
                <td class="px-6 py-4">
                    7.0 lb.
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-3" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-3" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    Apple AirPods
                </th>
                <td class="px-6 py-4">
                    White
                </td>
                <td class="px-6 py-4">
                    Accessories
                </td>
                <td class="px-6 py-4">
                    No
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    $399
                </td>
                <td class="px-6 py-4">
                    38 g
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-3" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-3" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    iPad Pro
                </th>
                <td class="px-6 py-4">
                    Gold
                </td>
                <td class="px-6 py-4">
                    Tablet
                </td>
                <td class="px-6 py-4">
                    No
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    $699
                </td>
                <td class="px-6 py-4">
                    1.3 lb.
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-3" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-3" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    Magic Keyboard
                </th>
                <td class="px-6 py-4">
                    Black
                </td>
                <td class="px-6 py-4">
                    Accessories
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    $99
                </td>
                <td class="px-6 py-4">
                    453 g
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-3" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-3" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    Apple TV 4K
                </th>
                <td class="px-6 py-4">
                    Black
                </td>
                <td class="px-6 py-4">
                    TV
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    No
                </td>
                <td class="px-6 py-4">
                    $179
                </td>
                <td class="px-6 py-4">
                    1.78 lb.
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td class="w-4 p-4">
                    <div class="flex items-center">
                        <input id="checkbox-table-search-3" type="checkbox"
                               class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600">
                        <label for="checkbox-table-search-3" class="sr-only">checkbox</label>
                    </div>
                </td>
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    AirTag
                </th>
                <td class="px-6 py-4">
                    Silver
                </td>
                <td class="px-6 py-4">
                    Accessories
                </td>
                <td class="px-6 py-4">
                    Yes
                </td>
                <td class="px-6 py-4">
                    No
                </td>
                <td class="px-6 py-4">
                    $29
                </td>
                <td class="px-6 py-4">
                    53 g
                </td>
                <td class="flex items-center px-6 py-4">
                    <a href="/" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</a>
                    <a href="/" class="font-medium text-red-600 dark:text-red-500 hover:underline ms-3">Remove</a>
                </td>
            </tr>
            </tbody>
        </table>
    </div>
</main>


<!--<h2>Problemi presenti sul server ottimizzabili:</h2>
<form method="post" action="/solve">
    <select name="commissione" id="problem">

    </select>
    <input type="submit">
</form>-->
