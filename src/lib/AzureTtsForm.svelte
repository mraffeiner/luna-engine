<script lang="ts">
	import { generateSpeech, type AzureTtsRequestParams, ttsOptions } from './ttsService';
	import Icon from './Icon.svelte';
	import Spinner from './Spinner.svelte';
	import { serviceError } from './dockerService';

	let text = $state('Hi there hello');
	let language = $state('en-US');
	let voice = $state('en-US-NancyNeural');
	let style = $state('whispering');
	let rate = $state(20);
	let pitch = $state(17);

	let audioUrl = $state<string | null>(null);
	let loading = $state(false);

	export async function handleGenerateSpeech(_event?: MouseEvent, newText?: string): Promise<void> {
		serviceError.set(null);
		audioUrl = null;
		loading = true;

		if (newText) {
			text = newText;
		}

		const blob = await generateSpeech({
			engine: 'azure',
			language,
			voice,
			style,
			rate: rate + '%',
			pitch: pitch + '%',
			text
		} as AzureTtsRequestParams);

		if (blob) {
			audioUrl = URL.createObjectURL(blob);
		}

		loading = false;
	}
</script>

<div class="card p-6">
	<h3 class="mb-5 flex items-center">
		<Icon
			path="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
			class="luna-text-primary-light icon-sm mr-2"
		/>
		Azure Text-to-Speech
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
			<label for="language" class="luna-text-muted mb-2 block text-sm font-medium">Language</label>
			<div class="relative">
				<select id="language" bind:value={language} class="form-control">
					{#if $ttsOptions.engines['azure']?.languages}
						{#each $ttsOptions.engines['azure']?.languages as lang}
							<option value={lang.value}>{lang.label}</option>
						{/each}
					{/if}
				</select>
			</div>
		</div>
		<div class="mb-4">
			<label for="voice" class="luna-text-muted mb-2 block text-sm font-medium">Voice</label>
			<div class="relative">
				<select id="voice" bind:value={voice} class="form-control">
					{#if $ttsOptions.engines['azure']?.voices}
						{#each $ttsOptions.engines['azure'].voices as voiceOption}
							<option value={voiceOption.value}>{voiceOption.label}</option>
						{/each}
					{/if}
				</select>
			</div>
		</div>

		<div class="mb-4">
			<label for="style" class="luna-text-muted mb-2 block text-sm font-medium">Style</label>
			<div class="relative">
				<select id="style" bind:value={style} class="form-control">
					{#if $ttsOptions.engines['azure']?.styles}
						{#each $ttsOptions.engines['azure'].styles as styleOption}
							<option value={styleOption.value}>{styleOption.label}</option>
						{/each}
					{/if}
				</select>
			</div>
		</div>

		<div class="mb-4">
			<label for="rate" class="luna-text-muted mb-2 block text-sm font-medium">Rate</label>
			<div class="relative mt-1 px-1">
				<input
					id="rate"
					type="range"
					min="-100"
					max="100"
					bind:value={rate}
					class="luna-bg-elevated accent-primary h-2 w-full cursor-pointer appearance-none rounded-lg"
				/>
				<div class="luna-text-disabled mt-1 flex justify-between px-1 text-xs">
					<span>Slower</span>
					<span class="font-medium">{rate}%</span>
					<span>Faster</span>
				</div>
			</div>
		</div>
		<div class="mb-4">
			<label for="pitch" class="luna-text-muted mb-2 block text-sm font-medium">Pitch</label>
			<div class="relative mt-1 px-1">
				<input
					id="pitch"
					type="range"
					min="-100"
					max="100"
					bind:value={pitch}
					class="luna-bg-elevated accent-primary h-2 w-full cursor-pointer appearance-none rounded-lg"
				/>
				<div class="luna-text-disabled mt-1 flex justify-between px-1 text-xs">
					<span>Lower</span>
					<span class="font-medium">{pitch}%</span>
					<span>Higher</span>
				</div>
			</div>
		</div>
	</div>

	<div class="mt-6">
		<button
			onclick={handleGenerateSpeech}
			disabled={loading}
			class="luna-bg-primary luna-text-base hover:luna-bg-primary-hover focus:luna-border-focus items-center rounded-md px-5 py-2.5 font-semibold shadow-sm transition-colors duration-200 focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-50"
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
