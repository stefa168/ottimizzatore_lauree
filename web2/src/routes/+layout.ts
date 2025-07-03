import type {LayoutLoad} from "./$types";
import {QueryClient} from "@tanstack/svelte-query";
import {browser} from "$app/environment";

// https://tanstack.com/query/v5/docs/framework/svelte/ssr#using-prefetchquery
export const load: LayoutLoad = async () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        enabled: browser
      }
    }
  });

  return {queryClient};
}