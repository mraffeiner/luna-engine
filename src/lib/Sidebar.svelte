<script lang="ts">
	import { page } from '$app/state';
	import { containerStatus } from './containerService';

	// Define the services
	const services = [
		{ id: 'docker-service', name: 'Docker Service', path: '/' },
		{ id: 'llm-service', name: 'LLM Service', path: '/llm-service' },
		{ id: 'tts-service', name: 'TTS Service', path: '/tts-service' },
		{ id: 'stt-service', name: 'STT Service', path: '/stt-service' },
		{ id: 'discord-service', name: 'Discord Service', path: '/discord-service' }
	];
</script>

<aside class="flex h-full w-64 flex-col border-r border-gray-700 bg-gray-800 text-white shadow-xl">
	<div class="border-b border-gray-700 bg-gray-900 p-4">
		<h2 class="flex items-center">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="mr-2 h-6 w-6 text-indigo-400"
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
			Luna Engine
		</h2>
	</div>

	<nav class="flex-1 overflow-y-auto p-4">
		<h3 class="sidebar-title">Services</h3>
		<ul class="space-y-1">
			{#each services as service}
				{#if $containerStatus[service.id]}
					{@const status = $containerStatus[service.id]}
					<li>
						<a
							href={service.path}
							class="flex items-center rounded-md px-3 py-2.5 transition-colors duration-200 {page
								.url.pathname === service.path
								? 'bg-indigo-900 bg-opacity-50 text-indigo-200'
								: 'hover:bg-gray-700'}"
						>
							<span
								class="mr-3 inline-block h-2.5 w-2.5 rounded-full {status.isRunning
									? 'bg-green-600'
									: 'bg-red-700'}
									{status.isStarting || status.isStopping ? 'animate-pulse' : ''}"
								title={status.isRunning ? 'Running' : 'Stopped'}
							></span>
							<span class="font-medium">{service.name}</span>
						</a>
					</li>
				{:else}
					<li>
						<a
							href={service.path}
							class="flex items-center rounded-md px-3 py-2.5 transition-colors duration-200 {page
								.url.pathname === service.path
								? 'bg-indigo-900 bg-opacity-50 text-indigo-200'
								: 'hover:bg-gray-700'}"
						>
							<span
								class="mr-3 inline-block h-2.5 w-2.5 rounded-full bg-gray-500"
								title="Unknown status"
							></span>
							<span class="font-medium">{service.name}</span>
						</a>
					</li>
				{/if}
			{/each}
		</ul>
	</nav>

	<div class="border-t border-gray-700 bg-gray-900 bg-opacity-50 p-4">
		<div class="flex items-center text-sm text-gray-400">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="mr-2 h-4 w-4 text-gray-500"
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
