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

let voiceBasedMotionIntervalId: number | undefined = undefined;
const voiceBasedMotionIntervalMS: number = 33.33;

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

			// Start/restart periodic updates
			if (paramUpdateIntervalId) {
				clearInterval(paramUpdateIntervalId);
			}
			paramUpdateIntervalId = setInterval(() => {
				setParams(get(modelParams));
			}, paramUpdateIntervalMS);

			// Start/restart voice based motion
			if (voiceBasedMotionIntervalId) {
				clearInterval(voiceBasedMotionIntervalId);
			}
			voiceBasedMotionIntervalId = setInterval(() => {
				moveModelByVoice();
			}, voiceBasedMotionIntervalMS);
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
		} else {
			modelParams.update((params) => {
				params.push({
					name: name,
					value: default_value,
					min: min,
					max: max,
					defaultValue: default_value,
					info: info
				});
				return params;
			});
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

export async function getParam(name: string): Promise<ModelParam | void> {
	try {
		const response = await fetch(`${API_BASE_URL}/get_param`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ name })
		});

		if (!response.ok) {
			serviceError.set(
				`Failed to get model param ${name}: ${response.status} ${response.statusText}`
			);
		} else {
			return await response.json();
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to get model param ${name}: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to get model param ${name}`);
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
		} else {
			modelParams.update((params) => {
				return params.filter((param) => param.name !== name);
			});
		}
	} catch (error) {
		if (error instanceof Error) {
			serviceError.set(`Failed to delete model param ${name}: ${error.message}`);
		} else {
			serviceError.set(`Unkown error trying to delete model param ${name}`);
		}
	}
}

/**
 * Creates a slow “brownian” noise generator in [–1,1].
 * @param freqHz  Update frequency in Hz
 * @param frameRate  Frames per second
 */
function makeBrown(freqHz: number, frameRate: number = 30): () => number {
	let z = 0;
	const λ = Math.exp((-2 * Math.PI * freqHz) / frameRate);

	return () => {
		const ε = Math.random() * 2 - 1;
		z = λ * z + Math.sqrt(1 - λ * λ) * ε;
		return z;
	};
}

// Tweak these to taste:
const A_PITCH = 12; // ° swing on loudness
const A_YAW = 6; // ° swing on frequency
const J_P = 3; // ° idle noise pitch
const J_Y = 5; // ° idle noise yaw
const J_R = 5; // ° idle noise roll
const ALPHA = 0.1; // smoothing factor [0..1]

const noiseP = makeBrown(0.2);
const noiseY = makeBrown(0.25);
const noiseR = makeBrown(0.15);

let facePitch = 0; // CustomFaceAngleY
let faceYaw = 0; // CustomFaceAngleX
let faceRoll = 0; // CustomFaceAngleZ

async function moveModelByVoice() {
	const volume = (await getParam('VoiceVolume'))?.value;
	const frequency = (await getParam('VoiceFrequency'))?.value;
	if (!volume || !frequency) return;

	// 1) raw targets
	const rawPitch = A_PITCH * (volume - 0.5) + J_P * noiseP();
	const rawYaw = A_YAW * frequency + J_Y * noiseY();
	const rawRoll = J_R * noiseR();

	// 2) exponential smoothing
	facePitch = ALPHA * rawPitch + (1 - ALPHA) * facePitch;
	faceYaw = ALPHA * rawYaw + (1 - ALPHA) * faceYaw;
	faceRoll = ALPHA * rawRoll + (1 - ALPHA) * faceRoll;

	modelParams.update((params) => {
		const updatedParams = params.map((param) => {
			// 3) apply to face
			if (param.name === 'CustomFaceAngleY') {
				param.value = facePitch;
			}
			if (param.name === 'CustomFaceAngleX') {
				param.value = faceYaw;
			}
			if (param.name === 'CustomFaceAngleZ') {
				param.value = faceRoll;
			}
			// 4) apply scaled to body
			if (param.name === 'CustomBodyAngleY') {
				param.value = facePitch;
			}
			if (param.name === 'CustomBodyAngleX') {
				param.value = faceYaw;
			}
			if (param.name === 'CustomBodyAngleZ') {
				param.value = faceRoll;
			}
			return param;
		});
		return updatedParams;
	});
}
