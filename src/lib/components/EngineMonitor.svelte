<script>
	import { clearDynamicPromptContent } from '$lib/pages/prompt/promptPage';
	import { engineConfig, engineStates } from '$lib/shared/shared.svelte';
	import Icon from './Icon.svelte';
</script>

<div class="flex-between gap-3 px-12 py-5">
	<div class="flex-start min-w-1/4 gap-3">
		<button
			id="modeSwitch"
			onclick={() => {
				engineConfig.mode = engineConfig.mode !== 'AUTO' ? 'AUTO' : 'REACT';
			}}
			class="relative cursor-pointer"
			aria-label="Engine Mode Switch"
		>
			<input type="checkbox" checked={engineConfig.mode === 'AUTO'} class="peer sr-only" />
			<div
				class="peer-checked:bg-primary-light peer-focus:ring-primary bg-bg-elevated
								h-5 w-10 rounded-full after:absolute after:left-[4px] after:top-[2px] after:h-4 after:w-4
								after:rounded-full after:bg-white after:shadow-md after:transition-all after:content-['']
								peer-checked:after:translate-x-full peer-focus:outline-none peer-focus:ring-2"
			></div>
		</button>
		<label
			for="modeSwitch"
			class="text-text-subtle mb-0! text-lg! cursor-pointer font-bold capitalize"
		>
			{engineConfig.mode.toLowerCase()}
		</label>
	</div>
	<div class="flex-center grow gap-2 text-lg">
		{#if engineConfig.mode === 'PAUSED'}
			<span class="text-danger-light animate-pulse font-semibold transition-colors"> PAUSED </span>
		{:else}
			<span
				class="font-semibold transition-colors {engineStates.thinking
					? 'text-primary-light animate-pulse'
					: 'text-text-disabled'}"
			>
				Thinking
			</span>
			<span
				class="font-semibold transition-colors {engineStates.speaking
					? 'text-primary-light animate-pulse'
					: 'text-text-disabled'}"
			>
				Speaking
			</span>
			<span
				class="font-semibold transition-colors {engineStates.waiting
					? 'text-primary-light animate-pulse'
					: 'text-text-disabled'}"
			>
				Waiting
			</span>
		{/if}
	</div>
	<div class="min-w-1/4 flex-end">
		<button onclick={() => clearDynamicPromptContent()}>
			<Icon
				path="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
				class="icon-lg text-text-subtle hover:text-danger-light/70 cursor-pointer"
			/>
		</button>
	</div>
</div>
