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
	llmPrepass: boolean;
	msMinAfterResponse: number;
} = $state({
	mode: 'REACT',
	llmPrepass: true,
	msMinAfterResponse: 1000
});

export const engineStates: {
	thinking: boolean;
	speaking: boolean;
	listening: boolean;
	waiting: boolean;
	hasNewMessages: boolean;
	busy: boolean;
	paused: boolean;
} = $state({
	thinking: false,
	speaking: false,
	listening: false,
	waiting: true,
	hasNewMessages: false,
	busy: false,
	paused: true
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
