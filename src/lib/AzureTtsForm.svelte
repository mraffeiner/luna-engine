<script lang="ts">
	import { llmOutput } from './stores';
	import {
		ttsOptions,
		ttsError,
		generateSpeech,
		getVoicesByEngine,
		type AzureTtsRequestParams
	} from './ttsService';

	let text = $state('Hi there hello');
	let language = $state('en-US');
	let voice = $state('en-US-NancyNeural');
	let style = $state('whispering');
	let rate = $state(20);
	let pitch = $state(17);

	let audioUrl = $state<string | null>(null);
	let loading = $state(false);

	async function handleGenerateSpeech() {
		loading = true;
		audioUrl = null;
		ttsError.set(null);

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

	$effect(() => {
		const unsubscribe = llmOutput.subscribe((newText) => {
			if (newText) {
				text = newText;
				handleGenerateSpeech();
			}
		});
		return () => {
			unsubscribe;
			llmOutput.set(null);
		}
	});
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
				d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
			/>
		</svg>
		Azure Text-to-Speech
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
					{#each $ttsOptions.languages as lang}
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
		<div class="mb-4">
			<label for="voice" class="mb-2 block text-sm font-medium text-gray-200">Voice</label>
			<div class="relative">
				<select
					id="voice"
					bind:value={voice}
					class="block w-full appearance-none rounded-md border border-gray-600 bg-gray-700 p-3 text-white shadow-sm transition-colors duration-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 sm:text-sm"
				>
					{#each getVoicesByEngine('azure') as voiceOption}
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
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"
						></path>
					</svg>
				</div>
			</div>
		</div>

		<div class="mb-4">
			<label for="style" class="mb-2 block text-sm font-medium text-gray-200">Style</label>
			<div class="relative">
				<select
					id="style"
					bind:value={style}
					class="block w-full appearance-none rounded-md border border-gray-600 bg-gray-700 p-3 text-white shadow-sm transition-colors duration-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 sm:text-sm"
				>
					{#each $ttsOptions.styles as styleOption}
						<option value={styleOption.value}>{styleOption.label}</option>
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

		<div class="mb-4">
			<label for="rate" class="mb-2 block text-sm font-medium text-gray-200">Rate</label>
			<div class="relative mt-1 px-1">
				<input
					id="rate"
					type="range"
					min="-100"
					max="100"
					bind:value={rate}
					class="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-600 accent-indigo-500"
				/>
				<div class="mt-1 flex justify-between px-1 text-xs text-gray-400">
					<span>Slower</span>
					<span class="font-medium">{rate}%</span>
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
					min="-100"
					max="100"
					bind:value={pitch}
					class="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-600 accent-indigo-500"
				/>
				<div class="mt-1 flex justify-between px-1 text-xs text-gray-400">
					<span>Lower</span>
					<span class="font-medium">{pitch}%</span>
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
