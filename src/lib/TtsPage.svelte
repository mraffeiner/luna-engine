<script lang="ts">
	import AzureTtsForm from './AzureTtsForm.svelte';
	import KokoroTtsForm from './KokoroTtsForm.svelte';
	import SesameTtsForm from './SesameTtsForm.svelte';
	import { llmOutput } from './stores';
	import { ttsOptions, fetchTtsOptions } from './ttsService';
	import Icon from './Icon.svelte';
	import Card from './Card.svelte';

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

<Card title="Text to Speech Settings">
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
</Card>
