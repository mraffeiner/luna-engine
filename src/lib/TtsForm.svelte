<script lang="ts">
	import AzureTtsForm from './AzureTtsForm.svelte';
	import KokoroTtsForm from './KokoroTtsForm.svelte';
	import SesameTtsForm from './SesameTtsForm.svelte';
	import { llmOutput } from './stores';
	import { ttsOptions, ttsError, fetchTtsOptions } from './ttsService';

	let selectedEngine = $state('kokoro');
	let azureTtsForm: AzureTtsForm | null = null;
	let kokoroTtsForm: KokoroTtsForm | null = null;
	let sesameTtsForm: SesameTtsForm | null = null;

	$effect(() => {
		fetchTtsOptions();
	});

	$effect(() => {
		const unsubscribe = llmOutput.subscribe((newText) => {
			if (newText) {
				if (selectedEngine === 'azure') {
					azureTtsForm!.handleGenerateSpeech(undefined, newText);
				} else if (selectedEngine === 'kokoro') {
					kokoroTtsForm!.handleGenerateSpeech(undefined, newText);
				} else if (selectedEngine === 'sesame') {
					sesameTtsForm!.handleGenerateSpeech(undefined, newText);
				}
			}
		});
		return () => {
			unsubscribe;
			llmOutput.set(null);
		};
	});
</script>

<div class="card card-hover p-6">
	<h2 class="mb-6 flex items-center">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="luna-text-primary-light mr-2 h-6 w-6"
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

	<div class="form-group">
		<label for="engine" class="luna-text-subtle mb-2 block text-sm font-medium">TTS Engine</label>
		<div class="relative">
			<select
				id="engine"
				bind:value={selectedEngine}
				class="luna-border-subtle luna-bg-elevated luna-text-muted focus:border-primary focus:ring-primary block w-full appearance-none rounded-md border p-3 shadow-sm transition-all duration-200"
			>
				{#each Object.entries($ttsOptions.engines) as [engineKey, engineOption]}
					<option value={engineKey}>{engineOption.label}</option>
				{/each}
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

	{#if $ttsError}
		<div class="animate-fadeIn alert-error mb-6 rounded-md border p-4 shadow-md">
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

	<div class="animate-fadeIn mt-4">
		<div class:hidden={selectedEngine !== 'azure'}>
			<AzureTtsForm bind:this={azureTtsForm} />
		</div>
		<div class:hidden={selectedEngine !== 'kokoro'}>
			<KokoroTtsForm bind:this={kokoroTtsForm} />
		</div>
		<div class:hidden={selectedEngine !== 'sesame'}>
			<SesameTtsForm bind:this={sesameTtsForm} />
		</div>
	</div>
</div>
