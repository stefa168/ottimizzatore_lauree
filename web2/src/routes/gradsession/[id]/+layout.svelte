<script lang="ts">
  import MdiInformationVariantBoxOutline from '~icons/mdi/information-variant-box-outline'
  import NimbusUniversity from '~icons/nimbus/university'
  import MaterialSymbolsPersonPin from '~icons/material-symbols/person-pin'
  import MageRobotUwuFill from '~icons/mage/robot-uwu-fill'
  import MdiCogOutline from '~icons/mdi/cog-outline'
  import RadixIconsArchive from '~icons/radix-icons/archive'

  import type {Component} from "svelte";
  import type {SvelteHTMLElements} from "svelte/elements";
  import type {LayoutProps} from "./$types";
  import {page} from '$app/state';
  import {setSessionData} from "../SessionData.svelte";
  import EditableSessionTitle from "./EditableSessionTitle.svelte";
  import {getSession, getSessionProfessors, getSessionStudents} from "@/api/sessions.remote";

  let {children, params}: LayoutProps = $props();
  const sessionId = $derived(Number(params.id));

  // The context must be set before the first `await`, otherwise the child routes can't see it. Its getters are only
  // read by the markup below, which waits for the queries (see the {#if}), and they follow the queries when refreshed.
  let sessionData = setSessionData({
    get session() {
      return session;
    },
    get students() {
      return students;
    },
    get professors() {
      return professors;
    },
  });

  const session = $derived(await getSession(sessionId));
  const students = $derived(await getSessionStudents(sessionId));
  const professors = $derived(await getSessionProfessors(sessionId));

  type Section = { label: string, slug: string, path?: string, icon?: Component<SvelteHTMLElements['svg']> };
  const sections: Section[] = [
    {label: 'Informazioni', slug: 'info', path: '', icon: MdiInformationVariantBoxOutline},
    {label: 'Studenti Candidati', slug: 'candidates', icon: NimbusUniversity},
    {label: 'Docenti della Sessione', slug: 'professors', icon: MaterialSymbolsPersonPin},
    {label: 'Ottimizzazione', slug: 'optimization', icon: MageRobotUwuFill},
    {label: 'Configurazione Aperta', slug: 'conf', icon: MdiCogOutline}
  ];

  const currentSection = $derived(page.url.pathname.split('/').at(3) ?? 'info');
  const isConfigOpen = $derived(page.url.pathname.split('/').at(4) !== undefined)
</script>

{#snippet tab(url: String | URL, section: Section, selected: Boolean)}
  <li class={[section.slug === 'conf' && (isConfigOpen ? 'visible' : 'hidden')]}>
    <a href={url.toString()}
       class={[
                 "inline-flex items-center justify-center p-4 px-2 border-b-2 border-transparent rounded-t-lg hover:cursor-pointer hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300 group transition-all ease-in-out duration-150",
                 selected && '!text-primary !border-primary'
               ]}>
      {#if section.icon}
        <section.icon class="w-4 h-4 me-2"/>
      {/if}
      <span>{section.label}</span>
    </a>
  </li>
{/snippet}

<!-- Referencing the awaited values makes the whole layout wait for them -->
{#if session && students && professors}
<div class="container mx-auto pb-10">
  {#if session.archived}
    <div class="mt-4 flex items-center gap-2 rounded-md border px-4 py-2 text-sm text-muted-foreground" role="status">
      <RadixIconsArchive class="size-4"/>
      Questa sessione è archiviata. Può essere ripristinata tra le sessioni attive dalla pagina
      <a href="/archive" class="text-blue-500 hover:underline">Sessioni Archiviate</a>.
    </div>
  {/if}
  <EditableSessionTitle {sessionData}/>

  <!-- Styles from https://flowbite.com/docs/components/tabs/ -->
  <!-- Tabs Root -->
  <div class="border-b border-gray-200 dark:border-gray-700 mb-4">
    <!-- Tabs List -->
    <ul class="flex flex-wrap -mb-px text-sm font-medium text-center text-gray-500 dark:text-gray-400">
      {#each sections as section}
        {@const
          url = section.slug !== 'conf' ?
          `/gradsession/${sessionId}/${section.path ?? section.slug}` :
          page.url
        }
        {@render tab(url, section, !isConfigOpen && currentSection === section.slug || isConfigOpen && section.slug === 'conf')}
      {/each}
    </ul>
  </div>

  {@render children?.()}
</div>
{/if}
