<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import { engineConfig, receiveInput, serviceOutput } from '$lib/shared/shared.svelte';
	import { onMount } from 'svelte';
	import ServicePage from '../ServicePage.svelte';
	import { selectedPrepassLlm, type LlmParams } from './llmService';
	import {
		fetchModels,
		generateResponse,
		loading,
		models,
		selectedResponseLlm
	} from './llmService';

	let currentModelOption = $state('groq|qwen-qwq-32b|true');
	let [selectedProvider, selectedModel, selectedIsReasoning] = $derived(
		currentModelOption.split('|')
	);
	let isReasoning = $derived(selectedIsReasoning.toLocaleLowerCase() === 'true');

	let systemPrompt = $state('You are Luna, a young AI woman an space elf Vtuber');
	let userPrompt = $state('Hey there, hello!');

	let prepassSystemPrompt = $state(
		`You are a text processing tool to prepare llm responses for text-to-speech.` +
			` Take the text and clean it up. Remove stutters with short repetitions.` +
			` Replace stage directions with compatible utterances or em dashes.` +
			` Replace descriptions with logical verbal reactions or follow-up explanations of what happened.` +
			` Replace code blocks or markdown with verbally communicated information.` +
			` Ensure that the final response retains the character and meaning of the original.` +
			` Respond with just the cleaned up text and nothing else:`
	);

	$effect(() => {
		if (currentModelOption) {
			selectedResponseLlm.update((current: LlmParams) => ({
				...current,
				requestParams: {
					provider: selectedProvider,
					model: selectedModel,
					system_prompt: systemPrompt,
					prompt: userPrompt
				},
				isReasoning
			}));
		}
	});

	$effect(() => {
		if (prepassSystemPrompt) {
			selectedPrepassLlm.update((current: LlmParams) => {
				current.requestParams.system_prompt = prepassSystemPrompt;
				return current;
			});
		}
	});

	$effect(() => {
		if (receiveInput.llm && serviceOutput.prompt) {
			systemPrompt = serviceOutput.prompt.system;
			userPrompt = serviceOutput.prompt.user;
		}
	});

	onMount(() => {
		fetchModels();
	});
</script>

<ContentPage name="llm-page">
	<ServicePage serviceName="llm-service">
		<Card title="LLM Settings">
			<div class="flex-start">
				<label>
					<input type="checkbox" bind:checked={receiveInput.llm} />
					<span>Receive Input</span>
				</label>
			</div>

			<div class="flex-start">
				<label>
					<input type="checkbox" bind:checked={engineConfig.llmPrepass} />
					<span>Prepass</span>
				</label>
			</div>

			<div class="form-group">
				<label for="model">Model</label>
				<select id="model" bind:value={currentModelOption} class="form-control">
					{#each $models as modelOption}
						<option value={`${modelOption.provider}|${modelOption.id}|${modelOption.isReasoning}`}
							>{modelOption.name}</option
						>
					{/each}
				</select>
			</div>

			{#if receiveInput.llm}
				<div class="form-group">
					<label for="systemPrompt">System Prompt</label>
					<textarea id="systemPrompt" rows="4" class="form-control" disabled
						>{serviceOutput.prompt.system.trim()}</textarea
					>
				</div>
				<div class="form-group">
					<label for="userPrompt">User Prompt</label>
					<textarea id="userPrompt" rows="4" class="form-control" disabled
						>{serviceOutput.prompt.user.trim()}</textarea
					>
				</div>
			{:else}
				<div class="form-group">
					<label for="systemPrompt">System Prompt</label>
					<textarea id="systemPrompt" bind:value={systemPrompt} rows="8" class="form-control"
					></textarea>
				</div>
				<div class="form-group">
					<label for="userPrompt">User Prompt</label>
					<textarea id="userPrompt" bind:value={userPrompt} rows="8" class="form-control"
					></textarea>
				</div>
			{/if}

			{#if engineConfig.llmPrepass}
				<div class="form-group">
					<label for="prepassSystemPrompt">Prepass System Prompt</label>
					<textarea
						id="prepassSystemPrompt"
						bind:value={prepassSystemPrompt}
						rows="4"
						class="form-control"
					></textarea>
				</div>
			{/if}

			<div>
				<button
					onclick={() => generateResponse($selectedResponseLlm)}
					disabled={$loading}
					class="btn-primary"
				>
					{#if $loading}
						<Spinner class="icon-lg text-text-base mr-2" />
					{/if}
					{$loading ? 'Generating...' : 'Generate'}
				</button>
			</div>

			{#if serviceOutput.llm.raw}
				<div class="form-group">
					<h3 class="text-text-subtle mb-2 text-lg font-medium">Raw Response</h3>
					<div class="form-control whitespace-pre-wrap p-4">
						{serviceOutput.llm.raw}
					</div>
				</div>
			{/if}

			{#if serviceOutput.llm.normalized}
				<div class="form-group">
					<h3 class="text-text-subtle mb-2 text-lg font-medium">Normalized Response</h3>
					<div class="form-control whitespace-pre-wrap p-4">
						{serviceOutput.llm.normalized}
					</div>
				</div>
			{/if}

			{#if engineConfig.llmPrepass && serviceOutput.llm.final}
				<div class="form-group">
					<h3 class="text-text-subtle mb-2 text-lg font-medium">Prepass Response</h3>
					<div class="form-control whitespace-pre-wrap p-4">
						{serviceOutput.llm.final}
					</div>
				</div>
			{/if}
		</Card>
	</ServicePage>
</ContentPage>
