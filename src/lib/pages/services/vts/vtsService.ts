import { get, writable } from 'svelte/store';
import { serviceError } from '../docker/dockerService';

export type ModelParam = {
	name: string;
	value: number;
	min?: number;
	max?: number;
	defaultValue?: number;
	info?: string;
};

const API_BASE_URL = '/api/vts';
export const loading = writable(false);
export const modelParams = writable<ModelParam[]>([]);

let paramUpdateIntervalId: number | undefined = undefined;
const paramUpdateIntervalMS: number = 500;

export async function connect() {
	loading.set(true);
	try {
		const response = await fetch(`${API_BASE_URL}/connect`);

		if (!response.ok) {
			serviceError.set(
				`Failed to connect to vts service: ${response.status} ${response.statusText}`
			);
		} else {
			await getCustomParams();
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

			// Start periodic updates
			if (paramUpdateIntervalId) {
				clearInterval(paramUpdateIntervalId);
			} else {
				paramUpdateIntervalId = setInterval(() => {
					setParams(get(modelParams));
				}, paramUpdateIntervalMS);
			}
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
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to create model param ${name}: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to create model param ${name}`);
		}
	}
}

export async function setParam(name: string, value: number) {
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
	}
}

export async function setParams(params: ModelParam[]): Promise<void>;

export async function setParams(names: string[], values: number[]): Promise<void>;

export async function setParams(
	paramsOrNames: string[] | ModelParam[],
	values?: number[]
): Promise<void> {
	try {
		let names: string[] = [];
		if (!values) {
			names = (paramsOrNames as ModelParam[]).map((param) => param.name);
			values = (paramsOrNames as ModelParam[]).map((param) => param.value);
		} else {
			names = paramsOrNames as string[];
		}

		const response = await fetch(`${API_BASE_URL}/set_params`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ names, values })
		});

		if (!response.ok) {
			serviceError.set(
				`Failed to set multiple model params: ${response.status} ${response.statusText}`
			);
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to set multiple model params: ${error.message}`);
		} else {
			serviceError.set(`Unknown error trying to set multiple model params`);
		}
	}
}

export async function deleteParam(name: string) {
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
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to delete model param ${name}: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to delete model param ${name}`);
		}
	}
}
