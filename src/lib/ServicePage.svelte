<script lang="ts">
	import { onNavigate } from '$app/navigation';
	import LogsDisplay from './LogsDisplay.svelte';
	import { dockerService, containerStatus, serviceError } from './dockerService';

	// Define props using $props rune
	const { children, serviceName, title } = $props();

	// Get the status for this service using $derived
	const status = $derived(
		$containerStatus[serviceName] || {
			isRunning: false,
			isStarting: false,
			isStopping: false
		}
	);

	let activeTab = $state('configuration');

	// Check container status on mount
	$effect(() => {
		dockerService.checkContainerStatus(serviceName);
	});

	onNavigate(() => {
		serviceError.set(null);
	});
</script>

<div class="mx-auto max-w-7xl p-6">
	<div class="mb-6">
		<h1 class="flex items-center">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="mr-3 h-8 w-8 text-indigo-400"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
				/>
			</svg>
			{title}
		</h1>
	</div>

	<div class="card mb-6 flex flex-wrap items-center gap-4 p-6">
		<button
			onclick={() =>
				status.isRunning
					? dockerService.stopContainer(serviceName)
					: dockerService.startContainer(serviceName)}
			class="rounded-md font-bold {status.isRunning
				? 'bg-red-700 hover:bg-red-800'
				: 'bg-green-700 hover:bg-green-600'} px-5 py-2.5 font-medium text-white shadow-sm focus:outline-none focus:ring-2 {status.isRunning
				? 'focus:ring-red-700'
				: 'focus:ring-green-600'} transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-50"
			disabled={status.isStarting || status.isStopping}
		>
			<span class="flex items-center">
				{#if status.isStarting || status.isStopping}
					<svg
						class="-ml-1 mr-2 h-4 w-4 animate-spin text-white"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					<span>Processing...</span>
				{:else if status.isRunning}
					Stop Service
				{:else}
					Start Service
				{/if}
			</span>
		</button>

		<div class="ml-auto flex items-center rounded-md border border-gray-600 bg-gray-700 px-4 py-2">
			<span class="mr-2 text-sm font-medium text-gray-300">Status:</span>
			<div class="flex items-center">
				<span
					class="inline-flex h-3 w-3 rounded-full {status.isRunning
						? 'bg-green-600'
						: 'bg-red-700'} animate-pulse"
					title={status.isRunning ? 'Running' : 'Stopped'}
				></span>
				<span
					class="ml-2 text-sm font-medium {status.isRunning ? 'text-green-500' : 'text-red-400'}"
				>
					{status.isRunning ? 'Running' : 'Stopped'}
				</span>
			</div>
		</div>
	</div>

	<div class="mb-4 flex border-b border-gray-700">
		<button
			class="tab-button flex-1 px-4 py-2 text-sm font-medium {activeTab === 'configuration'
				? 'border-b-2 border-indigo-500 text-indigo-200'
				: 'text-gray-300 hover:text-gray-100'}"
			onclick={() => (activeTab = 'configuration')}
		>
			Configuration
		</button>
		<button
			class="tab-button flex-1 px-4 py-2 text-sm font-medium {activeTab === 'logs'
				? 'border-b-2 border-indigo-500 text-indigo-200'
				: 'text-gray-300 hover:text-gray-100'}"
			onclick={() => (activeTab = 'logs')}
		>
			Logs
		</button>
	</div>

	<div class:hidden={activeTab !== 'configuration'}>
		{@render children()}
	</div>
	<div class:hidden={activeTab !== 'logs'}>
		<LogsDisplay {serviceName} />
	</div>
</div>

<style>
	.tab-button {
		transition:
			color 0.2s ease,
			border-color 0.2s ease;
	}
</style>
