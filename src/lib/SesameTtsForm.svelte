<script lang="ts">
	import { generateSpeech, ttsError, ttsOptions, type SesameTtsRequestParams } from './ttsService';

	let text = $state('Hi there hello');
	let voice = $state('alloy');

	let audioUrl = $state<string | null>(null);
	let loading = $state(false);

	export async function handleGenerateSpeech(_event?: MouseEvent, newText?: string): Promise<void> {
		ttsError.set(null);
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
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="luna-text-primary-light mr-2 h-5 w-5"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
			/>
		</svg>
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
				class="luna-border-subtle luna-bg-elevated luna-text-base focus:border-primary focus:ring-primary block w-full resize-none rounded-md border p-3 shadow-sm transition-colors duration-200 focus:ring-2 sm:text-sm"
			></textarea>
		</div>

		<div class="mb-4">
			<label for="voice" class="luna-text-muted mb-2 block text-sm font-medium">Voice</label>
			<div class="relative">
				<select
					id="voice"
					bind:value={voice}
					class="luna-border-subtle luna-bg-elevated luna-text-base focus:border-primary focus:ring-primary block w-full appearance-none rounded-md border p-3 shadow-sm transition-colors duration-200 focus:ring-2 sm:text-sm"
				>
					{#if $ttsOptions.engines['sesame']?.voices}
						{#each $ttsOptions.engines['sesame'].voices as voiceOption}
							<option value={voiceOption.value}>{voiceOption.label}</option>
						{/each}
					{/if}
				</select>
				<div
					class="luna-text-disabled pointer-events-none absolute inset-y-0 right-0 flex items-center px-3"
				>
					<svg
						class="h-4 w-4"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"
						></path>
					</svg>
				</div>
			</div>
		</div>
	</div>

	{#if $ttsError}
		<div class="alert-error my-4 rounded-md p-3">
			<p class="luna-text-danger-light flex items-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="mr-2 h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
					/>
				</svg>
				{$ttsError}
			</p>
		</div>
	{/if}

	<div class="mt-6">
		<button
			onclick={handleGenerateSpeech}
			disabled={loading}
			class="luna-bg-primary luna-text-base hover:luna-bg-primary-hover focus:luna-border-focus inline-flex items-center rounded-md px-5 py-2.5 font-semibold shadow-sm transition-colors duration-200 focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-50"
		>
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
			{loading ? 'Generating...' : 'Generate Speech'}
		</button>
	</div>

	{#if audioUrl}
		<div class="luna-border-subtle luna-bg-surface mt-6 rounded-lg border p-4">
			<h4 class="luna-text-muted mb-2 flex items-center text-sm font-medium">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="luna-text-success mr-1 h-4 w-4"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
					/>
				</svg>
				Generated Audio
			</h4>
			<audio controls autoplay={true} src={audioUrl} class="w-full rounded-md"></audio>
		</div>
	{/if}
</div>
