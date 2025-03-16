<script lang="ts">
	import { containerService } from './containerService';

	// Define props using $props rune
	const props = $props();

	// Use $state for local state
	let logs = $state<string[]>([]);
	let autoScroll = $state(true);
	let logsContainer = $state<HTMLDivElement | null>(null);

	/**
	 * Scroll to the bottom of the logs container
	 */
	function scrollToBottom() {
		if (logsContainer && autoScroll) {
			logsContainer.scrollTop = logsContainer.scrollHeight;
		}
	}

	/**
	 * Handle manual scrolling to detect if user has scrolled up
	 */
	function handleScroll() {
		if (!logsContainer) return;

		// If user scrolls up more than 100px from bottom, disable auto-scroll
		const isNearBottom =
			logsContainer.scrollHeight - logsContainer.scrollTop - logsContainer.clientHeight < 100;
		autoScroll = isNearBottom;
	}

	// Watch for changes to logs array and scroll if autoScroll is enabled
	$effect(() => {
		if (logs.length > 0 && autoScroll) {
			// Use setTimeout to ensure DOM is updated before scrolling
			setTimeout(scrollToBottom, 0);
		}
	});

	// Setup and cleanup
	$effect(() => {
		// Setup
		const handleBeforeUnload = () => {
			containerService.stopLogStream(props.serviceName);
		};

		window.addEventListener('beforeunload', handleBeforeUnload);

		containerService.startLogStream(props.serviceName);
		const logsStore = containerService.getLogsStore(props.serviceName);
		const unsubscribe = logsStore.subscribe((updatedLogs) => {
			logs = updatedLogs;
		});

		// Cleanup
		return () => {
			unsubscribe();
			window.removeEventListener('beforeunload', handleBeforeUnload);
		};
	});
</script>

<div class="card p-6">
	<div class="mb-3 flex items-center justify-between">
		<h3 class="flex items-center">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="mr-2 h-5 w-5 text-indigo-400"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
				/>
			</svg>
			Service Logs
		</h3>
		<div class="flex items-center">
			<label class="flex items-center text-sm text-gray-300">
				<input
					type="checkbox"
					bind:checked={autoScroll}
					class="mr-2 h-4 w-4 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500"
				/>
				Auto-scroll
			</label>
		</div>
	</div>

	<div
		bind:this={logsContainer}
		onscroll={handleScroll}
		class="custom-scrollbar h-[400px] overflow-auto whitespace-pre-line rounded-md border border-gray-700 bg-gray-900 p-4 font-mono text-sm text-gray-300"
	>
		{#if logs.length === 0}
			<div class="flex h-full items-center justify-center text-gray-500">
				<div class="text-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="mx-auto mb-2 h-10 w-10 text-gray-600"
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
					<p>No logs available</p>
					<p class="mt-1 text-xs text-gray-600">Start the service to see logs</p>
				</div>
			</div>
		{:else}
			{#each logs as log}
				<div class="py-0.5">{log}</div>
			{/each}
		{/if}
	</div>

	<div class="mt-2 flex items-center justify-between px-1">
		<div class="flex items-center text-sm text-gray-400">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="mr-1 h-4 w-4"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
				/>
			</svg>
			{logs.length} log {logs.length === 1 ? 'entry' : 'entries'}
		</div>
	</div>
</div>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 8px;
	}

	.custom-scrollbar::-webkit-scrollbar-track {
		background: #1f2937;
		border-radius: 4px;
	}

	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #374151;
		border-radius: 4px;
	}

	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: #4b5563;
	}
</style>
