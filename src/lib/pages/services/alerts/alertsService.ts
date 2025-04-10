import { serviceOutput } from '$lib/shared/shared.svelte';
import { writable } from 'svelte/store';

// Define the standardized structure received from the backend
export interface StandardizedAlert {
	id: string;
	type:
		| 'follow'
		| 'sub'
		| 'resub'
		| 'giftsub'
		| 'communitygiftsub'
		| 'tip'
		| 'cheer'
		| 'raid'
		| 'host'
		| 'test'
		| 'communityGiftPurchase'
		| 'redemption'
		| 'merch'
		| 'charityCampaignDonation'
		| 'unknown';
	platform: 'twitch' | 'youtube' | 'facebook' | 'trovo' | 'unknown';
	timestamp: string;
	user?: string;
	recipient?: string;
	amount?: number;
	currency?: string;
	message?: string;
	tier?: string;
	isGift?: boolean;
	isCommunity?: boolean;
	gifter?: string;
	originalEventName: string;
}

// --- Configuration ---
const API_BASE_URL = '/api/alerts';

const RECONNECT_INTERVAL = 5000; // ms

// --- Svelte Store ---
// Store for the latest alert message
export const alerts = writable<StandardizedAlert[]>([]);
// Store for the connection status
export const alertConnectionStatus = writable<
	'connecting' | 'connected' | 'disconnected' | 'error'
>('disconnected');

// --- WebSocket Logic ---
let ws: WebSocket | null = null;
let reconnectTimer: number | null = null;

// Helper to format timestamp
export function formatTimestamp(isoString: string): string {
	try {
		if (!isoString || typeof isoString !== 'string') return '??:??:??';
		const date = new Date(isoString);
		if (isNaN(date.getTime())) return '??:??:??';
		return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
	} catch (e) {
		console.error('Error formatting timestamp:', e, 'Input:', isoString);
		return '??:??:??';
	}
}

export function formatAlertMessage(alert: StandardizedAlert): string {
	const platformStr = alert.platform ? `[${alert.platform.toUpperCase()}]` : '';
	const typeStr = alert.type ? `[${alert.type.toUpperCase()}]` : '[UNKNOWN]';

	let coreMessage = '';

	// Determine the core message based on the alert type
	switch (alert.type) {
		case 'follow':
			coreMessage = `${alert.user || 'Someone'} just followed!`;
			break;
		case 'sub':
		case 'resub':
			coreMessage = `${alert.user || 'Someone'} subscribed`;
			if (alert.tier) {
				coreMessage += ` (Tier ${alert.tier})`;
			}
			if (alert.type === 'resub' && alert.amount) {
				coreMessage += ` for ${alert.amount} months!`;
			} else {
				coreMessage += `!`;
			}
			break;
		case 'giftsub':
			coreMessage = `${alert.gifter || 'Someone'} gifted a sub to ${alert.recipient || 'Someone'}!`;
			break;
		case 'communitygiftsub':
			coreMessage = `${alert.gifter || 'Someone'} gifted ${
				alert.amount || 'N/A'
			} subs to the community!`;
			break;
		case 'tip':
			coreMessage = `${alert.user || 'Someone'} tipped ${
				alert.amount || 'N/A'
			} ${alert.currency || ''}!`;
			break;
		case 'cheer':
			coreMessage = `${alert.user || 'Someone'} cheered ${alert.amount || 'N/A'} bits!`;
			break;
		case 'raid':
			coreMessage = `${alert.user || 'Someone'} raided with ${alert.amount || 'N/A'} viewers!`;
			break;
		case 'host':
			coreMessage = `${alert.user || 'Someone'} is hosting with ${alert.amount || 'N/A'} viewers!`;
			break;
		case 'test':
			coreMessage = `Test Event from ${alert.user || 'StreamElements'}`;
			if (alert.amount) {
				coreMessage += ` (Amount: ${alert.amount})`;
			}
			break;
		case 'redemption':
			coreMessage = `${alert.user || 'Someone'} redeemed`;
			if (alert.message) {
				coreMessage += ` ${alert.message}`;
			}
			coreMessage += `!`;
			break;
		case 'merch':
			coreMessage = `${alert.user || 'Someone'} purchased merch!`;
			if (alert.message) {
				coreMessage += ` (${alert.message})`;
			}
			break;
		case 'charityCampaignDonation':
			coreMessage = `${alert.user || 'Someone'} donated ${
				alert.amount || 'N/A'
			} ${alert.currency || ''} to charity!`;
			break;
		default:
			coreMessage = `${alert.user || 'Someone'} triggered ${alert.type}`;
			if (alert.amount) {
				coreMessage += ` (${alert.amount})`;
			}
			break;
	}

	// Construct the final string parts
	const prefix = `${platformStr} ${typeStr}`.trim();
	let finalMessage = `${prefix} ${coreMessage}`;

	// Append the message at the end
	if (alert.message) {
		finalMessage += ` "${alert.message}"`;
	}

	// Clean up potential double spaces
	return finalMessage.replace(/\s+/g, ' ').trim();
}

export function connect() {
	if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
		return;
	}

	if (reconnectTimer) {
		clearTimeout(reconnectTimer);
		reconnectTimer = null;
	}

	alertConnectionStatus.set('connecting');

	try {
		ws = new WebSocket(`${API_BASE_URL}/ws`);

		ws.onopen = () => {
			alertConnectionStatus.set('connected');
		};

		ws.onmessage = (event) => {
			try {
				const message: StandardizedAlert = JSON.parse(event.data);
				alerts.update((current) => [...current, message]);
				serviceOutput.alerts.push(formatAlertMessage(message));
			} catch (error) {
				console.error('[AlertsService] Error parsing message:', error, 'Data:', event.data);
			}
		};

		ws.onerror = (error) => {
			console.error('[AlertsService] WebSocket error:', error);
			alertConnectionStatus.set('error');
		};

		ws.onclose = () => {
			alertConnectionStatus.set('disconnected');
			ws = null;
			if (!reconnectTimer) {
				reconnectTimer = window.setTimeout(connect, RECONNECT_INTERVAL);
			}
		};
	} catch (error) {
		console.error('[AlertsService] Failed to create WebSocket:', error);
		alertConnectionStatus.set('error');
		if (!reconnectTimer) {
			reconnectTimer = window.setTimeout(connect, RECONNECT_INTERVAL);
		}
	}
}

export function disconnect() {
	if (reconnectTimer) {
		clearTimeout(reconnectTimer);
		reconnectTimer = null;
	}
	if (ws) {
		ws.close();
		ws = null;
		alertConnectionStatus.set('disconnected');
	}
}
