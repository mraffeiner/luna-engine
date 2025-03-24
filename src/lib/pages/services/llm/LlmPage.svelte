<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import { receiveInput, serviceOutput } from '$lib/shared/shared.svelte';
	import { cleanText } from '$lib/shared/utils';
	import { serviceError } from '../docker/dockerService';
	import ServicePage from '../ServicePage.svelte';

	let currentModelOption = $state('groq|qwen-qwq-32b|true');
	let [selectedProvider, selectedModel, selectedIsReasoning] = $derived(
		currentModelOption.split('|')
	);

	let prompt = $state('Hey there, hello!');
	let system_prompt = $state('You are Luna, a young AI woman an space elf Vtuber');
	let loading = $state(false);
	let responseText = $state<string | null>(null);

	let models = $state<{ provider: string; id: string; name: string; isReasoning: boolean }[]>([]);

	async function fetchModels() {
		try {
			const response = await fetch('/api/llm/models');
			if (response.ok) {
				models = await response.json();
				if (!currentModelOption && models.length > 0) {
					currentModelOption = `${models[0].provider}|${models[0].id}|${models[0].isReasoning}`;
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

	export async function generateResponse() {
		loading = true;
		responseText = '';

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
				const chunk = decoder.decode(value, { stream: true });
				if (chunk) {
					responseText += chunk;
				}
			}
		} else {
			serviceError.set(`Error generating response: ${response.status} ${response.statusText}`);
		}

		loading = false;

		serviceOutput.llm = cleanText(selectedIsReasoning.toLowerCase() === 'true', responseText);
	}

	$effect(() => {
		fetchModels();
	});

	$effect(() => {
		if (receiveInput.llm && serviceOutput.prompt) {
			system_prompt = serviceOutput.prompt.system;
			prompt = serviceOutput.prompt.user;
		}
	});
</script>

<ContentPage name="llm-page">
	<ServicePage serviceName="llm-service">
		<Card title="LLM Settings">
			<div class="flex-start">
				<label>
					<input type="checkbox" bind:checked={receiveInput.llm} />
					<span>Receive Input</span>
				</label>
			</div>

			<div class="form-group">
				<label for="model">Model</label>
				<select id="model" bind:value={currentModelOption} class="form-control">
					{#each models as modelOption}
						<option value={`${modelOption.provider}|${modelOption.id}|${modelOption.isReasoning}`}
							>{modelOption.name}</option
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

			<div>
				<button onclick={generateResponse} disabled={loading} class="btn-primary">
					{#if loading}
						<Spinner class="icon-lg text-text-base mr-2" />
					{/if}
					{loading ? 'Generating...' : 'Generate'}
				</button>
			</div>

			{#if responseText}
				<div class="form-group">
					<h3 class="text-text-subtle mb-2 text-lg font-medium">Response</h3>
					<div class="form-control whitespace-pre-wrap p-4">
						{responseText}
					</div>
				</div>
			{/if}
		</Card>
	</ServicePage>
</ContentPage>
