<script lang="ts">
	import { generateSpeech, ttsOptions, type SesameTtsRequestParams } from './ttsService';
	import Icon from './Icon.svelte';
	import Spinner from './Spinner.svelte';
	import { serviceError } from './dockerService';

	let text = $state('Hi there hello');
	let voice = $state('alloy');

	let audioUrl = $state<string | null>(null);
	let loading = $state(false);

	export async function handleGenerateSpeech(_event?: MouseEvent, newText?: string): Promise<void> {
		serviceError.set(null);
		audioUrl = null;
		loading = true;

		if (newText) {
			text = newText;
		}

		const params: SesameTtsRequestParams = {
			engine: 'sesame',
			voice,
			text
		};

		const audioBlob = await generateSpeech(params);
		if (audioBlob) {
			audioUrl = URL.createObjectURL(audioBlob);
		}

		loading = false;
	}
</script>

<div class="card p-6">
	<h3 class="mb-5 flex items-center">
		<Icon
			path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
			class="luna-text-primary-light icon-sm mr-2"
		/>
		Sesame Text-to-Speech
	</h3>

	<div class="grid grid-cols-1 gap-5 md:grid-cols-2">
		<div class="mb-4">
			<label for="text" class="luna-text-muted mb-2 block text-sm font-medium">Text</label>
			<textarea
				id="text"
				bind:value={text}
				rows="4"
				placeholder="Enter text to convert to speech..."
				class="form-control"
			></textarea>
		</div>

		<div class="mb-4">
			<label for="voice" class="luna-text-muted mb-2 block text-sm font-medium">Voice</label>
			<div class="relative">
				<select id="voice" bind:value={voice} class="form-control">
					{#if $ttsOptions.engines['sesame']?.voices}
						{#each $ttsOptions.engines['sesame'].voices as voiceOption}
							<option value={voiceOption.value}>{voiceOption.label}</option>
						{/each}
					{/if}
				</select>
			</div>
		</div>
	</div>

	<div class="mt-6">
		<button
			onclick={handleGenerateSpeech}
			disabled={loading}
			class="luna-bg-primary luna-text-base hover:luna-bg-primary-hover focus:luna-border-focus flex items-center rounded-md px-5 py-2.5 font-semibold shadow-sm transition-colors duration-200 focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-50"
		>
			{#if loading}
				<Spinner class="luna-text-base icon-lg mr-2" />
			{/if}
			{loading ? 'Generating...' : 'Generate Speech'}
		</button>
	</div>

	{#if audioUrl}
		<div class="luna-border-subtle luna-bg-surface mt-6 rounded-lg border p-4">
			<h4 class="luna-text-muted mb-2 flex items-center text-sm font-medium">
				<Icon
					path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
					class="luna-text-success icon-sm mr-1"
				/>
				Generated Audio
			</h4>
			<audio controls autoplay={true} src={audioUrl} class="w-full rounded-md"></audio>
		</div>
	{/if}
</div>
