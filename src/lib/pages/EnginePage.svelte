<script lang="ts">
	import EngineCard from '$lib/components/EngineCard.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { PAGES } from '$lib/shared/constants';
	import {
		engineConfig,
		engineStates,
		receiveInput,
		serviceOutput,
		subtitles
	} from '$lib/shared/shared.svelte';
	import ContentPage from './ContentPage.svelte';
	import {
		generateResponse,
		selectedPrepassLlm,
		selectedResponseLlm
	} from './services/llm/llmService';
	import ServicePage from './services/ServicePage.svelte';
	import { generateSpeech, selectedTts, type TtsParams } from './services/tts/ttsService';
	import { discordService } from './services/discord/discordService';
	import {
		asyncSleep,
		normalizeLlmResponse,
		normalizeTtsInput,
		splitByPunctuation
	} from '$lib/shared/utils';
	import { consumeNewMessages, updateUserPromptSection } from './prompt/promptPage';
	import { loading as sttLoading } from './services/stt/sttService';

	const shouldRespond = $derived(
		!engineStates.paused && !engineStates.busy && !engineStates.waiting && !engineStates.listening
	);

	let combinedPrompt = $derived.by(() => {
		const prompt = serviceOutput.prompt;
		let combined = '';
		if (prompt) {
			combined += prompt.system ? prompt.system : '';
			combined += prompt.user ? prompt.user : '';
		}
		return combined;
	});

	async function handleThinking() {
		engineStates.thinking = true;
		consumeNewMessages(); // Consume new messages and push them to the conversation
		engineStates.reading = false; // Just read all messages
		engineStates.hasNewMessages = false; // No new messages since Luna started responding to them
		const llmResponse = await generateResponse($selectedResponseLlm);
		engineStates.thinking = false;

		if (!llmResponse) return;

		serviceOutput.llm.raw = llmResponse;

		const llmNormalizedResponse = normalizeLlmResponse(llmResponse, 'You:');
		serviceOutput.llm.normalized = llmNormalizedResponse;

		if (!engineConfig.llmPrepass) return llmNormalizedResponse;

		const prepassParams = $selectedPrepassLlm;
		prepassParams.requestParams.prompt = llmNormalizedResponse;

		engineStates.thinking = true;
		const llmPrepassResponse = await generateResponse(prepassParams);
		engineStates.thinking = false;

		if (!llmPrepassResponse) return; // NOTE: Unlikely to happen, potentially add fallback

		const llmFinalResponse = normalizeLlmResponse(llmPrepassResponse, 'You:');

		serviceOutput.llm.final = llmFinalResponse;
		return llmFinalResponse;
	}

	async function handleSpeaking(text: string) {
		const ttsParams: TtsParams = $selectedTts;

		const normalizedText = normalizeTtsInput(text, ttsParams.requestParams.engine);

		let textParts: string[] = [normalizedText];
		if (engineConfig.interruptable)
			// Split by punctuation
			textParts = splitByPunctuation(normalizedText, 5);

		// OPTIMIZE: Pause audio instead of splitting and somehow figure out where it paused for conversation log
		// Generate and play each part
		let accumulatedText: string = ''; // For unfragmented conversation prompt
		for (const textPart of textParts) {
			accumulatedText = `${accumulatedText} ${textPart}`.trim();
			ttsParams.requestParams.text = textPart.trim();

			// OPTIMIZE: Use map with await Promise.all if latency between parts is too high
			const speechPart = await generateSpeech(ttsParams);

			if (!speechPart || !speechPart.blob) continue;

			engineStates.speaking = true;
			subtitles.text = ttsParams.requestParams.text;

			await new Promise<void>((resolve) => {
				const audioUrl = URL.createObjectURL(speechPart.blob);
				const audioElement = new Audio(audioUrl);

				audioElement.onended = () => {
					URL.revokeObjectURL(audioUrl);
					resolve();
				};

				audioElement.play();

				// Start parallel discord playback
				if (receiveInput.discord) {
					discordService.playAudio(speechPart.blob);
				}
			});

			subtitles.text = '';
			engineStates.speaking = false;

			// OPTIMIZE: Pause and resume depending on interrupt reason (Advanced interruption using small llm decision)
			if (engineStates.paused || engineStates.listening || $sttLoading || engineStates.reading) {
				break;
			}
		}

		// Handle prompt update here to ensure conversation only receives uninterrupted parts
		if (receiveInput.prompt && accumulatedText) {
			updateUserPromptSection('conversation', null, `You: ${accumulatedText}`, null, true);
		}
	}

	// OPTIMIZE: Parallel thinking -> Query small model for instant generic response and start talking while thinking
	async function respond() {
		engineStates.busy = true;
		engineStates.waiting = false;

		try {
			const response = await handleThinking();

			if (response) {
				await handleSpeaking(response);
			}

			engineStates.waiting = true;
			await asyncSleep(engineConfig.msMinAfterResponse);
			engineStates.waiting =
				engineConfig.mode !== 'AUTO' && !engineStates.hasNewMessages && !engineStates.listening;
		} catch (error) {
			engineStates.reset();
			console.error(`Engine paused because of error: `, error);
		}
	}

	$effect(() => {
		if (engineStates.hasNewMessages) {
			engineStates.waiting = false;
			asyncSleep(5000).then(() => {
				// Interrupt speech after 5 seconds to acknowledge new messages
				if (engineStates.speaking && engineStates.hasNewMessages) engineStates.reading = true;
			});
		}
	});

	$effect(() => {
		if (shouldRespond) {
			respond().then(() => (engineStates.busy = false));
		}
	});
</script>

<ContentPage name="home">
	<ServicePage serviceName="luna-engine">
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
								{#if serviceOutput.llm.normalized}
									{serviceOutput.llm.normalized}
								{/if}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'stt-page'}
					<div class="col-span-3 row-span-2">
						<EngineCard title={page.name} bind:receiveInput={receiveInput.stt}>
							<div class="whitespace-pre-wrap">
								{#each serviceOutput.stt as entry}
									{entry.username}: {entry.transcript}
								{/each}
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
