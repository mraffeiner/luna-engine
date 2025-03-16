import { get, writable, type Writable } from 'svelte/store';

/**
 * Interface matching backend ContainerStatusResponse
 */
export interface ContainerStatusResponse {
	running: boolean;
	status: string;
}

/**
 * Frontend container status with loading state
 */
export interface ContainerStatus {
	isRunning: boolean;
	isStarting: boolean;
	isStopping: boolean;
	status?: string;
}

// Stores
export const serviceError = writable<string | null>(null);
export const containerStatus = writable<Record<string, ContainerStatus>>({});

// Private state
const logStreams = new Map<string, EventSource>();
const serviceLogs = new Map<string, Writable<string[]>>();
const API_BASE_URL = '/api/docker';

// Default container status
const DEFAULT_STATUS = {
	isRunning: false,
	isStarting: false,
	isStopping: false,
	status: 'unknown'
};

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
			let errorText: string;
			try {
				const errorJson = await response.json();
				errorText = errorJson.detail || JSON.stringify(errorJson);
			} catch {
				errorText = await response.text();
			}

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
 * Updates container status with new values
 */
function updateStatus(serviceName: string, updates: Partial<ContainerStatus>): void {
	containerStatus.update((status) => ({
		...status,
		[serviceName]: {
			...(status[serviceName] || DEFAULT_STATUS),
			...updates
		}
	}));
}

/**
 * Service for managing container operations
 */
export const dockerService = {
	/**
	 * Starts a container
	 */
	startContainer: async (serviceName: string): Promise<void> => {
		updateStatus(serviceName, { isStarting: true });

		try {
			await apiRequest(`/start_container/${serviceName}`, serviceName, 'start', { method: 'POST' });
			updateStatus(serviceName, { isRunning: true });
			dockerService.startLogStream(serviceName);
		} finally {
			updateStatus(serviceName, { isStarting: false });
		}
	},

	/**
	 * Stops a container
	 */
	stopContainer: async (serviceName: string): Promise<void> => {
		updateStatus(serviceName, { isStopping: true });

		try {
			await apiRequest(`/stop_container/${serviceName}`, serviceName, 'stop', { method: 'POST' });
			updateStatus(serviceName, { isRunning: false });
		} finally {
			updateStatus(serviceName, { isStopping: false });
		}
	},

	/**
	 * Starts a log stream for a container
	 */
	startLogStream: async (serviceName: string): Promise<void> => {
		if (logStreams.has(serviceName) || !get(containerStatus)[serviceName]?.isRunning) {
			return;
		}
		// Initialize or reset logs store
		const logsStore = serviceLogs.get(serviceName) || writable<string[]>([]);
		if (!serviceLogs.has(serviceName)) {
			serviceLogs.set(serviceName, logsStore);
		} else {
			logsStore.set([]);
		}

		try {
			const eventSource = new EventSource(`${API_BASE_URL}/container_logs/${serviceName}`);
			logStreams.set(serviceName, eventSource);

			eventSource.onmessage = (event) => {
				logsStore.update((logs) => [...logs, event.data + '\n']);
			};

			eventSource.onerror = (error) => {
				if (!get(containerStatus)[serviceName].isStopping) {
					serviceError.set(`Failed to stream logs for ${serviceName}`);
					console.error(`Log stream error for ${serviceName}:`, error);
				}

				eventSource.close();
				logStreams.delete(serviceName);
			};
		} catch (error) {
			console.error(`Failed to start log stream for ${serviceName}:`, error);
		}
	},

	/**
	 * Stops a log stream for a container
	 */
	stopLogStream: (serviceName: string): void => {
		const eventSource = logStreams.get(serviceName);
		if (eventSource) {
			eventSource.close();
			logStreams.delete(serviceName);
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
	},

	/**
	 * Checks the status of a container
	 */
	checkContainerStatus: async (serviceName: string): Promise<ContainerStatusResponse | null> => {
		const data = await apiRequest<ContainerStatusResponse>(
			`/container_status/${serviceName}`,
			serviceName,
			'check status'
		);

		if (data) {
			updateStatus(serviceName, {
				isRunning: data.running,
				status: data.status
			});
		}

		return data;
	}
};
