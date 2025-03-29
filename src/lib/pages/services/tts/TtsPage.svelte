<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import { receiveInput, serviceOutput } from '$lib/shared/shared.svelte';
	import { onMount } from 'svelte';
	import ServicePage from '../ServicePage.svelte';
	import AzureTtsForm from './AzureTtsForm.svelte';
	import KokoroTtsForm from './KokoroTtsForm.svelte';
	import SesameTtsForm from './SesameTtsForm.svelte';
	import { fetchTtsOptions, ttsAudioUrl, ttsOptions, type TtsEngine } from './ttsService';
	import { normalizeTtsInput } from '$lib/shared/utils';

	let selectedEngine: TtsEngine = $state('kokoro');
	let text = $state('Hey there, hello!');

	$effect(() => {
		if (receiveInput.tts && serviceOutput.llm.final) {
			text = normalizeTtsInput(serviceOutput.llm.final, selectedEngine);
		}
	});

	onMount(() => {
		fetchTtsOptions();
	});
</script>

<ContentPage name="tts-page">
	<ServicePage serviceName="tts-service">
		<Card title="Text to Speech Settings">
			<div class="flex-start">
				<label>
					<input type="checkbox" bind:checked={receiveInput.tts} />
					<span>Receive Input</span>
				</label>
			</div>
			<div class="form-group">
				<label for="engine">TTS Engine</label>
				<div class="relative">
					<select id="engine" bind:value={selectedEngine} class="form-control">
						{#each Object.entries($ttsOptions.engines) as [engineKey, engineOption]}
							<option value={engineKey}>{engineOption.label}</option>
						{/each}
					</select>
				</div>
			</div>

			<div class="mt-4">
				<div class="animate-in" class:hidden={selectedEngine !== 'azure'}>
					<AzureTtsForm active={selectedEngine === 'azure'} {text} />
				</div>
				<div class="animate-in" class:hidden={selectedEngine !== 'kokoro'}>
					<KokoroTtsForm active={selectedEngine === 'kokoro'} {text} />
				</div>
				<div class="animate-in" class:hidden={selectedEngine !== 'sesame'}>
					<SesameTtsForm active={selectedEngine === 'sesame'} {text} />
				</div>

				{#if $ttsAudioUrl}
					<div class="border-border-subtle bg-bg-surface mt-6 rounded-lg border p-4">
						<h4 class="text-text-muted mb-2 flex items-center text-sm font-medium">
							<Icon
								path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
								class="text-success icon-sm mr-4"
							/>
							Generated Audio
						</h4>
						<audio
							controls
							autoplay={!receiveInput.discord}
							src={$ttsAudioUrl}
							class="w-full rounded-md"
						></audio>
					</div>
				{/if}
			</div>
		</Card>
	</ServicePage>
</ContentPage>
