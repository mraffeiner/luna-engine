import { writable } from 'svelte/store';

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

export interface VoiceWeight {
	voice: string;
	weight: number;
}

export interface KokoroTtsRequestParams extends BaseTtsRequestParams {
	engine: 'kokoro';
	language: string;
	speed: number;
	pitch?: number;
	voiceMix?: VoiceWeight[];
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

// Shared store for error messages
export const ttsError = writable<string | null>(null);

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
			ttsError.set(errorMsg);
		}
	} catch (error) {
		const errorMsg = `Error fetching TTS options: ${error}`;
		console.error(errorMsg);
		ttsError.set(errorMsg);
	}
}

/**
 * Generates speech using the TTS API
 */
export async function generateSpeech(params: TtsRequestParams): Promise<Blob | null> {
	try {
		// Process voice mix for Kokoro if present
		if (params.engine === 'kokoro') {
			const kokoroParams = params as KokoroTtsRequestParams;
			const voiceMix = kokoroParams.voiceMix;

			// Format voice string as "voice1:weight1+voice2:weight2+..."
			if (voiceMix && voiceMix.length > 0) {
				kokoroParams.voice = voiceMix.map((v) => `${v.voice}(${v.weight})`).join('+');
			}
		}

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
			ttsError.set(errorMsg);
			return null;
		}
	} catch (error) {
		const errorMsg = `Error generating speech: ${error}`;
		ttsError.set(errorMsg);
		return null;
	}
}
