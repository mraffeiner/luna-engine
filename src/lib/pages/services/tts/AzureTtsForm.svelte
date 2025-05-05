<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import {
		type AzureTtsRequestParams,
		generateSpeech,
		loading,
		selectedTts,
		ttsOptions,
		type TtsParams
	} from './ttsService';

	let { active, text } = $props();

	let language = $state('en-US');
	let voice = $state('en-US-NancyNeural');
	let style = $state('whispering');
	let rate = $state(20);
	let pitch = $state(17);

	const params: AzureTtsRequestParams = $derived({
		engine: 'azure',
		language,
		voice,
		style,
		rate: rate + '%',
		pitch: pitch + '%',
		text,
		save: false
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
		<label for="language">Language</label>
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
		<label for="voice">Voice</label>
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
		<label for="style">Style</label>
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
		<label for="rate">Rate</label>
		<div class="relative mt-1 px-1">
			<input
				id="rate"
				type="range"
				min="-100"
				max="100"
				bind:value={rate}
				class="bg-bg-elevated accent-primary h-2 w-full cursor-pointer appearance-none rounded-lg"
			/>
			<div class="text-text-disabled flex-between mt-1 px-1 text-xs">
				<span>Slower</span>
				<span class="font-medium">{rate}%</span>
				<span>Faster</span>
			</div>
		</div>
	</div>
	<div class="mb-4">
		<label for="pitch">Pitch</label>
		<div class="relative mt-1 px-1">
			<input
				id="pitch"
				type="range"
				min="-100"
				max="100"
				bind:value={pitch}
				class="bg-bg-elevated accent-primary h-2 w-full cursor-pointer appearance-none rounded-lg"
			/>
			<div class="text-text-disabled flex-between mt-1 px-1 text-xs">
				<span>Lower</span>
				<span class="font-medium">{pitch}%</span>
				<span>Higher</span>
			</div>
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
