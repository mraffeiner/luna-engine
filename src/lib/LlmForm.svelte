<script lang="ts">
	import { llmOutput, promptOutput } from './stores';
	import Icon from './Icon.svelte';
	import Spinner from './Spinner.svelte';
	import { cleanText } from './utils';
	import { serviceError } from './dockerService';

	let model = $state('groq|qwen-qwq-32b');
	let selectedProvider = $derived(model.split('|')[0]);
	let selectedModel = $derived(model.split('|')[1]);

	let prompt = $state('Hey there, hello!');
	let system_prompt = $state('You are Luna, a young AI woman an space elf Vtuber');
	let loading = $state(false);
	let responseText = $state<string | null>(null);

	let forwardOutput = $state(true);

	let models = $state<{ provider: string; value: string; label: string }[]>([]);

	async function fetchModels() {
		try {
			const response = await fetch('/api/llm/models');
			if (response.ok) {
				const data = await response.json();
				models = data.models;
				if (!model && models.length > 0) {
					model = `${models[0].provider}|${models[0].value}`;
				}
			} else {
				console.error('Failed to fetch LLM options:', response.status, response.statusText);
				serviceError.set(`Failed to fetch LLM options: ${response.status} ${response.statusText}`);
			}
		} catch (error) {
			console.error('Error fetching LLM options:', error);
			serviceError.set(`Error fetching LLM options: ${error}`);
		}
	}

	async function generateResponse() {
		loading = true;
		responseText = '';
		serviceError.set(null);

		const response = await fetch('/api/llm/generate', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				provider: selectedProvider,
				model: selectedModel,
				system_prompt,
				prompt
			})
		});

		if (response.ok && response.body) {
			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let done = false;

			while (!done) {
				const { value, done: readerDone } = await reader.read();
				done = readerDone;
				const chunk = decoder.decode(value);
				if (chunk) {
					responseText += chunk;
				}
			}
		} else {
			serviceError.set(`Error generating response: ${response.status} ${response.statusText}`);
		}

		loading = false;

		if (forwardOutput && responseText) {
			llmOutput.set(cleanText(true, responseText));
		}
	}

	$effect(() => {
		fetchModels();
	});

	$effect(() => {
		const unsubscribe = promptOutput.subscribe((newPrompt) => {
			if (newPrompt) {
				if (newPrompt.systemPrompt !== system_prompt) {
					system_prompt = newPrompt.systemPrompt;
				}
				if (newPrompt.userPrompt !== prompt) {
					prompt = newPrompt.userPrompt;
				}
				generateResponse();
			}
		});

		return () => {
			unsubscribe();
		};
	});
</script>

<div class="card">
	<div class="card-header">
		<h2>
			<Icon path="M13 10V3L4 14h7v7l9-11h-7z" class="luna-text-primary-light icon-lg mr-2" />
			LLM Service
		</h2>
	</div>

	<div class="card-body">
		<div class="form-group">
			<label for="model">Model</label>
			<select id="model" bind:value={model} class="form-control">
				{#each models as modelOption}
					<option value={`${modelOption.provider}|${modelOption.value}`}>{modelOption.label}</option
					>
				{/each}
			</select>
		</div>

		<div class="form-group">
			<label for="systemPrompt">System Prompt</label>
			<textarea id="systemPrompt" bind:value={system_prompt} rows="3" class="form-control"
			></textarea>
		</div>

		<div class="form-group">
			<label for="prompt">User Prompt</label>
			<textarea id="prompt" bind:value={prompt} rows="4" class="form-control"></textarea>
		</div>

		<div class="form-group">
			<label class="flex-start space-x-2">
				<input type="checkbox" bind:checked={forwardOutput} />
				<span class="luna-text-subtle">Forward Output</span>
			</label>
		</div>

		<div class="form-group">
			<button onclick={generateResponse} disabled={loading} class="btn-primary">
				{#if loading}
					<Spinner class="luna-text-base icon-lg mr-2" />
				{/if}
				{loading ? 'Generating...' : 'Generate'}
			</button>
		</div>

		{#if responseText}
			<div class="form-group">
				<h3 class="luna-text-subtle mb-2 text-lg font-medium">Response</h3>
				<div class="form-control whitespace-pre-wrap p-4">
					{responseText}
				</div>
			</div>
		{/if}
	</div>
</div>
