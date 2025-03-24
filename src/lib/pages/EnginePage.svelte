<script lang="ts">
	import EngineCard from '$lib/components/EngineCard.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { PAGES } from '$lib/shared/constants';
	import {
		engineConfig,
		engineState,
		receiveInput,
		serviceOutput
	} from '$lib/shared/shared.svelte';
	import { onMount, tick } from 'svelte';
	import ContentPage from './ContentPage.svelte';
	import { generateResponse } from './services/llm/llmService';
	import ServicePage from './services/ServicePage.svelte';
	import { generateSpeech } from './services/tts/ttsService';

	let busy = $derived(engineState.thinking || engineState.speaking || engineState.waiting);
	let auto = $state(false);

	let combinedPrompt = $derived.by(() => {
		const prompt = serviceOutput.prompt;
		let combined = '';
		if (prompt) {
			combined += prompt.system ? prompt.system : '';
			combined += prompt.user ? prompt.user : '';
		}
		return combined;
	});

	/**
	 * Auto: Respond continuously when finishing previous response
	 */
	$effect(() => {
		if (engineConfig.mode !== 'AUTO' || busy) return;

		engineState.thinking = true;
		generateResponse().then(() => {
			generateSpeech().then(() => {
				engineState.speaking = true;
				engineState.thinking = false;
			});
		});
	});

	/**
	 * React: Respond only when input changes
	 */
	$effect(() => {
		if (engineConfig.mode !== 'REACT' || busy) return;

		if (serviceOutput.stt) {
			// Tick to ensure prompt received stt output first
			tick().then(() => {
				engineState.thinking = true;
				generateResponse().then(() => {
					generateSpeech().then(() => {
						engineState.speaking = true;
						engineState.thinking = false;
					});
				});
			});
		}
	});

	$effect(() => {
		engineConfig.mode = auto ? 'AUTO' : 'REACT';
	});

	onMount(() => {
		setTimeout(() => {
			engineState.waiting = false;
		}, 5);
	});
</script>

<ContentPage name="engine-page">
	<ServicePage serviceName="control-panel">
		<div class="flex-start mb-4 gap-3">
			<label class="mb-0! relative cursor-pointer">
				<input type="checkbox" bind:checked={auto} class="peer sr-only" />
				<div
					class="peer-checked:bg-primary-light peer-focus:ring-primary bg-bg-elevated h-5 w-10
					rounded-full after:absolute after:left-[4px] after:top-[2px] after:h-4
					after:w-4 after:rounded-full after:bg-white
					after:shadow-md after:transition-all after:content-['']
					peer-checked:after:translate-x-full peer-focus:outline-none peer-focus:ring-2"
				></div>
			</label>
			<span class="text-text-subtle text-lg font-bold">{auto ? 'Auto' : 'React'}</span>
		</div>

		<div class="grid grid-cols-8 grid-rows-9 gap-4">
			{#each PAGES.slice(2, PAGES.length) as page}
				{#if page.id === 'prompt-page'}
					<div class="col-span-5 row-span-9">
						<EngineCard title={page.name} bind:receiveInput={receiveInput.prompt}>
							<div class="whitespace-pre-wrap">
								{combinedPrompt}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'llm-page'}
					<div class="col-span-3 row-span-3">
						<EngineCard title={page.name} bind:receiveInput={receiveInput.llm}>
							<div class="whitespace-pre-wrap">
								{#if serviceOutput.llm}
									{serviceOutput.llm}
								{/if}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'stt-page'}
					<div class="col-span-3 row-span-2">
						<EngineCard title={page.name} bind:receiveInput={receiveInput.stt}>
							<div class="whitespace-pre-wrap">
								{#if serviceOutput.stt}
									{serviceOutput.stt}
								{/if}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'tts-page'}
					<div class="col-span-3 row-span-2">
						<EngineCard title={page.name} bind:receiveInput={receiveInput.tts}>
							<div>
								{#if serviceOutput.tts}
									<h4 class="text-text-subtle mb-2 flex items-center text-sm font-medium">
										<Icon
											path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
											class="text-primary-light icon-sm mr-2"
										/>
										Luna
									</h4>
									<audio controls src={serviceOutput.tts.url} class="w-full rounded-md"></audio>
								{/if}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'discord-page'}
					<div class="col-span-3 row-span-2">
						<EngineCard title={page.name} bind:receiveInput={receiveInput.discord}>
							<div>
								{#if serviceOutput.discord}
									{@const [username, audio] = [...serviceOutput.discord.entries()].pop() ?? []}
									<h4 class="text-text-subtle mb-2 flex items-center text-sm font-medium">
										<Icon
											path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
											class="text-success icon-sm mr-2"
										/>
										{username}
									</h4>
									<audio controls src={audio?.url} class="w-full rounded-md"></audio>
								{/if}
							</div>
						</EngineCard>
					</div>
				{/if}
			{/each}
		</div>
	</ServicePage>
</ContentPage>
