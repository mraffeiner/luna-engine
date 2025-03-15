import { serviceError } from '$lib/containerService';

const API_BASE_URL = '/api/discord';

let audioWebSocket: WebSocket | null = null;

export const discordService = {
	async connect(guildId: string, channelId: string): Promise<boolean> {
		console.log('discordService.connect called with guildId:', guildId, 'channelId:', channelId);
		try {
			const response = await fetch(`${API_BASE_URL}/join-voice`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ guildId, channelId })
			});
			console.log('discordService.connect response:', response);
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

	async connectWebSocket(onAudioReceived: (audioBlob: Blob) => void): Promise<void> {
		if (audioWebSocket) {
			return;
		}
		audioWebSocket = new WebSocket('/api/discord/ws');

		audioWebSocket.onopen = () => {
			console.log('WebSocket connection established (discordService)');
		};

		audioWebSocket.onmessage = async (event: MessageEvent) => {
			console.log('Received message from WebSocket (discordService):', event);
			onAudioReceived(new Blob([event.data], { type: 'audio/wav' }));
		};

		audioWebSocket.onclose = () => {
			console.log('WebSocket connection closed (discordService)');
			audioWebSocket = null;
		};

		audioWebSocket.onerror = (event: Event) => {
			console.error('WebSocket error (discordService):', event);
			serviceError.set('WebSocket error: ' + String(event));
			audioWebSocket = null;
		};
	},

	async disconnect(): Promise<boolean> {
		try {
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
		} finally {
			if (audioWebSocket) {
				audioWebSocket.close();
				audioWebSocket = null;
			}
		}
	}
};
