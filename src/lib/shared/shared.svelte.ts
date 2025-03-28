import { SvelteMap } from 'svelte/reactivity';
import { PAGES } from './constants';

export const currentPage = $state({
	id: PAGES[0].id,
	name: PAGES[0].name
});

export type ContainerStatus = 'RUNNING' | 'STOPPED' | 'STARTING' | 'STOPPING' | 'UNKNOWN';

export const containerStatus: SvelteMap<string, ContainerStatus> = new SvelteMap();

export type EngineMode = 'AUTO' | 'REACT' | 'PAUSED';

export const engineConfig: {
	mode: EngineMode;
	msMinAfterResponse: number;
	msMinAfterError: number;
} = $state({
	mode: 'PAUSED',
	msMinAfterResponse: 1000,
	msMinAfterError: 5000
});

export const engineStates: {
	thinking: boolean;
	speaking: boolean;
	hasNewMessages: boolean;
	waiting: boolean;
} = $state({
	thinking: false,
	speaking: false,
	hasNewMessages: false,
	waiting: false
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
	tts: { blob: Blob | undefined; url: string };
	discord: SvelteMap<string, { blob: Blob; url: string }>;
	stt: SvelteMap<string, string>;
	chat: string;
} = $state({
	prompt: { system: '', user: '' },
	llm: '',
	tts: { blob: undefined, url: '' },
	discord: new SvelteMap(),
	stt: new SvelteMap(),
	chat: ''
});

export const speakerAudio: SvelteMap<string, string> = $state(new SvelteMap());
