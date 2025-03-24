<script lang="ts">
	import EngineCard from '$lib/components/EngineCard.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { PAGES } from '$lib/shared/constants';
	import { engineConfig, forwardOutput } from '$lib/shared/shared.svelte';
	import { discordOutput, llmOutput, promptOutput, sttOutput, ttsOutput } from '$lib/shared/stores';
	import ContentPage from './ContentPage.svelte';
	import ServicePage from './services/ServicePage.svelte';
</script>

<ContentPage name="engine-page">
	<ServicePage serviceName="control-panel">
		<div class="flex-start mb-4 gap-3">
			<label class="mb-0! relative cursor-pointer">
				<input type="checkbox" bind:checked={engineConfig.auto} class="peer sr-only" />
				<div
					class="peer-checked:bg-primary-light peer-focus:ring-primary bg-bg-elevated h-5 w-10
					rounded-full after:absolute after:left-[4px] after:top-[2px] after:h-4
					after:w-4 after:rounded-full after:bg-white
					after:shadow-md after:transition-all after:content-['']
					peer-checked:after:translate-x-full peer-focus:outline-none peer-focus:ring-2"
				></div>
			</label>
			<span class="text-text-subtle text-lg font-bold">{engineConfig.auto ? 'Auto' : 'React'}</span>
		</div>

		<div class="grid grid-cols-8 grid-rows-9 gap-4">
			{#each PAGES.slice(2, PAGES.length) as page}
				{#if page.id === 'prompt-page'}
					<div class="col-span-5 row-span-9">
						<EngineCard title={page.name} bind:forward={forwardOutput.prompt}>
							<div class="whitespace-pre-wrap">
								{#if $promptOutput?.systemPrompt || $promptOutput?.userPrompt}
									{$promptOutput.systemPrompt}{$promptOutput.userPrompt
										? `${$promptOutput.userPrompt}`
										: ''}
								{/if}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'llm-page'}
					<div class="col-span-3 row-span-3">
						<EngineCard title={page.name} bind:forward={forwardOutput.llm}>
							<div class="whitespace-pre-wrap">
								{#if $llmOutput}
									{$llmOutput}
								{/if}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'tts-page'}
					<div class="col-span-3 row-span-2">
						<EngineCard title={page.name} bind:forward={forwardOutput.tts}>
							<div>
								{#if $ttsOutput}
									<h4 class="text-text-subtle mb-2 flex items-center text-sm font-medium">
										<Icon
											path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
											class="text-primary-light icon-sm mr-2"
										/>
										Luna
									</h4>
									<audio controls src={$ttsOutput.audioUrl} class="w-full rounded-md"></audio>
								{/if}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'discord-page'}
					<div class="col-span-3 row-span-2">
						<EngineCard title={page.name} bind:forward={forwardOutput.discord}>
							<div>
								{#if $discordOutput}
									<h4 class="text-text-subtle mb-2 flex items-center text-sm font-medium">
										<Icon
											path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
											class="text-success icon-sm mr-2"
										/>
										{$discordOutput.username}
									</h4>
									<audio controls src={$discordOutput.audioUrl} class="w-full rounded-md"></audio>
								{/if}
							</div>
						</EngineCard>
					</div>
				{:else if page.id === 'stt-page'}
					<div class="col-span-3 row-span-2">
						<EngineCard title={page.name} bind:forward={forwardOutput.stt}>
							<div class="whitespace-pre-wrap">
								{#if $sttOutput}
									{$sttOutput}
								{/if}
							</div>
						</EngineCard>
					</div>
				{/if}
			{/each}
		</div>
	</ServicePage>
</ContentPage>
