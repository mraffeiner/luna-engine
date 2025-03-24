import { writable } from 'svelte/store';

export const promptOutput = writable<{ systemPrompt: string; userPrompt: string } | null>(null);
export const llmOutput = writable<string | null>(null);
export const ttsOutput = writable<{ audioBlob: Blob; audioUrl: string } | null>(null);
export const discordOutput = writable<{
	username: string;
	audioBlob: Blob;
	audioUrl: string;
} | null>(null);
export const sttOutput = writable<string | null>(null);
