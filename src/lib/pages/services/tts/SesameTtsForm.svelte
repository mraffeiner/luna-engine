<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import {
		generateSpeech,
		loading,
		selectedTts,
		type SesameTtsRequestParams,
		ttsOptions,
		type TtsParams
	} from './ttsService';

	let { active, text } = $props();

	let voice = $state('alloy');

	const params: SesameTtsRequestParams = $derived({
		engine: 'sesame',
		voice,
		text
	});

	$effect(() => {
		if (active && params) {
			selectedTts.update((current: TtsParams) => ({
				...current,
				requestParams: params
			}));
		}
	});
</script>

<div class="grid grid-cols-1 gap-5 md:grid-cols-2">
	<div class="mb-4">
		<label for="text">Text</label>
		<textarea
			id="text"
			bind:value={text}
			rows="4"
			placeholder="Enter text to convert to speech..."
			class="form-control"
		></textarea>
	</div>

	<div class="mb-4">
		<label for="voice">Voice</label>
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
	<button onclick={() => generateSpeech($selectedTts)} disabled={$loading} class="btn-primary">
		{#if $loading}
			<Spinner class="text-text-base icon-lg mr-2" />
			<span>Generating...</span>
		{:else}
			<Icon
				path="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
				class="icon-lg mr-2"
			/>
			<span>Generate Speech</span>
		{/if}
	</button>
</div>
