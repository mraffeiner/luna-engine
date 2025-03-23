import { SvelteMap } from 'svelte/reactivity';

export const currentPage = $state({
	id: 'home',
	name: 'Control Panel'
});

export const containerStatus: SvelteMap<
	string,
	'RUNNING' | 'STOPPED' | 'STARTING' | 'STOPPING' | 'UNKNOWN'
> = new SvelteMap();
