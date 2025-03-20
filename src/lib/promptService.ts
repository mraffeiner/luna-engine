import { writable } from 'svelte/store';

// Interface for user prompt section
export interface UserPromptSection {
	id: string;
	name: string;
	content: string;
}

// Interface for prompt template
export interface TemplateData {
	systemPrompt: string;
	userPromptSections: UserPromptSection[];
}

// Store for prompt template
export const templateName = writable('');
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

// Functions for managing user prompt sections
export function addUserPromptSection(name: string, content: string): void {
	if (!name) {
		promptError.set('Please enter a name for the dynamic prompt.');
		return;
	}

	const id = Date.now().toString();
	userPromptSections.update((prompts) => [...prompts, { id, name, content }]);
	promptError.set(null);
}

export function updateUserPromptSection(id: string, name: string, content: string): void {
	userPromptSections.update((prompts) =>
		prompts.map((p) => (p.id === id ? { ...p, name, content } : p))
	);
}

export function deleteUserPromptSection(id: string): void {
	userPromptSections.update((prompts) => prompts.filter((p) => p.id !== id));
}

// Functions for managing prompt templates
export function saveTemplate(name: string, template: string) {
	if (name) {
		// Save the template and its dynamic prompts
		const saveData: TemplateData = {
			systemPrompt: template,
			userPromptSections: getCurrentUserPromptSections()
		};
		localStorage.setItem(name, JSON.stringify(saveData));
		promptError.set(null);
	} else {
		promptError.set('Please enter a name for the prompt.');
	}
}

export function loadTemplate(name: string) {
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
				templateName.set(name);
			} catch (error) {
				console.error('Error parsing prompt template:', error);
			}
		} else {
			promptError.set(`Prompt "${name}" not found.`);
		}
	}
}

export function deleteTemplate(name: string) {
	if (name) {
		localStorage.removeItem(name);
		promptError.set(null);
		systemPrompt.set('');
		templateName.set('');
		userPromptSections.set([]);
	} else {
		promptError.set('No prompt selected to delete.');
	}
}

export function listTemplateNames(): string[] {
	const keys: string[] = [];
	for (let i = 0; i < localStorage.length; i++) {
		const key = localStorage.key(i);
		if (key !== null) {
			// Try to parse the value to see if it's a prompt template
			try {
				const value = localStorage.getItem(key);
				if (value) {
					const parsed = JSON.parse(value);
					// If it has systemPrompt, it's a prompt template
					if (typeof parsed === 'object' && 'systemPrompt' in parsed) {
						keys.push(key);
					}
				}
			} catch (error) {
				console.error('Error parsing prompt template:', error);
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
