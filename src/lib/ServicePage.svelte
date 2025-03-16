<script lang="ts">
	import LogsDisplay from './LogsDisplay.svelte';
	import { containerService, containerStatus } from './containerService';

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

	// Check container status on mount
	$effect(() => {
		containerService.checkContainerStatus(serviceName);
	});

	// Start log stream if service is running
	$effect(() => {
		if (status.isRunning) {
			containerService.startLogStream(serviceName);
		}
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
					? containerService.stopContainer(serviceName)
					: containerService.startContainer(serviceName)}
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

		<button
			onclick={() => containerService.clearLogs(serviceName)}
			class="rounded-md bg-gray-700 px-5 py-2.5 font-medium text-white shadow-sm transition-colors duration-200 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-600 disabled:cursor-not-allowed disabled:opacity-50"
			disabled={status.isStarting || status.isStopping}
		>
			<span class="flex items-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="mr-1.5 h-4 w-4"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
					/>
				</svg>
				Clear Logs
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

	<div class="flex flex-col gap-6 lg:flex-row">
		<div class="w-full lg:w-1/2">
			{@render children()}
		</div>
		<div class="w-full lg:w-1/2">
			<LogsDisplay {serviceName} />
		</div>
	</div>
</div>
