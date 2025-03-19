<script lang="ts">
	import { llmOutput, promptOutput } from './stores';

	let model = $state('deepseek-r1-distill-llama-70b');
	let prompt = $state('Hey');
	let system_prompt = $state('You are Luna, a young AI woman an space elf Vtuber');
	let loading = $state(false);
	let errorMessage = $state<string | null>(null);
	let responseText = $state<string | null>(null);

	let forwardOutput = $state(true);

	let models = $state<{ value: string; label: string }[]>([]);
	let localErrorMessage = $state<string | null>(null);

	const displayError = $derived(errorMessage || localErrorMessage);

	async function fetchModels() {
		try {
			const response = await fetch('/api/llm/models');
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

		const response = await fetch('/api/llm/generate', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				model,
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
			errorMessage = `Error generating response: ${response.status} ${response.statusText}`;
		}

		loading = false;

		if (forwardOutput && responseText) {
			llmOutput.set(responseText.replace(/<think\b[^>]*>[\s\S]*?<\/think>/gi, '').trim());
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
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="icon icon-lg icon-primary mr-2"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M13 10V3L4 14h7v7l9-11h-7z"
			/>
		</svg>
		<h2>LLM Service</h2>
	</div>

	<div class="card-body">
		{#if displayError}
			<div class="alert-error">
				<p>{displayError}</p>
			</div>
		{/if}

		<div class="form-group">
			<label for="model">Model</label>
			<select id="model" bind:value={model} class="form-control">
				{#each models as modelOption}
					<option value={modelOption.value}>{modelOption.label}</option>
				{/each}
			</select>
		</div>

		<div class="form-group">
			<label for="system_prompt">System Prompt</label>
			<textarea id="system_prompt" bind:value={system_prompt} rows="3" class="form-control"
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
					<svg
						class="luna-text-base -ml-1 mr-3 h-5 w-5 animate-spin"
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
			<div class="form-group">
				<h3 class="luna-text-subtle mb-2 text-lg font-medium">Response</h3>
				<div class="form-control whitespace-pre-wrap p-4">
					{responseText}
				</div>
			</div>
		{/if}
	</div>
</div>
