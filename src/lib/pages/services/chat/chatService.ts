import { writable, type Writable } from 'svelte/store';

// --- Types ---
export interface ChatMessage {
	platform: 'twitch' | 'youtube' | 'system' | 'unknown';
	channel: string;
	author: string;
	text: string;
	timestamp: string;
}

export type Platform = 'twitch' | 'youtube';
export type ConnectionStatus =
	| 'disconnected'
	| 'connecting'
	| 'connected'
	| 'auth_required'
	| 'error'
	| 'error_config'
	| 'error_api'
	| 'error_quota'
	| 'error_chat_ended'
	| 'error_auth'
	| 'error_no_live_chat'
	| 'authenticated';

// --- Constants ---
const MAX_MESSAGES = 150;
const API_BASE_URL = '/api/chat';
const WS_URL = '/api/chat/ws';

// --- Stores ---
export const chatMessages: Writable<ChatMessage[]> = writable([]);
export const platformStatus: Writable<Record<Platform, ConnectionStatus>> = writable({
	twitch: 'disconnected',
	youtube: 'disconnected'
});
export const webSocketStatus: Writable<'connecting' | 'connected' | 'disconnected' | 'error'> =
	writable('disconnected');

// --- WebSocket Management ---
let socket: WebSocket | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY_MS = 3000;

function addMessage(message: ChatMessage) {
	chatMessages.update((messages) => {
		const newMessages = [...messages, message];
		if (newMessages.length > MAX_MESSAGES) {
			return newMessages.slice(newMessages.length - MAX_MESSAGES);
		}
		return newMessages;
	});
}

function addSystemMessage(text: string) {
	const systemMessage: ChatMessage = {
		platform: 'system',
		channel: '',
		author: 'System',
		text: text,
		timestamp: new Date().toISOString()
	};
	addMessage(systemMessage);
}

function connectWebSocket() {
	if (
		socket &&
		(socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)
	)
		return;

	webSocketStatus.set('connecting');
	socket = new WebSocket(WS_URL);

	socket.onopen = () => {
		webSocketStatus.set('connected');
		reconnectAttempts = 0;
		addSystemMessage('Connected to chat message feed.');
		// Fetch initial status upon successful connection
		fetchPlatformStatus();
	};

	socket.onmessage = (event) => {
		try {
			const messageData = JSON.parse(event.data);

			// Check if it's a chat message
			if (
				messageData?.platform &&
				messageData?.author &&
				messageData?.text &&
				messageData?.timestamp
			) {
				const newMessage: ChatMessage = {
					platform: messageData.platform,
					channel: messageData.channel || 'unknown',
					author: messageData.author,
					text: messageData.text,
					timestamp: messageData.timestamp
				};
				addMessage(newMessage);
			}
			// Check if it's a status update message
			else if (
				messageData?.type === 'status_update' &&
				messageData?.platform &&
				messageData?.status
			) {
				const platform = messageData.platform as Platform;
				const status = messageData.status as ConnectionStatus;
				// Update the specific platform's status in the store
				platformStatus.update((current) => {
					if (current[platform] !== status) {
						return { ...current, [platform]: status };
					}
					return current; // No change needed
				});
			} else {
				console.warn('Received unknown or malformed message via WebSocket:', messageData);
			}
		} catch (error) {
			console.error('Failed to parse WebSocket message:', error, 'Data:', event.data);
		}
	};

	socket.onerror = (error) => {
		console.error('WebSocket error:', error);
		webSocketStatus.set('error');
		addSystemMessage('WebSocket connection error.');
	};

	socket.onclose = (event) => {
		webSocketStatus.set('disconnected');
		addSystemMessage('Disconnected from chat message feed.');
		socket = null;

		if (!event.wasClean && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
			reconnectAttempts++;
			setTimeout(connectWebSocket, RECONNECT_DELAY_MS * Math.pow(2, reconnectAttempts - 1));
		} else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
			console.error('Max WebSocket reconnect attempts reached.');
		}
	};
}

function disconnectWebSocket() {
	if (socket) {
		reconnectAttempts = MAX_RECONNECT_ATTEMPTS;
		socket.close(1000, 'Client initiated disconnect');
		socket = null;
		webSocketStatus.set('disconnected');
	}
}

// --- API Interaction ---

async function fetchPlatformStatus(): Promise<void> {
	try {
		const response = await fetch(`${API_BASE_URL}/status`);
		if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
		const statusData: Record<Platform, ConnectionStatus> = await response.json();
		platformStatus.set(statusData);
	} catch (error) {
		console.error('Failed to fetch platform status:', error);
		addSystemMessage(`Error fetching platform status: ${error}`);
	}
}

async function controlPlatform(
	platform: Platform,
	action: 'connect' | 'disconnect'
): Promise<void> {
	try {
		const response = await fetch(`${API_BASE_URL}/${action}/${platform}`, { method: 'POST' }); // Uses relative path
		if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
		const statusData: Record<Platform, ConnectionStatus> = await response.json();

		if (action === 'connect' && statusData[platform] === 'auth_required') {
			addSystemMessage(`YouTube authentication required. Fetching auth URL...`);
			await fetchAndCopyAuthUrl();
		} else {
			addSystemMessage(
				`${platform.charAt(0).toUpperCase() + platform.slice(1)} ${action} request processed. New status: ${statusData[platform]}`
			);
		}
		platformStatus.set(statusData);
	} catch (error) {
		console.error(`Failed to ${action} ${platform}:`, error);
		addSystemMessage(`Error processing ${action} request for ${platform}: ${error}`);
		fetchPlatformStatus();
	}
}

async function fetchAndCopyAuthUrl(): Promise<void> {
	try {
		const response = await fetch(`${API_BASE_URL}/auth-url`); // Uses relative path
		if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
		const data = await response.json();
		if (data.auth_url) {
			await navigator.clipboard.writeText(data.auth_url);
			addSystemMessage(
				'YouTube Auth URL copied to clipboard! Paste it into your browser and grant access'
			);
		} else {
			addSystemMessage(
				'Could not retrieve YouTube Auth URL. Is it needed? ' + (data.message || '')
			);
		}
	} catch (error) {
		console.error('Failed to fetch or copy auth URL:', error);
		addSystemMessage(`Error fetching YouTube Auth URL: ${error}`);
	}
}

// --- Service Object ---
export const chatService = {
	connectWebSocket,
	disconnectWebSocket,
	connectPlatform: (platform: Platform) => controlPlatform(platform, 'connect'),
	disconnectPlatform: (platform: Platform) => controlPlatform(platform, 'disconnect'),
	fetchStatus: fetchPlatformStatus,
	fetchAndCopyAuthUrl: fetchAndCopyAuthUrl
};
