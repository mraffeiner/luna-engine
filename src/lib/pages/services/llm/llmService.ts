import { normalizeLlmResponse } from '$lib/shared/utils';
import { writable } from 'svelte/store';
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

export const selectedResponseLlm = writable<LlmParams>({
	requestParams: {
		provider: '',
		model: '',
		system_prompt: '',
		prompt: ''
	},
	isReasoning: false
});

export const selectedPrepassLlm = writable<LlmParams>({
	requestParams: {
		provider: 'groq',
		model: 'llama-3.3-70b-specdec',
		system_prompt:
			'You are a text processing tool to prepare llm responses for text-to-speech. Take the text and clean it up. Remove stutters with short repititions. Replace stage directions with compatible utterances or em dashes. Replace descriptions with logical verbal reactions or follow-up explanations of what happened. Replace code blocks or markdown with verbally communicated information. Ensure that the final response retains the character and meaning of the original. Respond with just the cleaned up text and nothing else',
		prompt: ''
	},
	isReasoning: false
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
			// Clean response when done
			const llmOutput = normalizeLlmResponse(responseText, params.isReasoning, 'Luna:');
			return llmOutput;
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
