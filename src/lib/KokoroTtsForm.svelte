<script lang="ts">
	import {
		ttsError,
		generateSpeech,
		getVoicesByEngine,
		getLanguagesByEngine,
		type KokoroTtsRequestParams,
		type VoiceWeight
	} from './ttsService';

	let text = $state('Hi there hello');
	let language = $state('en-US');
	let voice = $state('af_bella'); // Fallback for single voice mode
	let speed = $state(1.15);
	let pitch = $state(1.1);

	// Voice mixing
	let useVoiceMix = $state(true);
	let voiceMix = $state<VoiceWeight[]>([
		{ voice: 'af_nicole', weight: 5.0 },
		{ voice: 'am_echo', weight: 2.0 },
		{ voice: 'jf_alpha', weight: 2.0 },
		{ voice: 'zf_xiaoxiao', weight: 2.0 }
	]);

	let audioUrl = $state<string | null>(null);
	let loading = $state(false);

	function addVoice() {
		const kokoroVoices = getVoicesByEngine('kokoro');
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
		if (newText) {
			text = newText;
		}

		loading = true;
		audioUrl = null;
		ttsError.set(null);

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
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="mr-2 h-5 w-5 text-indigo-400"
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
		Kokoro Text-to-Speech
	</h3>

	<div class="grid grid-cols-1 gap-5 md:grid-cols-2">
		<div class="mb-4">
			<label for="text" class="mb-2 block text-sm font-medium text-gray-200">Text</label>
			<textarea
				id="text"
				bind:value={text}
				rows="4"
				placeholder="Enter text to convert to speech..."
				class="block w-full resize-none rounded-md border border-gray-600 bg-gray-700 p-3 text-white shadow-sm transition-colors duration-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 sm:text-sm"
			></textarea>
		</div>

		<div class="mb-4">
			<label for="language" class="mb-2 block text-sm font-medium text-gray-200">Language</label>
			<div class="relative">
				<select
					id="language"
					bind:value={language}
					class="block w-full appearance-none rounded-md border border-gray-600 bg-gray-700 p-3 text-white shadow-sm transition-colors duration-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 sm:text-sm"
				>
					{#each getLanguagesByEngine('kokoro') as lang}
						<option value={lang.value}>{lang.label}</option>
					{/each}
				</select>
				<div
					class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-400"
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

		<!-- Voice Mixing Toggle -->
		<div class="col-span-1 mb-4 md:col-span-2">
			<div class="flex items-center rounded-md border border-gray-600 bg-gray-800 p-3">
				<input
					id="useVoiceMix"
					type="checkbox"
					bind:checked={useVoiceMix}
					class="h-5 w-5 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500"
				/>
				<label for="useVoiceMix" class="ml-3 block text-sm font-medium text-gray-200">
					Enable Voice Mixing (blend multiple voices together)
				</label>
			</div>
		</div>

		{#if !useVoiceMix}
			<!-- Single Voice Selection (when mixing is disabled) -->
			<div class="mb-4">
				<label for="voice" class="mb-2 block text-sm font-medium text-gray-200">Voice</label>
				<div class="relative">
					<select
						id="voice"
						bind:value={voice}
						class="block w-full appearance-none rounded-md border border-gray-600 bg-gray-700 p-3 text-white shadow-sm transition-colors duration-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 sm:text-sm"
					>
						{#each getVoicesByEngine('kokoro') as voiceOption}
							<option value={voiceOption.value}>{voiceOption.label}</option>
						{/each}
					</select>
					<div
						class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-400"
					>
						<svg
							class="h-4 w-4"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M19 9l-7 7-7-7"
							></path>
						</svg>
					</div>
				</div>
			</div>
		{:else}
			<!-- Voice Mixing UI (when mixing is enabled) -->
			<div class="col-span-1 mb-4 md:col-span-2">
				<div class="mb-3 flex items-center justify-between">
					<label for="addVoice" class="block text-sm font-medium text-gray-200">Voice Mix</label>
					<button
						id="addVoice"
						type="button"
						onclick={addVoice}
						disabled={voiceMix.length >= getVoicesByEngine('kokoro').length}
						class="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm transition-colors duration-200 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 disabled:cursor-not-allowed disabled:opacity-50"
					>
						<span class="flex items-center">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="mr-1 h-4 w-4"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 6v6m0 0v6m0-6h6m-6 0H6"
								/>
							</svg>
							Add Voice
						</span>
					</button>
				</div>

				<div class="custom-scrollbar max-h-60 space-y-3 overflow-y-auto pr-1">
					{#each voiceMix as voice, i}
						<div class="flex flex-wrap gap-2 rounded-md border border-gray-600 bg-gray-800 p-3">
							<div class="min-w-[200px] flex-grow">
								<div class="relative">
									<select
										value={voice.voice}
										onchange={(e) => updateVoiceSelection(i, e.currentTarget.value)}
										class="w-full appearance-none rounded-md border border-gray-600 bg-gray-700 p-2 text-sm text-white"
									>
										{#each getVoicesByEngine('kokoro') as voiceOption}
											<option value={voiceOption.value}>{voiceOption.label}</option>
										{/each}
									</select>
									<div
										class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400"
									>
										<svg
											class="h-4 w-4"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											xmlns="http://www.w3.org/2000/svg"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 9l-7 7-7-7"
											></path>
										</svg>
									</div>
								</div>
							</div>
							<div class="flex min-w-[200px] flex-grow items-center gap-2">
								<input
									type="range"
									min="0.1"
									max="10.0"
									step="0.1"
									value={voice.weight}
									oninput={(e) => updateVoiceWeight(i, parseFloat(e.currentTarget.value))}
									class="h-2 flex-grow cursor-pointer appearance-none rounded-lg bg-gray-600 accent-indigo-500"
								/>
								<span class="w-12 text-sm font-medium text-gray-300">{voice.weight.toFixed(1)}</span
								>
							</div>
							<button
								type="button"
								onclick={() => removeVoice(i)}
								disabled={voiceMix.length <= 1}
								class="rounded-md bg-red-700 px-2 py-1 text-xs font-bold text-white transition-colors duration-200 hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-700 disabled:cursor-not-allowed disabled:opacity-50"
							>
								<span class="flex items-center">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="mr-1 h-3 w-3"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
										/>
									</svg>
									Remove
								</span>
							</button>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<div class="mb-4">
			<label for="speed" class="mb-2 block text-sm font-medium text-gray-200">Speed</label>
			<div class="relative mt-1 px-1">
				<input
					id="speed"
					type="range"
					min="0.5"
					max="2.0"
					step="0.01"
					bind:value={speed}
					class="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-600 accent-indigo-500"
				/>
				<div class="mt-1 flex justify-between px-1 text-xs text-gray-400">
					<span>Slower</span>
					<span class="font-medium">{speed}x</span>
					<span>Faster</span>
				</div>
			</div>
		</div>

		<div class="mb-4">
			<label for="pitch" class="mb-2 block text-sm font-medium text-gray-200">Pitch</label>
			<div class="relative mt-1 px-1">
				<input
					id="pitch"
					type="range"
					min="0.5"
					max="2.0"
					step="0.01"
					bind:value={pitch}
					class="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-600 accent-indigo-500"
				/>
				<div class="mt-1 flex justify-between px-1 text-xs text-gray-400">
					<span>Lower</span>
					<span class="font-medium">{pitch}x</span>
					<span>Higher</span>
				</div>
			</div>
		</div>
	</div>

	{#if $ttsError}
		<div class="my-4 rounded-md border border-red-800 bg-red-900 bg-opacity-30 p-3">
			<p class="flex items-center text-red-400">
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
			class="inline-flex items-center rounded-md bg-indigo-600 px-5 py-2.5 font-semibold text-white shadow-sm transition-colors duration-200 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 disabled:cursor-not-allowed disabled:opacity-50"
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
			{loading ? 'Generating...' : 'Generate Speech'}
		</button>
	</div>

	{#if audioUrl}
		<div class="mt-6 rounded-lg border border-gray-600 bg-gray-800 p-4">
			<h4 class="mb-2 flex items-center text-sm font-medium text-gray-300">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="mr-1 h-4 w-4 text-green-500"
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

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 8px;
	}

	.custom-scrollbar::-webkit-scrollbar-track {
		background: #374151;
		border-radius: 4px;
	}

	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #4b5563;
		border-radius: 4px;
	}

	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: #6b7280;
	}
</style>
