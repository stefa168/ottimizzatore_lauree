<script lang="ts">
    export let orientation: 'horizontal' | 'vertical' = 'horizontal';
    const o = orientation === 'vertical' ? 'vertical' : 'horizontal';
</script>

<div aria-orientation={o}
     class="inline-flex w-fit
            flex-col:[aria-orientation='vertical'] flex-row:[aria-orientation='horizontal']
            [&>*]:rounded-none
            [&>*]:-ml-px first:[&>*]:ml-0
            [&>*]:border-s-0 first:[&>*]:border
            [&>*]:first:rounded-s-md [&>*]:last:rounded-e-md
            [aria-orientation='vertical']:[&>*]:-mt-px
            [aria-orientation='vertical']:[&>*]:border-t-0
            [aria-orientation='vertical']:[&>*]:first:rounded-t-md
            [aria-orientation='vertical']:[&>*]:last:rounded-b-md">
    <slot />
</div>
