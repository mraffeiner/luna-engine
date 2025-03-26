import { SvelteMap } from 'svelte/reactivity';
import { PAGES } from './constants';

export const currentPage = $state({
	id: PAGES[0].id,
	name: PAGES[0].name
});

export type ContainerStatus = 'RUNNING' | 'STOPPED' | 'STARTING' | 'STOPPING' | 'UNKNOWN';

export const containerStatus: SvelteMap<string, ContainerStatus> = new SvelteMap();

export type EngineMode = 'AUTO' | 'REACT' | 'WAIT';

export const engineConfig: {
	mode: EngineMode;
} = $state({
	mode: 'AUTO'
});

export const engineState: {
	thinking: boolean;
	speaking: boolean;
	hasNewMessages: boolean;
	paused: boolean;
	reset: () => void;
} = $state({
	thinking: false,
	speaking: false,
	hasNewMessages: false,
	paused: true,
	reset: () => {
		engineState.thinking = false;
		engineState.speaking = false;
		engineState.hasNewMessages = false;
		engineState.paused = true;
	}
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
	stt: string;
	chat: string;
} = $state({
	prompt: { system: '', user: '' },
	llm: '',
	tts: { blob: undefined, url: '' },
	discord: new SvelteMap(),
	stt: '',
	chat: ''
});

export const speakerAudio: SvelteMap<string, string> = $state(new SvelteMap());
