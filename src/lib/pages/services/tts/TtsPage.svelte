<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import { receiveInput, serviceOutput } from '$lib/shared/shared.svelte';
	import { serviceError } from '../docker/dockerService';
	import ServicePage from '../ServicePage.svelte';
	import AzureTtsForm from './AzureTtsForm.svelte';
	import KokoroTtsForm from './KokoroTtsForm.svelte';
	import SesameTtsForm from './SesameTtsForm.svelte';
	import { fetchTtsOptions, generateSpeech, ttsOptions, type TtsRequestParams } from './ttsService';

	let selectedEngine = $state('kokoro');
	let text = $state('Hey there, hello!');
	let audioUrl = $state('');
	let loading = $state(false);

	async function handleGenerateSpeech(params: TtsRequestParams) {
		loading = true;

		if (params) {
			const audioBlob = await generateSpeech(params);

			if (audioBlob) {
				if (audioUrl) URL.revokeObjectURL(audioUrl);
				audioUrl = URL.createObjectURL(audioBlob);
				serviceOutput.tts = { blob: audioBlob, url: audioUrl };
			}
		}

		loading = false;
	}

	$effect(() => {
		fetchTtsOptions();
	});

	$effect(() => {
		if (receiveInput.tts && serviceOutput.llm) {
			text = serviceOutput.llm;
		}
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
					<AzureTtsForm {text} {loading} {handleGenerateSpeech} />
				</div>
				<div class="animate-in" class:hidden={selectedEngine !== 'kokoro'}>
					<KokoroTtsForm {text} {loading} {handleGenerateSpeech} />
				</div>
				<div class="animate-in" class:hidden={selectedEngine !== 'sesame'}>
					<SesameTtsForm {text} {loading} {handleGenerateSpeech} />
				</div>

				{#if audioUrl}
					<div class="border-border-subtle bg-bg-surface mt-6 rounded-lg border p-4">
						<h4 class="text-text-muted mb-2 flex items-center text-sm font-medium">
							<Icon
								path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
								class="text-success icon-sm mr-4"
							/>
							Generated Audio
						</h4>
						<audio controls autoplay={true} src={audioUrl} class="w-full rounded-md"></audio>
					</div>
				{/if}
			</div>
		</Card>
	</ServicePage>
</ContentPage>
