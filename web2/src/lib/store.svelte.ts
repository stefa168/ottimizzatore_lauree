import {persisted} from "svelte-persisted-store";

export let debugEnabled = persisted("debugEnabled", false);