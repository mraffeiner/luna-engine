import { writable } from 'svelte/store';
import { serviceError } from '../docker/dockerService';

export interface EngineOptions {
	label: string;
	voices: { value: string; label: string }[];
	languages?: { value: string; label: string }[];
	styles?: { value: string; label: string }[];
}

export interface TtsOptions {
	engines: { [key: string]: EngineOptions };
}

// Request interfaces matching backend models
export interface BaseTtsRequestParams {
	voice: string;
	text: string;
}

export interface AzureTtsRequestParams extends BaseTtsRequestParams {
	engine: 'azure';
	language: string;
	style: string;
	rate: string;
	pitch: string;
}

export interface KokoroTtsRequestParams extends BaseTtsRequestParams {
	engine: 'kokoro';
	language: string;
	speed: number;
	pitch?: number;
}

export interface SesameTtsRequestParams extends BaseTtsRequestParams {
	engine: 'sesame';
}

// Union type for request parameters
export type TtsRequestParams =
	| AzureTtsRequestParams
	| KokoroTtsRequestParams
	| SesameTtsRequestParams;

// Shared store for TTS options
export const ttsOptions = writable<TtsOptions>({
	engines: {}
});

/**
 * Fetches TTS options from the API
 */
export async function fetchTtsOptions(): Promise<void> {
	try {
		const response = await fetch('/api/tts/options');
		if (response.ok) {
			const data = await response.json();
			ttsOptions.set(data);
		} else {
			const errorMsg = `Failed to fetch TTS options: ${response.status} ${response.statusText}`;
			console.error(errorMsg);
			serviceError.set(errorMsg);
		}
	} catch (error) {
		const errorMsg = `Error fetching TTS options: ${error}`;
		console.error(errorMsg);
		serviceError.set(errorMsg);
	}
}

/**
 * Generates speech using the TTS API
 */
export async function generateSpeech(params: TtsRequestParams): Promise<Blob | null> {
	try {
		const response = await fetch('/api/tts/generate', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(params)
		});

		if (response.ok) {
			return await response.blob();
		} else {
			const errorMsg = `Error generating speech: ${response.status} ${response.statusText}`;
			serviceError.set(errorMsg);
			return null;
		}
	} catch (error) {
		const errorMsg = `Error generating speech: ${error}`;
		serviceError.set(errorMsg);
		return null;
	}
}
