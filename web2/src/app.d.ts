// Fix for modules not being found https://github.com/unplugin/unplugin-icons?tab=readme-ov-file#configuration
import 'unplugin-icons/types/svelte'

// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
