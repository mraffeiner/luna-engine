import { writable } from 'svelte/store';

// Interface for user prompt section
export interface UserPromptSection {
	id: string;
	name: string;
	content: string;
}

// Interface for prompt template
export interface PromptTemplateData {
	systemPrompt: string;
	userPromptSections: UserPromptSection[];
}

// Store for prompt template
export const promptName = writable('');
export const systemPrompt = writable('');
export const promptError = writable<string | null>(null);
export const userPromptSections = writable<UserPromptSection[]>([]);
export const userPrompt = writable<string>('');

// Update user prompt whenever the sections change
function updateUserPrompt() {
	let sections: UserPromptSection[] = [];
	userPromptSections.subscribe((value) => {
		sections = value;
	})();

	let text = '';
	if (sections.length > 0) {
		sections.forEach((section) => {
			text += `\n\n# ${section.name}\n${section.content}`;
		});
	}

	userPrompt.set(text);
}

// Subscribe to changes in userPromptSections
userPromptSections.subscribe(() => updateUserPrompt());

// Functions for managing dynamic prompts
export function addDynamicPrompt(name: string, content: string): void {
	if (!name) {
		promptError.set('Please enter a name for the dynamic prompt.');
		return;
	}

	const id = Date.now().toString();
	userPromptSections.update((prompts) => [...prompts, { id, name, content }]);
	promptError.set(null);
}

export function updateDynamicPrompt(id: string, name: string, content: string): void {
	userPromptSections.update((prompts) =>
		prompts.map((p) => (p.id === id ? { ...p, name, content } : p))
	);
}

export function deleteDynamicPrompt(id: string): void {
	userPromptSections.update((prompts) => prompts.filter((p) => p.id !== id));
}

// Functions for managing prompt templates
export function savePromptTemplate(name: string, template: string) {
	if (name) {
		// Save the template and its dynamic prompts
		const saveData: PromptTemplateData = {
			systemPrompt: template,
			userPromptSections: getCurrentUserPromptSections()
		};
		localStorage.setItem(name, JSON.stringify(saveData));
		promptError.set(null);
	} else {
		promptError.set('Please enter a name for the prompt.');
	}
}

export function loadPromptTemplate(name: string) {
	if (name) {
		const loadedData = localStorage.getItem(name);
		if (loadedData !== null) {
			try {
				const parsedData = JSON.parse(loadedData);
				if (parsedData.systemPrompt) {
					systemPrompt.set(parsedData.systemPrompt);
					if (Array.isArray(parsedData.userPromptSections)) {
						userPromptSections.set(parsedData.userPromptSections);
					} else {
						userPromptSections.set([]);
					}
				}
				promptError.set(null);
				promptName.set(name);
			} catch (error) {
				console.error('Error parsing prompt template:', error);
			}
		} else {
			promptError.set(`Prompt "${name}" not found.`);
		}
	}
}

export function deletePromptTemplate(name: string) {
	if (name) {
		localStorage.removeItem(name);
		promptError.set(null);
		systemPrompt.set('');
		promptName.set('');
		userPromptSections.set([]);
	} else {
		promptError.set('No prompt selected to delete.');
	}
}

export function listPromptNames(): string[] {
	const keys: string[] = [];
	for (let i = 0; i < localStorage.length; i++) {
		const key = localStorage.key(i);
		if (key !== null) {
			// Try to parse the value to see if it's a prompt template
			try {
				const value = localStorage.getItem(key);
				if (value) {
					const parsed = JSON.parse(value);
					// If it has systemPrompt or mainTemplate, it's a prompt template
					if (
						typeof parsed === 'object' &&
						('systemPrompt' in parsed || 'mainTemplate' in parsed)
					) {
						keys.push(key);
					}
				}
			} catch (error) {
				console.error('Error parsing prompt template:', error);
				// If it can't be parsed as JSON, it might be an old format prompt
				// or some other data, so we'll include it
				keys.push(key);
			}
		}
	}
	return keys;
}

// Helper function to get current user prompt sections
function getCurrentUserPromptSections(): UserPromptSection[] {
	let result: UserPromptSection[] = [];
	userPromptSections.subscribe((value) => {
		result = value;
	})();
	return result;
}
