import { containerStatus } from '$lib/shared/shared.svelte';
import { writable, type Writable } from 'svelte/store';

/**
 * Interface matching backend ContainerStatusResponse
 */
export interface ContainerStatusResponse {
	status: string;
}

// Stores
export const serviceError = writable<string | null>(null);

// Private state
const serviceLogs = new Map<string, Writable<string[]>>();
const API_BASE_URL = '/api/docker';
let logStream: EventSource | null = null; // Single EventSource for all logs

/**
 * Makes an API request with consistent error handling
 */
async function apiRequest<T>(
	endpoint: string,
	serviceName: string,
	operation: string,
	options: RequestInit = {}
): Promise<T | null> {
	try {
		const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

		if (!response.ok) {
			const errorText = await response.text();
			const message = `API error for ${serviceName} (${operation}): ${response.status} ${response.statusText} - ${errorText}`;
			serviceError.set(message);
			console.error(`API error for ${serviceName}:`, message);
			throw new Error(message);
		}

		return response.json();
	} catch (error) {
		const message =
			error instanceof Error
				? `Failed to ${operation} ${serviceName}: ${error.message}`
				: `Failed to ${operation} ${serviceName}: Unknown error`;

		serviceError.set(message);
		console.error(`Failed to ${operation} ${serviceName}:`, error);
		return null;
	}
}

/**
 * Service for managing container operations
 */
export const dockerService = {
	/**
	 * Checks the status of a container
	 */
	checkContainerStatus: async (serviceName: string): Promise<void> => {
		const data = await apiRequest<ContainerStatusResponse>(
			`/container_status/${serviceName}`,
			serviceName,
			'check status'
		);

		if (data?.status) {
			containerStatus.set(
				serviceName,
				data.status === 'running' || data.status === 'restarting' ? 'RUNNING' : 'STOPPED'
			);
		} else {
			containerStatus.set(serviceName, 'UNKNOWN');
		}
	},

	/**
	 * Starts a container
	 */
	startContainer: async (serviceName: string): Promise<void> => {
		containerStatus.set(serviceName, 'STARTING');

		try {
			await apiRequest(`/start_container/${serviceName}`, serviceName, 'start', { method: 'POST' });
			containerStatus.set(serviceName, 'RUNNING');
		} catch (error) {
			containerStatus.set(serviceName, 'STOPPED');
			console.error('Failed to start container:', error);
		}
	},

	/**
	 * Stops a container
	 */
	stopContainer: async (serviceName: string): Promise<void> => {
		containerStatus.set(serviceName, 'STOPPING');

		try {
			await apiRequest(`/stop_container/${serviceName}`, serviceName, 'stop', { method: 'POST' });
			containerStatus.set(serviceName, 'STOPPED');
		} catch (error) {
			containerStatus.set(serviceName, 'RUNNING');
			console.error('Failed to stop container:', error);
		}
	},

	/**
	 * Starts the global log stream
	 */
	startLogsStream: () => {
		if (logStream) {
			return;
		}

		try {
			logStream = new EventSource(`${API_BASE_URL}/container_logs`);

			logStream.onmessage = (event) => {
				const data = JSON.parse(event.data);
				const serviceName = data.service;
				const logMessage = data.log + '\n';

				if (serviceName) {
					if (!serviceLogs.has(serviceName)) {
						serviceLogs.set(serviceName, writable<string[]>([]));
					}
					serviceLogs.get(serviceName)!.update((logs) => [...logs, logMessage]);
				}
			};

			logStream.onerror = (error) => {
				serviceError.set('Failed to stream logs');
				console.error('Log stream error:', error);
				if (logStream) {
					logStream.close();
					logStream = null;
				}
			};
		} catch (error) {
			console.error('Failed to start global log stream:', error);
		}
	},

	/**
	 *  Stops the global log stream
	 */
	stopLogsStream: (): void => {
		if (logStream) {
			logStream.close();
			logStream = null;
		}
	},

	/**
	 * Gets the logs store for a service
	 */
	getLogsStore: (serviceName: string): Writable<string[]> => {
		if (!serviceLogs.has(serviceName)) {
			serviceLogs.set(serviceName, writable<string[]>([]));
		}
		return serviceLogs.get(serviceName)!;
	},

	/**
	 * Clears the logs for a service
	 */
	clearLogs: (serviceName: string): void => {
		serviceLogs.get(serviceName)?.set([]);
	}
};
