import { serviceError } from '$lib/pages/services/docker/dockerService';

const API_BASE_URL = '/api/discord';

let audioWebSocket: WebSocket | null = null;
let resolvePlaybackComplete: () => void = () => {};

export const discordService = {
	async connect(guildId: string, channelId: string): Promise<boolean> {
		try {
			const response = await fetch(`${API_BASE_URL}/join-voice`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ guildId, channelId })
			});
			if (!response.ok) {
				const error = await response.text();
				console.error('discordService.connect error:', error);
				throw new Error(error);
			}
			return true;
		} catch (error) {
			serviceError.set(error instanceof Error ? error.message : String(error));
			console.error('discordService.connect error:', error);
			return false;
		}
	},

	connectWebSocket(onAudioReceived: (username: string, audioBlob: Blob) => void) {
		if (audioWebSocket) {
			return;
		}

		audioWebSocket = new WebSocket(`${API_BASE_URL}/`);
		audioWebSocket.binaryType = 'arraybuffer';

		audioWebSocket.onmessage = (event: MessageEvent) => {
			if (event.data instanceof ArrayBuffer) {
				// Extract username and audio blob
				const dataView = new DataView(event.data);
				const usernameLength = dataView.getUint32(0, false);
				const usernameBytes = new Uint8Array(event.data, 4, usernameLength);
				const username = new TextDecoder().decode(usernameBytes);
				const audioData = new Uint8Array(event.data, 4 + usernameLength);
				const audioBlob = new Blob([audioData], { type: 'audio/wav' });

				onAudioReceived(username, audioBlob);
			} else if (typeof event.data === 'string') {
				const message = JSON.parse(event.data);
				if (message.type === 'playback_complete') {
					resolvePlaybackComplete();
				}
			}
		};

		audioWebSocket.onclose = () => {
			audioWebSocket = null;
		};

		audioWebSocket.onerror = (event: Event) => {
			console.error('WebSocket error:', event);
			serviceError.set('WebSocket error: ' + String(event));
			audioWebSocket = null;
		};
	},

	playAudio(audioBlob: Blob): Promise<void> {
		if (!audioWebSocket) {
			throw new Error('WebSocket not connected');
		}

		audioWebSocket.send(audioBlob);
		return new Promise((resolve, reject) => {
			resolvePlaybackComplete = resolve;
			setTimeout(() => {
				reject(new Error('Playback timeout'));
			}, 300000); // 5 minutes
		});
	},

	async disconnect(): Promise<boolean> {
		try {
			audioWebSocket?.close();
			const response = await fetch(`${API_BASE_URL}/leave-voice`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({})
			});
			if (!response.ok) {
				const error = await response.text();
				throw new Error(error);
			}
			return true;
		} catch (error) {
			serviceError.set(error instanceof Error ? error.message : String(error));
			return false;
		}
	}
};
