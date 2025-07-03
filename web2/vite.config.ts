import tailwindcss from '@tailwindcss/vite';
import {sveltekit} from '@sveltejs/kit/vite';
import {defineConfig} from 'vite';
import Icons from 'unplugin-icons/vite'
import {paraglideVitePlugin} from '@inlang/paraglide-js';

export default defineConfig({
    plugins: [
        tailwindcss(),
        sveltekit(),
        Icons({
            compiler: 'svelte',
            autoInstall: true
        }),
        paraglideVitePlugin({
            project: './project.inlang',
            outdir: './src/lib/paraglide'
        })
    ]
});
