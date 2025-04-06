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
		"Take the users input verbatim and only replace any out of character descriptions or stage directions (like asterisk enclosed annotations) with in character reactions or after-the-fact explanations. Replace laughs, giggles or similar with fitting utterances like heh, ha ha, hehe, ahem, erm, uh, um, etc. Pauses should be handled through logical punctuation or em dashes. Stutters should be short word repetitions instead of single letters. Fix non-English and uppercase occurrences. Don't alter or add anything to what was actually said, but make sure the final result doesn't contain out of character descriptions or stage directions. If there is nothing to replace, respond with the original text. Respond with just the final result."
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
