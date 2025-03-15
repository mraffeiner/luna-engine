import { writable } from 'svelte/store';

export interface SttResponse {
	text: string;
}

// Shared store for error messages
export const sttError = writable<string | null>(null);
export const sttStatus = writable<'idle' | 'recording' | 'transcribing'>('idle');

/**
 * Transcribes audio using the STT API
 * @param audioBlob The audio blob to transcribe
 * @returns The transcribed text or null if an error occurred
 */
export async function transcribeAudio(audioBlob: Blob): Promise<string | null> {
	try {
		sttStatus.set('transcribing');
		sttError.set(null);

		// Create a FormData object and append the audio blob
		const formData = new FormData();
		formData.append('audio', audioBlob, 'recording.mp3');

		// Send the request to the API
		const response = await fetch('/api/stt', {
			method: 'POST',
			body: formData
		});

		// Handle the response
		if (response.ok) {
			const data: SttResponse = await response.json();
			sttStatus.set('idle');
			return data.text;
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
			sttError.set(errorMsg);
			sttStatus.set('idle');
			return null;
		}
	} catch (error) {
		const errorMsg = `Error transcribing audio: ${error instanceof Error ? error.message : String(error)}`;
		sttError.set(errorMsg);
		sttStatus.set('idle');
		return null;
	}
}
