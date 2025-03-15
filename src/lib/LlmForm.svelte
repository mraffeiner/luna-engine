<script lang="ts">
	import { llmOutput, sttOutput } from './stores';

	let model = $state('gpt-4o-mini');
	let prompt = $state('Hi there');
	let loading = $state(false);
	let errorMessage = $state<string | null>(null);
	let responseText = $state<string | null>(null);
	let forwardToTts = $state(false);

	let models = $state<{ value: string; label: string }[]>([]);
	let localErrorMessage = $state<string | null>(null);

	const displayError = $derived(errorMessage || localErrorMessage);

	async function fetchModels() {
		try {
			const response = await fetch('/api/llm/options');
			if (response.ok) {
				const data = await response.json();
				models = data.models;
				if (models.length > 0 && !model) {
					model = models[0].value;
				}
			} else {
				console.error('Failed to fetch LLM options:', response.status, response.statusText);
				localErrorMessage = `Failed to fetch LLM options: ${response.status} ${response.statusText}`;
			}
		} catch (error) {
			console.error('Error fetching LLM options:', error);
			localErrorMessage = `Error fetching LLM options: ${error}`;
		}
	}

	async function generateResponse() {
		loading = true;
		responseText = '';
		errorMessage = null;

		const response = await fetch('/api/llm/chat', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				model,
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
			errorMessage = `Error generating response: ${response.status} ${response.statusText}`;
		}

		loading = false;

		if (forwardToTts && responseText) {
			llmOutput.set(responseText);
		}
	}

	$effect(() => {
		const unsubscribe = sttOutput.subscribe((newPrompt) => {
			if (newPrompt) {
				prompt = newPrompt;
				generateResponse();
			}
		});
		
		fetchModels();
		
		return () => {
			unsubscribe;
			sttOutput.set(null);
		}
	});
</script>

<div class="rounded-lg bg-gray-700 p-6 shadow-md">
	<h2 class="mb-4 text-2xl font-semibold text-white">LLM Service</h2>

	<div class="mb-4">
		<label for="model" class="block text-sm font-medium text-gray-200">Model</label>
		<select
			id="model"
			bind:value={model}
			class="mt-1 block w-full rounded-md border-gray-600 bg-gray-800 p-2 text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
		>
			{#each models as modelOption}
				<option value={modelOption.value}>{modelOption.label}</option>
			{/each}
		</select>
	</div>

	<div class="grid grid-cols-1 gap-4 md:grid-cols-1">
		<div class="mb-4">
			<label for="prompt" class="block text-sm font-medium text-gray-200">Prompt</label>
			<textarea
				id="prompt"
				bind:value={prompt}
				rows="4"
				class="mt-1 block w-full rounded-md border-gray-600 bg-gray-800 p-2 text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
			></textarea>
		</div>
	</div>

	{#if displayError}
		<p class="mt-4 text-red-500">{displayError}</p>
	{/if}

	<div class="mt-4">
		<label class="inline-flex items-center space-x-2">
			<input type="checkbox" class="rounded border-gray-600 text-indigo-600 focus:ring-indigo-500" bind:checked={forwardToTts} />
			<span class="text-gray-200">Forward to TTS</span>
		</label>
	</div>

	<div class="mt-6">
		<button
			onclick={generateResponse}
			disabled={loading}
			class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
		>
			{#if loading}
				<svg
					class="-ml-1 mr-3 h-5 w-5 animate-spin text-white"
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
				>
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					></path>
				</svg>
			{/if}
			{loading ? 'Generating...' : 'Generate'}
		</button>
	</div>

	{#if responseText}
		<div class="mt-4">
			<h3 class="text-lg font-semibold text-white">Response</h3>
			<div class="mt-2 rounded-md bg-gray-800 p-2 text-white" style="white-space: pre-wrap;">
				{responseText}
			</div>
		</div>
	{/if}
</div>
