<script lang="ts">
	import { page } from '$app/state';
	import { containerStatus } from './dockerService';

	// Define the services
	const services = [
		{
			id: 'docker-service',
			name: 'Docker Service',
			path: '/docker-service',
			icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9'
		},
		{
			id: 'discord-service',
			name: 'Discord Service',
			path: '/discord-service',
			icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z'
		},
		{
			id: 'stt-service',
			name: 'STT Service',
			path: '/stt-service',
			icon: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z'
		},
		{
			id: 'llm-service',
			name: 'LLM Service',
			path: '/llm-service',
			icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'
		},
		{
			id: 'tts-service',
			name: 'TTS Service',
			path: '/tts-service',
			icon: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z'
		},
		{
			id: 'prompt-service',
			name: 'Prompt Service',
			path: '/prompt-service',
			icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z'
		}
	];
</script>

<aside class="flex h-full w-56 flex-col border-r border-gray-700 bg-gray-800 text-white shadow-xl">
	<div class="border-b border-gray-700 bg-gray-900 p-4">
		<h2 class="flex-start">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="icon icon-lg icon-primary mr-2"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M13 10V3L4 14h7v7l9-11h-7z"
				/>
			</svg>
			<span class="text-xl font-bold">Luna Engine</span>
		</h2>
	</div>

	<nav class="custom-scrollbar flex-1 overflow-y-auto p-4">
		<h3 class="sidebar-title">Services</h3>
		<ul class="space-y-2">
			{#each services as service}
				{#if $containerStatus[service.id]}
					{@const status = $containerStatus[service.id]}
					<li>
						<a
							href={service.path}
							class="flex-start transition-standard rounded-lg px-3 py-3 {page.url.pathname ===
							service.path
								? 'bg-indigo-900/70 text-indigo-200 shadow-md'
								: 'hover:bg-gray-700/70'}"
						>
							<span
								class="mr-3 {status.isRunning ? 'status-running' : 'status-stopped'}
									{status.isStarting || status.isStopping ? 'status-pulse' : ''}"
								title={status.isRunning ? 'Running' : 'Stopped'}
							></span>
							<div class="flex items-center">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="icon icon-sm mr-2 {page.url.pathname === service.path
										? 'text-indigo-300'
										: 'text-gray-400'}"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d={service.icon}
									/>
								</svg>
								<span class="font-medium">{service.name}</span>
							</div>
						</a>
					</li>
				{:else}
					<li>
						<a
							href={service.path}
							class="flex-start transition-standard rounded-lg px-3 py-3 {page.url.pathname ===
							service.path
								? 'bg-indigo-900/70 text-indigo-200 shadow-md'
								: 'hover:bg-gray-700/70'}"
						>
							<span class="status-unknown mr-3" title="Unknown status"></span>
							<div class="flex items-center">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="icon icon-sm mr-2 {page.url.pathname === service.path
										? 'text-indigo-300'
										: 'text-gray-400'}"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d={service.icon}
									/>
								</svg>
								<span class="font-medium">{service.name}</span>
							</div>
						</a>
					</li>
				{/if}
			{/each}
		</ul>
	</nav>

	<div class="glass-effect border-t border-gray-700 p-4">
		<div class="flex-start text-sm text-gray-400">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="icon icon-sm icon-secondary mr-2"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<p>Luna Engine Control Panel</p>
		</div>
	</div>
</aside>
