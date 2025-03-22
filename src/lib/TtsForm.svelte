<script lang="ts">
	import AzureTtsForm from './AzureTtsForm.svelte';
	import KokoroTtsForm from './KokoroTtsForm.svelte';
	import SesameTtsForm from './SesameTtsForm.svelte';
	import { llmOutput } from './stores';
	import { ttsOptions, fetchTtsOptions } from './ttsService';
	import Icon from './Icon.svelte';

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

<div class="card">
	<div class="card-header">
		<h2>
			<Icon
				path="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
				class="luna-text-primary-light icon-lg mr-2"
			/>
			Text-to-Speech
		</h2>
	</div>

	<div class="card-body">
		<div class="form-group">
			<label for="engine" class="luna-text-subtle mb-2 block text-sm font-medium">TTS Engine</label>
			<div class="relative">
				<select id="engine" bind:value={selectedEngine} class="form-control">
					{#each Object.entries($ttsOptions.engines) as [engineKey, engineOption]}
						<option value={engineKey}>{engineOption.label}</option>
					{/each}
				</select>
			</div>
		</div>
	</div>

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
