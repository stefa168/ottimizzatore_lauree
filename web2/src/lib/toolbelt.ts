// https://github.com/huntabyte/svelte-toolbelt/blob/main/src/lib/types.ts#L15
export type Expand<T> = T extends infer U ? { [K in keyof U]: U[K] } : never;