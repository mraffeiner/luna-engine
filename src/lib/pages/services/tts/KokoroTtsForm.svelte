<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import {
		generateSpeech,
		type KokoroTtsRequestParams,
		loading,
		selectedTts,
		ttsOptions,
		type TtsParams
	} from './ttsService';

	let { active, text } = $props();

	let language = $state('en-US');
	let voice = $state('af_nicole');
	let useVoiceMix = $state(true);
	let voiceMix: { voice: string; weight: number }[] = $state([
		{ voice: 'af_nicole', weight: 2.5 },
		{ voice: 'am_echo', weight: 1.0 },
		{ voice: 'jf_alpha', weight: 1.0 },
		{ voice: 'zf_xiaoxiao', weight: 0.5 }
	]);
	let speed = $state(0.9);
	let pitch = $state(1.17);

	const voiceMixParams = $derived(voiceMix.map((v) => `${v.voice}(${v.weight})`).join('+'));

	const params: KokoroTtsRequestParams = $derived({
		engine: 'kokoro',
		language,
		voice: useVoiceMix ? voiceMixParams : voice,
		speed,
		pitch,
		text
	});

	function addVoice() {
		const kokoroVoices = $ttsOptions.engines['kokoro']?.voices || [];
		// Find a voice that's not already in the mix
		const unusedVoice = kokoroVoices.find((v) => !voiceMix.some((mix) => mix.voice === v.value));

		if (unusedVoice) {
			voiceMix = [...voiceMix, { voice: unusedVoice.value, weight: 1.0 }];
		}
	}

	function removeVoice(index: number) {
		voiceMix = voiceMix.filter((_, i) => i !== index);
	}

	function updateVoiceWeight(index: number, weight: number) {
		voiceMix = voiceMix.map((v, i) => (i === index ? { ...v, weight } : v));
	}

	function updateVoiceSelection(index: number, voiceValue: string) {
		voiceMix = voiceMix.map((v, i) => (i === index ? { ...v, voice: voiceValue } : v));
	}

	$effect(() => {
		if (active && params) {
			selectedTts.update((current: TtsParams) => ({
				...current,
				requestParams: params
			}));
		}
	});
</script>

<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
	<div class="form-group">
		<label for="text">Text</label>
		<textarea
			id="text"
			bind:value={text}
			placeholder="Enter text to convert to speech..."
			class="form-control"
		></textarea>
	</div>

	<div class="form-group">
		<label for="language">Language</label>
		<div class="relative">
			<select id="language" bind:value={language} class="form-control">
				{#if $ttsOptions.engines['kokoro']?.languages}
					{#each $ttsOptions.engines['kokoro'].languages as lang}
						<option value={lang.value}>{lang.label}</option>
					{/each}
				{/if}
			</select>
		</div>
	</div>

	<!-- Voice Mixing Toggle -->
	<div class="form-group col-span-1 lg:col-span-2">
		<div class="flex-start rounded-md">
			<label>
				<input type="checkbox" bind:checked={useVoiceMix} />
				<span>Use Voice Mix</span>
			</label>
		</div>
	</div>

	{#if !useVoiceMix}
		<!-- Single Voice Selection (when mixing is disabled) -->
		<div class="form-group">
			<label for="voice">Voice</label>
			<div class="relative">
				<select id="voice" bind:value={voice} class="form-control">
					{#if $ttsOptions.engines['kokoro']?.voices}
						{#each $ttsOptions.engines['kokoro'].voices as voiceOption}
							<option value={voiceOption.value}>{voiceOption.label}</option>
						{/each}
					{/if}
				</select>
			</div>
		</div>
	{:else}
		<!-- Voice Mixing UI (when mixing is enabled) -->
		<div class="form-group col-span-1 lg:col-span-2">
			<div class="mb-6">
				<label for="addVoice">Voice Mix</label>
			</div>
			{#each voiceMix as voice, i}
				<div class="mb-4 flex flex-wrap gap-3 rounded-md">
					<div class="min-w-[200px] flex-grow">
						<div class="relative">
							<select
								value={voice.voice}
								onchange={(e) => updateVoiceSelection(i, e.currentTarget.value)}
								class="form-control"
							>
								{#if $ttsOptions.engines['kokoro']?.voices}
									{#each $ttsOptions.engines['kokoro'].voices as voiceOption}
										<option value={voiceOption.value}>{voiceOption.label}</option>
									{/each}
								{/if}
							</select>
						</div>
					</div>
					<div class="flex min-w-[200px] flex-grow items-center gap-3">
						<input
							type="range"
							min="0.1"
							max="10.0"
							step="0.1"
							value={voice.weight}
							oninput={(e) => updateVoiceWeight(i, parseFloat(e.currentTarget.value))}
							class="flex-grow"
						/>
						<span class="text-text-muted w-12 text-sm font-medium">{voice.weight.toFixed(1)}</span>
					</div>
					<button
						type="button"
						onclick={() => removeVoice(i)}
						disabled={voiceMix.length <= 1}
						class="btn-danger"
					>
						<Icon
							path="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
							class="icon-sm mr-2"
						/>
						Remove
					</button>
				</div>
			{/each}
			<div class="flex-center mt-6">
				<button
					id="addVoice"
					type="button"
					onclick={addVoice}
					disabled={voiceMix.length >= ($ttsOptions.engines['kokoro']?.voices.length || 0)}
					class="btn-primary"
				>
					<Icon path="M12 6v6m0 0v6m0-6h6m-6 0H6" class="icon-sm mr-2" />
					Add Voice
				</button>
			</div>
		</div>
	{/if}
	<div class="form-group">
		<label for="speed">Speed</label>
		<div class="relative mt-1 px-1">
			<input id="speed" type="range" min="0.5" max="2.0" step="0.01" bind:value={speed} />
			<div class="text-text-disabled flex-between mt-2 px-1 text-xs">
				<span>Slower</span>
				<span class="bg-bg-elevated text-primary-light rounded-md px-2 py-1 font-medium"
					>{speed}x</span
				>
				<span>Faster</span>
			</div>
		</div>
	</div>

	<div class="form-group">
		<label for="pitch">Pitch</label>
		<div class="relative mt-1 px-1">
			<input id="pitch" type="range" min="0.5" max="2.0" step="0.01" bind:value={pitch} />
			<div class="text-text-disabled flex-between mt-2 px-1 text-xs">
				<span>Lower</span>
				<span class="bg-bg-elevated text-primary-light rounded-md px-2 py-1 font-medium"
					>{pitch}x</span
				>
				<span>Higher</span>
			</div>
		</div>
	</div>
</div>

<div class="mt-6">
	<button onclick={generateSpeech} disabled={$loading} class="btn-primary">
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
