import { writable } from 'svelte/store';

export const promptName = writable('');
export const promptTemplate = writable('');
export const promptError = writable<string | null>(null);
export const dynamicPrompt = writable<string>('');

export function savePromptTemplate(name: string, template: string) {
	if (name) {
		localStorage.setItem(name, template);
		promptError.set(null);
	} else {
		promptError.set('Please enter a name for the prompt.');
	}
}

export function loadPromptTemplate(name: string) {
	if (name) {
		const loadedTemplate = localStorage.getItem(name);
		if (loadedTemplate !== null) {
			promptTemplate.set(loadedTemplate);
			promptError.set(null);
			promptName.set(name);
		} else {
			promptError.set(`Prompt "${name}" not found.`);
		}
	}
}

export function deletePromptTemplate(name: string) {
	if (name) {
		localStorage.removeItem(name);
		promptError.set(null);
		promptTemplate.set('');
		promptName.set('');
	} else {
		promptError.set('No prompt selected to delete.');
	}
}

export function listPromptNames(): string[] {
	const keys: string[] = [];
	for (let i = 0; i < localStorage.length; i++) {
		const key = localStorage.key(i);
		if (key !== null) {
			keys.push(key);
		}
	}
	return keys;
}

export async function fetchDynamicPrompt(): Promise<void> {
	try {
		const response = await fetch('/api/prompt/prompt');
		if (response.ok) {
			const data = await response.json();
			dynamicPrompt.set(data.prompt);
		} else {
			const errorMsg = `Failed to fetch dynamic prompt: ${response.status} ${response.statusText}`;
			console.error(errorMsg);
			promptError.set(errorMsg);
		}
	} catch (error) {
		const errorMsg = `Error fetching dynamic prompt: ${error}`;
		console.error(errorMsg);
		promptError.set(errorMsg);
	}
}
