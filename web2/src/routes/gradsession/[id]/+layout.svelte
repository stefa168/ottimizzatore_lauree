<script lang="ts">
  import MdiInformationVariantBoxOutline from '~icons/mdi/information-variant-box-outline'
  import NimbusUniversity from '~icons/nimbus/university'
  import MaterialSymbolsPersonPin from '~icons/material-symbols/person-pin'
  import MageRobotUwuFill from '~icons/mage/robot-uwu-fill'

  import type {Component} from "svelte";
  import type {SvelteHTMLElements} from "svelte/elements";
  import type {LayoutProps} from "./$types";
  import {page} from '$app/state';
  import {setSessionData} from "../SessionData.svelte";

  let {children, data}: LayoutProps = $props();
  let sessionData = setSessionData(data.session, data.student_entries, data.professors);

  type Section = { label: string, slug: string, path?: string, icon: Component<SvelteHTMLElements['svg']> };
  const sections: Section[] = [
    {label: 'Informazioni', slug: 'info', path: '', icon: MdiInformationVariantBoxOutline},
    {label: 'Studenti Candidati', slug: 'candidates', icon: NimbusUniversity},
    {label: 'Docenti della Sessione', slug: 'professors', icon: MaterialSymbolsPersonPin},
    {label: 'Ottimizzazione', slug: 'optimization', icon: MageRobotUwuFill},
  ];

  let currentSection = $derived(page.url.pathname.split('/').at(3) ?? 'info');
</script>

<div class="container mx-auto pb-10">
  <h1 class="text-2xl mb-4 font-medium">{sessionData.session.title}</h1>

  <!-- Styles from https://flowbite.com/docs/components/tabs/ -->
  <!-- Tabs Root -->
  <div class="border-b border-gray-200 dark:border-gray-700 mb-4">
    <!-- Tabs List -->
    <ul class="flex flex-wrap -mb-px text-sm font-medium text-center text-gray-500 dark:text-gray-400">
      {#each sections as section}
        <li>
          <a href={`/gradsession/${data.session_id}/${section.path ?? section.slug}`}
             data-active={currentSection === section.slug}
             class="inline-flex items-center justify-center p-4 px-2 border-b-2 border-transparent rounded-t-lg hover:cursor-pointer hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300 group data-[active=true]:text-primary data-[active=true]:border-primary transition-all ease-in-out duration-150">
            <section.icon class="w-4 h-4 me-2"/>
            <span>{section.label}</span>
          </a>
        </li>
      {/each}
    </ul>
  </div>

  {@render children?.()}
</div>