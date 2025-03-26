import { serviceOutput } from '$lib/shared/shared.svelte';
import { normalizeLlmResponse } from '$lib/shared/utils';
import { get, writable } from 'svelte/store';
import { serviceError } from '../docker/dockerService';

export interface LlmParams {
	requestParams: {
		provider: string;
		model: string;
		system_prompt: string;
		prompt: string;
	};
	isReasoning: boolean;
}

export const models = writable<
	{ provider: string; id: string; name: string; isReasoning: boolean }[]
>([]);

export const selectedLlm = writable<LlmParams>({
	requestParams: {
		provider: '',
		model: '',
		system_prompt: '',
		prompt: ''
	},
	isReasoning: false
});

export const loading = writable(false);
export const responseText = writable('');

export async function fetchModels() {
	try {
		const response = await fetch('/api/llm/models');
		if (response.ok) {
			const data = await response.json();
			models.set(data);
		} else {
			console.error('Failed to fetch LLM options:', response.status, response.statusText);
			serviceError.set(`Failed to fetch LLM options: ${response.status} ${response.statusText}`);
		}
	} catch (error) {
		console.error('Error fetching LLM options:', error);
		serviceError.set(`Error fetching LLM options: ${error}`);
	}
}

export async function generateResponse() {
	loading.set(true);
	try {
		responseText.set('');
		const response = await fetch('/api/llm/generate', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(get(selectedLlm).requestParams)
		});

		if (response.ok && response.body) {
			const reader = response.body.getReader();
			const decoder = new TextDecoder();

			while (true) {
				const { done, value } = await reader.read();
				if (done) {
					break;
				} else {
					responseText.update((text) => text + decoder.decode(value, { stream: true }));
				}
			}
			// Clean response when done
			serviceOutput.llm = normalizeLlmResponse(
				get(responseText),
				get(selectedLlm).isReasoning,
				'Luna:'
			);
		} else {
			serviceError.set(`Error generating response: ${response.status} ${response.statusText}`);
		}
	} catch (error) {
		serviceError.set(`Error generating response: ${error}`);
		throw error;
	} finally {
		loading.set(false);
	}
}
