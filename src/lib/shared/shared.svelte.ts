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
	hasNewMessages: boolean;
	waiting: boolean;
	paused: boolean;
} = $state({
	thinking: false,
	speaking: false,
	hasNewMessages: false,
	waiting: false,
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
	llm: { raw: string; prepass: string };
	tts: { blob: Blob | undefined; url: string };
	discord: SvelteMap<string, { blob: Blob; url: string }>;
	stt: { username: string; transcript: string }[];
	chat: ChatMessage[];
} = $state({
	prompt: { system: '', user: '' },
	llm: { raw: '', prepass: '' },
	tts: { blob: undefined, url: '' },
	discord: new SvelteMap(),
	stt: [],
	chat: []
});

export const speakerAudio: SvelteMap<string, string> = $state(new SvelteMap());
