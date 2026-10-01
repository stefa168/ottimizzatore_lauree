import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	compilerOptions: {
		experimental: {
			// Lets components `await` remote queries directly
			async: true
		}
	},

	kit: {
		alias: {
			"@/*": "./src/lib/*"
		},
		// adapter-auto only supports some environments, see https://svelte.dev/docs/kit/adapter-auto for a list.
		// If your environment is not supported, or you settled on a specific environment, switch out the adapter.
		// See https://svelte.dev/docs/kit/adapters for more information about adapters.
		adapter: adapter(),
		experimental: {
			// All backend calls go through remote functions (src/lib/api/*.remote.ts)
			remoteFunctions: true,
			// Errors thrown while rendering (e.g. a remote query returning 404) show the +error page, also on the server
			handleRenderingErrors: true
		}
	}
};

export default config;
