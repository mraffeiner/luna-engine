import { writable } from 'svelte/store';
import { serviceError } from '../docker/dockerService';

const API_BASE_URL = '/api/vts';
export const loading = writable(false);
export const modelParams = writable<
	{
		name: string;
		value: number;
		min?: number;
		max?: number;
		defaultValue?: number;
		info?: string;
	}[]
>([]);

export async function connect() {
	loading.set(true);
	try {
		const response = await fetch(`${API_BASE_URL}/connect`);

		if (!response.ok) {
			serviceError.set(
				`Failed to connect to vts service: ${response.status} ${response.statusText}`
			);
		} else {
			getCustomParams();
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to connect to vts service: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to connect to vts service`);
		}
	} finally {
		loading.set(false);
	}
}

export async function getCustomParams() {
	loading.set(true);
	try {
		const response = await fetch(`${API_BASE_URL}/list_custom_params`);

		if (!response.ok) {
			serviceError.set(`Failed to get model params: ${response.status} ${response.statusText}`);
		} else {
			const data = await response.json();
			modelParams.set(data);
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to get model params: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to get model params`);
		}
	} finally {
		loading.set(false);
	}
}

export async function createParam(
	name: string,
	min: number,
	max: number,
	default_value: number,
	info?: string
) {
	loading.set(true);
	try {
		const response = await fetch(`${API_BASE_URL}/create_param`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ name, min, max, default_value, info })
		});

		if (!response.ok) {
			serviceError.set(
				`Failed to create model param ${name}: ${response.status} ${response.statusText}`
			);
		} else {
			getCustomParams();
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to create model param ${name}: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to create model param ${name}`);
		}
	} finally {
		loading.set(false);
	}
}

export async function setParam(name: string, value: number) {
	loading.set(true);
	try {
		const response = await fetch(`${API_BASE_URL}/set_param`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ name, value })
		});

		if (!response.ok) {
			serviceError.set(
				`Failed to set model param ${name} to ${value}: ${response.status} ${response.statusText}`
			);
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to set model param ${name} to ${value}: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to set model param ${name} to ${value}`);
		}
	} finally {
		loading.set(false);
	}
}

export async function deleteParam(name: string) {
	loading.set(true);
	try {
		const response = await fetch(`${API_BASE_URL}/delete_param`, {
			method: 'DELETE',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ name })
		});

		if (!response.ok) {
			serviceError.set(
				`Failed to delete model param ${name}: ${response.status} ${response.statusText}`
			);
		} else {
			getCustomParams();
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to delete model param ${name}: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to delete model param ${name}`);
		}
	} finally {
		loading.set(false);
	}
}
