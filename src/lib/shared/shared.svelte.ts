import { SvelteMap } from 'svelte/reactivity';
import { PAGES } from './constants';

export const currentPage = $state({
	id: PAGES[0].id,
	name: PAGES[0].name
});

export const containerStatus: SvelteMap<
	string,
	'RUNNING' | 'STOPPED' | 'STARTING' | 'STOPPING' | 'UNKNOWN'
> = new SvelteMap();

export const engineConfig = $state({
	auto: false
});

export const forwardOutput = $state({
	prompt: true,
	llm: true,
	tts: true,
	discord: true,
	stt: true
});

export const speakerAudio: SvelteMap<string, string> = $state(new SvelteMap());
