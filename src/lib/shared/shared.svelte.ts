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

export const engineConfig: {
	auto: boolean;
} = $state({
	auto: false
});

export const lunaState = $state({
	listening: false,
	thinking: false,
	talking: false,
	waiting: true
});

export const receiveInput = $state({
	prompt: true,
	llm: true,
	tts: true,
	discord: true,
	stt: true
});

export const serviceOutput: {
	prompt: { system: string; user: string };
	llm: string;
	tts: { blob: Blob | undefined; url: string } | undefined;
	discord: SvelteMap<string, { blob: Blob; url: string }>;
	stt: string;
} = $state({
	prompt: { system: '', user: '' },
	llm: '',
	tts: { blob: undefined, url: '' },
	discord: new SvelteMap(),
	stt: ''
});

export const speakerAudio: SvelteMap<string, string> = $state(new SvelteMap());
