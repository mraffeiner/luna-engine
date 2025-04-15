import { writable } from 'svelte/store';
import { serviceError } from '../docker/dockerService';

export interface LlmParams {
	requestParams: {
		provider: string;
		model: string;
		system_prompt: string;
		prompt: string;
	};
}

export const models = writable<{ provider: string; id: string; name: string }[]>([]);

export const selectedResponseLlm = writable<LlmParams>({
	requestParams: {
		provider: '',
		model: '',
		system_prompt: '',
		prompt: ''
	}
});

export const selectedPrepassLlm = writable<LlmParams>({
	requestParams: {
		provider: 'groq',
		model: 'meta-llama/llama-4-scout-17b-16e-instruct',
		system_prompt: '',
		prompt: ''
	}
});

export const loading = writable(false);

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

export async function generateResponse(params: LlmParams): Promise<string | undefined> {
	loading.set(true);
	try {
		const response = await fetch('/api/llm/generate', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(params.requestParams)
		});

		if (response.ok && response.body) {
			const reader = response.body.getReader();
			const decoder = new TextDecoder();

			let responseText = '';
			while (true) {
				const { done, value } = await reader.read();
				if (done) {
					break;
				} else {
					responseText += decoder.decode(value, { stream: true });
				}
			}
			return responseText;
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
