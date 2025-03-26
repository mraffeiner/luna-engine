import { get, writable } from 'svelte/store';
import { serviceError } from '../services/docker/dockerService';
import { serviceOutput } from '$lib/shared/shared.svelte';

// Interface for user prompt section
export interface UserPromptSection {
	id: string;
	name: string;
	content: string;
	limit: number;
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
export function addUserPromptSection(name: string, content: string, limit: number): void {
	if (!name) {
		serviceError.set('Please enter a name for the dynamic prompt.');
		return;
	}

	const id = name.toLowerCase().trim().replace(/ /g, '-');
	userPromptSections.update((prompts) => [...prompts, { id, name, content, limit }]);
}

export function updateUserPromptSection(
	id: string,
	name: string | null,
	content: string | null,
	limit: number | null,
	append: boolean = false
): void {
	userPromptSections.update((prompts) => {
		const updatedPrompts = prompts.map((prompt) => {
			if (prompt.id === id) {
				if (name && name !== '') {
					prompt.name = name;
				}
				if (limit && limit >= 0) {
					prompt.limit = limit;
				}
				if (append) {
					// Remove oldest lines when limit is exceeded
					if (prompt.limit > 0 && prompt.content.split('\n').length > 2) {
						const [headline, ...lines] = prompt.content.split('\n');
						let characters = lines.join('\n').length;
						while (characters > prompt.limit) {
							lines.shift();
							characters = lines.join('\n').length;
						}
						prompt.content = headline + '\n\n' + lines.join('\n').trim() + content;
					} else {
						prompt.content += content;
					}
				} else if (content) {
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

export function clearDynamicPromptContent(): void {
	userPromptSections.update((prompts) => {
		const updatedPrompts = prompts.map((prompt) => {
			if (prompt.content.split('\n').length > 2) {
				prompt.content = prompt.content.split('\n')[0] + '\n\n';
			}
			return prompt;
		});
		return updatedPrompts;
	});
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
