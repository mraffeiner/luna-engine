import { SvelteMap } from 'svelte/reactivity';
import { PAGES } from './constants';
import type { ChatMessage } from '$lib/pages/services/chat/chatService';

export const currentPage = $state({
	id: PAGES[0].id,
	name: PAGES[0].name
});

export type ContainerStatus = 'RUNNING' | 'STOPPED' | 'STARTING' | 'STOPPING' | 'UNKNOWN';

export const containerStatus: SvelteMap<string, ContainerStatus> = new SvelteMap();

export type EngineMode = 'AUTO' | 'REACT';

export const engineConfig: {
	mode: EngineMode;
	interruptable: boolean;
	llmPrepass: boolean;
	msMinAfterResponse: number;
} = $state({
	mode: 'REACT',
	llmPrepass: true,
	interruptable: false,
	msMinAfterResponse: 0
});

export const engineStates: {
	thinking: boolean;
	speaking: boolean;
	listening: boolean;
	reading: boolean;
	waiting: boolean;
	hasNewMessages: boolean; // REVIEW: Should probably be handled differently
	busy: boolean;
	paused: boolean;
	reset: () => void;
} = $state({
	thinking: false,
	speaking: false,
	reading: false,
	listening: false,
	waiting: true,
	hasNewMessages: false,
	busy: false,
	paused: true,
	reset: () => {
		engineStates.paused = true;
		engineStates.waiting = false;
		engineStates.thinking = false;
		engineStates.speaking = false;
		engineStates.reading = false;
		engineStates.listening = false;
		engineStates.busy = false;
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
	llm: { raw: string; normalized: string; final: string };
	tts: { blob: Blob | undefined; url: string };
	discord: SvelteMap<string, { blob: Blob; url: string }>;
	stt: { username: string; transcript: string }[];
	chat: ChatMessage[];
} = $state({
	prompt: { system: '', user: '' },
	llm: { raw: '', normalized: '', final: '' },
	tts: { blob: undefined, url: '' },
	discord: new SvelteMap(),
	stt: [],
	chat: []
});

export const speakerAudio: SvelteMap<string, string> = $state(new SvelteMap());
