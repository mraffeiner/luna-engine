import { get, writable } from 'svelte/store';
import { serviceError } from '../docker/dockerService';
import { serviceOutput } from '$lib/shared/shared.svelte';
import type { TTS_ENGINES } from '$lib/shared/constants';

export type TtsEngine = (typeof TTS_ENGINES)[number];

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
	engine: TtsEngine;
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

export type TtsParams = {
	requestParams: TtsRequestParams;
};

// Shared store for TTS options
export const ttsOptions = writable<TtsOptions>({
	engines: {}
});

export const selectedTts = writable<TtsParams>();

export const loading = writable(false);
export const ttsAudioUrl = writable('');

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
			serviceError.set(`Failed to fetch TTS options: ${response.status} ${response.statusText}`);
		}
	} catch (error) {
		serviceError.set(`Error fetching TTS options: ${error}`);
	}
}

/**
 * Generates speech using the TTS API
 */
export async function generateSpeech(
	params: TtsParams
): Promise<{ blob: Blob; url: string } | undefined> {
	loading.set(true);
	try {
		if (get(ttsAudioUrl)) {
			URL.revokeObjectURL(get(ttsAudioUrl));
		}

		const response = await fetch('/api/tts/generate', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(params.requestParams)
		});

		if (response.ok) {
			const audioBlob = await response.blob();
			if (audioBlob) {
				ttsAudioUrl.set(URL.createObjectURL(audioBlob));

				const ttsOutput = { blob: audioBlob, url: get(ttsAudioUrl) };
				serviceOutput.tts = ttsOutput;
				return ttsOutput;
			}
		} else {
			serviceError.set(`Error generating speech: ${response.status} ${response.statusText}`);
		}
	} catch (error) {
		serviceError.set(`Error generating speech: ${error}`);
		throw error;
	} finally {
		loading.set(false);
	}
}
