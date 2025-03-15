<script lang="ts">
	import AzureTtsForm from './AzureTtsForm.svelte';
	import KokoroTtsForm from './KokoroTtsForm.svelte';
	import { ttsOptions, ttsError, fetchTtsOptions } from './ttsService';

	let selectedEngine = $state('kokoro');

	// Initialize options on component mount
	$effect(() => {
		fetchTtsOptions();
	});
</script>

<div class="card p-6">
	<h2 class="mb-6 flex items-center">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="mr-2 h-6 w-6 text-indigo-400"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
			/>
		</svg>
		Text-to-Speech
	</h2>

	<div class="mb-6">
		<label for="engine" class="mb-2 block text-sm font-medium text-gray-200">TTS Engine</label>
		<div class="relative">
			<select
				id="engine"
				bind:value={selectedEngine}
				class="block w-full appearance-none rounded-md border border-gray-600 bg-gray-700 p-3 text-white shadow-sm transition-colors duration-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 sm:text-sm"
			>
				{#each $ttsOptions.engines as engineOption}
					<option value={engineOption.value}>{engineOption.label}</option>
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

	{#if $ttsError}
		<div class="mb-6 rounded-md border border-red-800 bg-red-900 bg-opacity-30 p-3">
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

	<div class="mt-2">
		{#if selectedEngine === 'azure'}
			<AzureTtsForm />
		{:else if selectedEngine === 'kokoro'}
			<KokoroTtsForm />
		{:else}
			<div class="rounded-md border border-yellow-800 bg-yellow-900 bg-opacity-30 p-4">
				<p class="flex items-center text-yellow-400">
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
					Unsupported TTS engine selected: {selectedEngine}
				</p>
			</div>
		{/if}
	</div>
</div>
