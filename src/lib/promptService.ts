import { writable } from 'svelte/store';

// Interface for dynamic prompt
export interface DynamicPrompt {
	id: string;
	name: string;
	content: string;
}

// Interface for prompt template
export interface PromptTemplateData {
	mainTemplate: string;
	dynamicPrompts: DynamicPrompt[];
}

// Store for prompt template
export const promptName = writable('');
export const promptTemplate = writable('');
export const promptError = writable<string | null>(null);
export const dynamicPrompts = writable<DynamicPrompt[]>([]);
export const combinedPrompt = writable<string>('');

// Update combined prompt whenever the template or dynamic prompts change
function updateCombinedPrompt() {
	let dynamicPromptsArray: DynamicPrompt[] = [];
	dynamicPrompts.subscribe((value) => {
		dynamicPromptsArray = value;
	})();

	let mainTemplate = '';
	promptTemplate.subscribe((value) => {
		mainTemplate = value;
	})();

	let combined = mainTemplate;

	if (dynamicPromptsArray.length > 0) {
		dynamicPromptsArray.forEach((dp) => {
			combined += `\n\n# ${dp.name}\n${dp.content}\n`;
		});
	}

	combinedPrompt.set(combined);
}

// Subscribe to changes in promptTemplate and dynamicPrompts
promptTemplate.subscribe(() => updateCombinedPrompt());
dynamicPrompts.subscribe(() => updateCombinedPrompt());

// Functions for managing dynamic prompts
export function addDynamicPrompt(name: string, content: string): void {
	if (!name) {
		promptError.set('Please enter a name for the dynamic prompt.');
		return;
	}

	const id = Date.now().toString();
	dynamicPrompts.update((prompts) => [...prompts, { id, name, content }]);
	promptError.set(null);
}

export function updateDynamicPrompt(id: string, name: string, content: string): void {
	dynamicPrompts.update((prompts) =>
		prompts.map((p) => (p.id === id ? { ...p, name, content } : p))
	);
}

export function deleteDynamicPrompt(id: string): void {
	dynamicPrompts.update((prompts) => prompts.filter((p) => p.id !== id));
}

// Functions for managing prompt templates
export function savePromptTemplate(name: string, template: string) {
	if (name) {
		// Save the template and its dynamic prompts
		const saveData: PromptTemplateData = {
			mainTemplate: template,
			dynamicPrompts: getCurrentDynamicPrompts()
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

				// Check if it's the new format with dynamic prompts
				if (typeof parsedData === 'object' && parsedData.mainTemplate) {
					promptTemplate.set(parsedData.mainTemplate);
					if (Array.isArray(parsedData.dynamicPrompts)) {
						dynamicPrompts.set(parsedData.dynamicPrompts);
					} else {
						dynamicPrompts.set([]);
					}
				} else {
					// Handle legacy format (just a string)
					promptTemplate.set(parsedData);
					dynamicPrompts.set([]);
				}

				promptError.set(null);
				promptName.set(name);
			} catch (error) {
				// If parsing fails, assume it's the old format (just a string)
				console.error('Error parsing prompt template:', error);
				promptTemplate.set(loadedData);
				promptName.set(name);
				dynamicPrompts.set([]);
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
		promptTemplate.set('');
		promptName.set('');
		dynamicPrompts.set([]);
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
					// If it has mainTemplate or is a string, it's a prompt template
					if (typeof parsed === 'object' && 'mainTemplate' in parsed) {
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

// Helper function to get current dynamic prompts
function getCurrentDynamicPrompts(): DynamicPrompt[] {
	let result: DynamicPrompt[] = [];
	dynamicPrompts.subscribe((value) => {
		result = value;
	})();
	return result;
}
