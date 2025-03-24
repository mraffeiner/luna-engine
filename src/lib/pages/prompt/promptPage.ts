import { get, writable } from 'svelte/store';
import { serviceError } from '../services/docker/dockerService';
import { serviceOutput } from '$lib/shared/shared.svelte';

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
export const userPrompt = writable('');
export const userPromptSections = writable<UserPromptSection[]>([]);

systemPrompt.subscribe((content) => (serviceOutput.prompt.system = content));
userPromptSections.subscribe((sections) => {
	let content = '';
	if (sections.length > 0) {
		sections.forEach((section) => {
			content += `\n\n# ${section.name}\n${section.content}`;
		});
	}

	userPrompt.set(content);
	serviceOutput.prompt.user = content;
});

// Functions for managing user prompt sections
export function addUserPromptSection(name: string, content: string): void {
	if (!name) {
		serviceError.set('Please enter a name for the dynamic prompt.');
		return;
	}

	const id = name.toLowerCase().trim().replace(/ /g, '-');
	userPromptSections.update((prompts) => [...prompts, { id, name, content }]);
	serviceError.set(null);
}

export function updateUserPromptSection(
	id: string,
	name: string | null,
	content: string,
	append: boolean = false
): void {
	userPromptSections.update((prompts) => {
		const updatedPrompts = prompts.map((prompt) => {
			if (prompt.id === id) {
				if (name) {
					prompt.name = name;
				}
				if (append) {
					prompt.content += content;
				} else {
					prompt.content = content;
				}
			}
			return prompt;
		});
		return updatedPrompts;
	});
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
			userPromptSections: get(userPromptSections)
		};
		localStorage.setItem(name, JSON.stringify(saveData));
		serviceError.set(null);
	} else {
		serviceError.set('Please enter a name for the prompt.');
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
				serviceError.set(null);
				templateName.set(name);
			} catch (error) {
				console.error('Error parsing prompt template:', error);
			}
		} else {
			serviceError.set(`Prompt "${name}" not found.`);
		}
	}
}

export function deleteTemplate(name: string) {
	if (name) {
		localStorage.removeItem(name);
		serviceError.set(null);
		systemPrompt.set('');
		templateName.set('');
		userPromptSections.set([]);
	} else {
		serviceError.set('No prompt selected to delete.');
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
