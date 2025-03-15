import { writable } from 'svelte/store';

export const llmOutput = writable<string | null>(null);
export const sttOutput = writable<string | null>(null);
