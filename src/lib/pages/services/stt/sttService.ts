import { writable, derived } from 'svelte/store'; // Import derived
import { serviceError } from '../docker/dockerService';
import { serviceOutput } from '$lib/shared/shared.svelte';

export interface SttResponse {
	text: string;
}

export interface SttModel {
	value: string;
	label: string;
}

// Shared stores
export const activeTranscriptions = writable(0); // Counter store
export const loading = derived(activeTranscriptions, ($count) => $count > 0); // Derived loading state
export const sttModels = writable<SttModel[]>([]);

/**
 * Fetches available STT models from the API
 * @returns Array of available models or empty array if an error occurred
 */
export async function fetchSttModels(): Promise<SttModel[]> {
	try {
		const response = await fetch('/api/stt/models');

		if (response.ok) {
			const data = await response.json();
			const models = data.models || [];
			sttModels.set(models);
			return models;
		} else {
			// Try to get more detailed error information
			let errorDetail = '';
			try {
				const errorData = await response.json();
				errorDetail = errorData.detail || '';
			} catch {
				errorDetail = response.statusText;
			}

			const errorMsg = `Error fetching STT models: ${response.status} ${errorDetail}`;
			serviceError.set(errorMsg);
			return [];
		}
	} catch (error) {
		const errorMsg = `Error fetching STT models: ${error instanceof Error ? error.message : String(error)}`;
		serviceError.set(errorMsg);
		return [];
	}
}

/**
 * Transcribes audio using the STT API
 * @param audioBlob The audio blob to transcribe
 * @param model The model to use for transcription
 * @returns The transcribed text or null if an error occurred
 */
export async function transcribeAudio(
	audioBlob: Blob,
	model: string = 'whisper-large-v3',
	username?: string
): Promise<string | null> {
	try {
		activeTranscriptions.update((n) => n + 1); // Increment counter
		// Create a FormData object and append the audio blob and model
		const formData = new FormData();
		formData.append('audio', audioBlob, 'recording.mp3');
		formData.append('model', model);

		// Send the request to the API
		const response = await fetch('/api/stt/transcribe', {
			method: 'POST',
			body: formData
		});

		// Handle the response
		if (response.ok) {
			const data: SttResponse = await response.json();
			const transcript = data.text.trim();

			if (
				!transcript ||
				transcript === 'You' ||
				transcript === 'Thank you.' ||
				transcript === 'Thank you!'
			)
				return null;

			serviceOutput.stt.push({ username: username ? username : 'Anonymous', transcript });
			return transcript;
		} else {
			// Try to get more detailed error information
			let errorDetail = '';
			try {
				const errorData = await response.json();
				errorDetail = errorData.detail || '';
			} catch {
				errorDetail = response.statusText;
			}

			const errorMsg = `Error transcribing audio: ${response.status} ${errorDetail}`;
			serviceError.set(errorMsg);
			return null;
		}
	} catch (error) {
		const errorMsg = `Error transcribing audio: ${error instanceof Error ? error.message : String(error)}`;
		serviceError.set(errorMsg);
		return null;
	} finally {
		activeTranscriptions.update((n) => n - 1); // Decrement counter
	}
}
