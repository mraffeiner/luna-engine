import { serviceError } from '../docker/dockerService'; // Use shared error handling

// --- Constants ---
const OBS_API_BASE_URL = '/api/obs'; // Use the Nginx proxy path

// --- Public API ---

/**
 * Sends text to the OBS subtitle source via the backend service and Nginx proxy.
 * @param text The text to display as a subtitle.
 */
export async function sendSubtitle(text: string): Promise<{ success: boolean; error?: string }> {
	try {
		const response = await fetch(`${OBS_API_BASE_URL}/subtitle`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ text })
		});

		const data = await response.json();

		if (!response.ok) {
			// Handle specific proxy errors or service errors
			let errorMessage =
				data.error || `Failed to send subtitle: ${response.status} ${response.statusText}`;
			if (response.status === 502 || response.status === 503 || response.status === 504) {
				errorMessage = `OBS service unavailable (Proxy Error ${response.status})`;
			} else if (
				response.status === 500 &&
				data.error === 'OBS_SUBTITLE_SOURCE_NAME environment variable not set'
			) {
				errorMessage = 'OBS Subtitle Source Name not configured in the backend service.';
			}
			throw new Error(errorMessage);
		}

		// Clear specific error if send subtitle succeeds
		serviceError.update((err) =>
			err?.startsWith('Failed to send subtitle') ||
			err?.startsWith('OBS service unavailable') ||
			err?.startsWith('OBS Subtitle Source Name')
				? null
				: err
		);
		return { success: true };
	} catch (error) {
		console.error('Error sending subtitle:', error);
		const errorMessage = error instanceof Error ? error.message : String(error);
		// Set the error in the shared banner
		serviceError.set(`OBS Subtitle Error: ${errorMessage}`);
		return { success: false, error: errorMessage };
	}
}
