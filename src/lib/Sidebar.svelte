<script lang="ts">
	import { containerStatus } from './dockerService';
	import Icon from './Icon.svelte';
	import { currentPage } from './shared.svelte';

	// Define pages
	const pages = [
		{
			id: 'docker-service',
			name: 'Docker Service',
			icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9'
		},
		{
			id: 'prompt-templates',
			name: 'Prompt Templates',
			icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z'
		},
		{
			id: 'llm-service',
			name: 'LLM Service',
			icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'
		},
		{
			id: 'tts-service',
			name: 'TTS Service',
			icon: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z'
		},
		{
			id: 'discord-service',
			name: 'Discord Service',
			icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z'
		},
		{
			id: 'stt-service',
			name: 'STT Service',
			icon: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z'
		}
	];
</script>

<aside
	class="glass-effect luna-border-base luna-bg-surface luna-text-base flex h-full w-56 flex-col border-r shadow-xl"
>
	<div class="luna-border-base luna-bg-base flex items-center justify-center border-b p-5">
		<button
			onclick={() => {
				currentPage.id = 'home';
			}}
			class="flex cursor-pointer items-center"
		>
			<Icon path="M13 10V3L4 14h7v7l9-11h-7z" class="luna-text-primary-light icon-lg mr-2" />
			<span class="text-xl font-bold">Luna Engine</span>
		</button>
	</div>

	<nav class="custom-scrollbar flex-1 overflow-y-auto p-4">
		<h3 class="sidebar-title">Services</h3>
		<ul>
			{#each pages as page}
				<li class="pt-6">
					<button
						onclick={() => {
							currentPage.id = page.id;
						}}
						class="flex cursor-pointer items-center"
					>
						{#if $containerStatus[page.id]}
							{@const status = $containerStatus[page.id]}
							<Icon
								path={page.icon}
								class="icon-sm mr-2 {status.isRunning
									? 'luna-text-success'
									: 'luna-text-danger'} {status.isStarting || status.isStopping
									? 'status-pulse'
									: ''}"
							/>
						{:else}
							<Icon path={page.icon} class="icon-sm mr-2" />
						{/if}
						<span class="font-medium {currentPage.id === page.id ? 'luna-text-primary-light' : ''}"
							>{page.name}</span
						>
					</button>
				</li>
			{/each}
		</ul>
	</nav>

	<div class="luna-border-base border-t p-4">
		<div class="luna-text-disabled flex items-center text-sm">
			<Icon path="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" class="icon-sm mr-2" />
			<p>Luna Engine Control Panel</p>
		</div>
	</div>
</aside>
