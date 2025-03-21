<script lang="ts">
	import {
		ttsError,
		generateSpeech,
		type KokoroTtsRequestParams,
		type VoiceWeight,
		ttsOptions
	} from './ttsService';
	import Icon from './Icon.svelte';
	import Spinner from './Spinner.svelte';

	let text = $state('Hi there hello');
	let language = $state('en-US');
	let voice = $state('af_nicole');
	// Voice mixing
	let useVoiceMix = $state(true);
	let voiceMix = $state<VoiceWeight[]>([
		{ voice: 'af_nicole', weight: 2.5 },
		{ voice: 'am_echo', weight: 1.0 },
		{ voice: 'jf_alpha', weight: 1.0 },
		{ voice: 'zf_xiaoxiao', weight: 0.5 }
	]);
	let speed = $state(0.9);
	let pitch = $state(1.17);

	let audioUrl = $state<string | null>(null);
	let loading = $state(false);

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

	export async function handleGenerateSpeech(_event?: MouseEvent, newText?: string): Promise<void> {
		ttsError.set(null);
		audioUrl = null;
		loading = true;

		if (newText) {
			text = newText;
		}

		const params: KokoroTtsRequestParams = {
			engine: 'kokoro',
			language,
			voice: useVoiceMix ? voiceMix[0].voice : voice, // Fallback voice
			speed,
			pitch,
			text
		};

		// Add voice mix if enabled
		if (useVoiceMix && voiceMix.length > 0) {
			params.voiceMix = voiceMix;
		}

		const blob = await generateSpeech(params);

		if (blob) {
			audioUrl = URL.createObjectURL(blob);
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
		Kokoro Text-to-Speech
	</h3>

	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<div class="form-group">
			<label for="text" class="luna-text-muted mb-2 block text-sm font-medium">Text</label>
			<textarea
				id="text"
				bind:value={text}
				placeholder="Enter text to convert to speech..."
				class="form-control"
			></textarea>
		</div>

		<div class="form-group">
			<label for="language" class="luna-text-muted mb-2 block text-sm font-medium">Language</label>
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
			<div
				class="glass-effect luna-border-subtle flex items-center rounded-md border p-4 shadow-sm"
			>
				<input
					id="useVoiceMix"
					type="checkbox"
					bind:checked={useVoiceMix}
					class="luna-border-subtle luna-bg-elevated luna-text-primary focus:ring-primary h-5 w-5 rounded"
				/>
				<label for="useVoiceMix" class="luna-text-muted ml-3 block text-sm font-medium">
					Enable Voice Mixing (blend multiple voices together)
				</label>
			</div>
		</div>

		{#if !useVoiceMix}
			<!-- Single Voice Selection (when mixing is disabled) -->
			<div class="form-group">
				<label for="voice" class="luna-text-muted mb-2 block text-sm font-medium">Voice</label>
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
				<div class="mb-3 flex items-center justify-between">
					<label for="addVoice" class="luna-text-muted block text-sm font-medium">Voice Mix</label>
					<button
						id="addVoice"
						type="button"
						onclick={addVoice}
						disabled={voiceMix.length >= ($ttsOptions.engines['kokoro']?.voices.length || 0)}
						class="btn-primary btn-sm btn-icon"
					>
						<Icon path="M12 6v6m0 0v6m0-6h6m-6 0H6" class="icon-sm" />
						Add Voice
					</button>
				</div>

				<div class="custom-scrollbar max-h-[min(40vh,400px)] space-y-3 overflow-y-auto pr-1">
					{#each voiceMix as voice, i}
						<div
							class="glass-effect luna-border-subtle hover:luna-border-hover flex flex-wrap gap-3 rounded-md border p-4 shadow-sm transition-all duration-200"
						>
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
								<span class="luna-text-muted w-12 text-sm font-medium"
									>{voice.weight.toFixed(1)}</span
								>
							</div>
							<button
								type="button"
								onclick={() => removeVoice(i)}
								disabled={voiceMix.length <= 1}
								class="btn-danger btn-sm btn-icon"
							>
								<Icon
									path="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
									class="icon-sm"
								/>
								Remove
							</button>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<div class="form-group">
			<label for="speed" class="luna-text-muted mb-2 block text-sm font-medium">Speed</label>
			<div class="relative mt-1 px-1">
				<input id="speed" type="range" min="0.5" max="2.0" step="0.01" bind:value={speed} />
				<div class="luna-text-disabled mt-2 flex justify-between px-1 text-xs">
					<span>Slower</span>
					<span class="luna-bg-elevated luna-text-primary-light rounded-md px-2 py-1 font-medium"
						>{speed}x</span
					>
					<span>Faster</span>
				</div>
			</div>
		</div>

		<div class="form-group">
			<label for="pitch" class="luna-text-muted mb-2 block text-sm font-medium">Pitch</label>
			<div class="relative mt-1 px-1">
				<input id="pitch" type="range" min="0.5" max="2.0" step="0.01" bind:value={pitch} />
				<div class="luna-text-disabled mt-2 flex justify-between px-1 text-xs">
					<span>Lower</span>
					<span class="luna-bg-elevated luna-text-primary-light rounded-md px-2 py-1 font-medium"
						>{pitch}x</span
					>
					<span>Higher</span>
				</div>
			</div>
		</div>
	</div>

	{#if $ttsError}
		<div class="animate-fadeIn alert-error my-5 rounded-md border p-4 shadow-md">
			<p class="luna-text-danger-light flex items-center">
				<Icon
					path="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
					class="icon-sm mr-2"
				/>
				{$ttsError}
			</p>
		</div>
	{/if}

	<div class="mt-6">
		<button onclick={handleGenerateSpeech} disabled={loading} class="btn-primary btn-icon">
			{#if loading}
				<Spinner class="luna-text-base icon-lg mr-2" />
				<span>Generating...</span>
			{:else}
				<Icon
					path="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
					class="icon-sm"
				/>
				<span>Generate Speech</span>
			{/if}
		</button>
	</div>

	{#if audioUrl}
		<div
			class="glass-effect animate-slideInUp luna-border-primary mt-6 rounded-xl border p-4 shadow-lg"
		>
			<h4 class="luna-text-primary-light mb-3 flex items-center text-sm font-medium">
				<Icon
					path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
					class="luna-text-success icon-sm mr-2"
				/>
				Generated Audio
			</h4>
			<audio controls autoplay={true} src={audioUrl} class="w-full rounded-md"></audio>
		</div>
	{/if}
</div>
