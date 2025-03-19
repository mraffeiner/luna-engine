<script lang="ts">
	import { dockerService } from './dockerService';

	// Define props
	const { serviceName } = $props();

	// Use $state for local state
	let autoScroll = $state(true);
	let logsContainer = $state<HTMLDivElement | null>(null);
	let logs: string[] = $state([]);
	let filterText = $state('');

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

		const isNearBottom =
			logsContainer.scrollHeight - logsContainer.scrollTop - logsContainer.clientHeight < 10;
		autoScroll = isNearBottom;
	}

	/**
	 *  Colorize the log based on keywords
	 */
	function colorizeLog(log: string) {
		let colorClass = 'text-gray-300'; // Default color

		if (log.toLowerCase().includes('error')) {
			colorClass = 'text-red-300';
		} else if (log.toLowerCase().includes('warning')) {
			colorClass = 'text-yellow-300';
		} else if (log.toLowerCase().includes('debug')) {
			colorClass = 'text-blue-300';
		} else if (log.toLowerCase().includes('info')) {
			colorClass = 'text-green-300';
		}

		return `<span class="${colorClass}">${log}</span>`;
	}

	/**
	 * Filter logs based on search text
	 */
	function getFilteredLogs() {
		if (!filterText) return logs;

		return logs.filter((log) => log.toLowerCase().includes(filterText.toLowerCase()));
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
		const unsubscribe = dockerService.getLogsStore(serviceName).subscribe((updatedLogs) => {
			logs = updatedLogs;
		});

		// Cleanup
		return () => {
			unsubscribe();
		};
	});
</script>

<div class="card card-hover p-6">
	<div class="mb-4 flex items-center justify-between">
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
		<div class="flex items-center gap-3">
			<div class="relative">
				<input
					type="text"
					bind:value={filterText}
					placeholder="Filter logs..."
					class="w-48 rounded-md border border-gray-600 bg-gray-700 py-1.5 pl-8 pr-3 text-sm text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
				/>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					/>
				</svg>
			</div>
			<button
				onclick={() => dockerService.clearLogs(serviceName)}
				class="btn-secondary btn-sm btn-icon"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4"
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
				Clear
			</button>
		</div>
	</div>

	<div class="relative">
		<div
			bind:this={logsContainer}
			onscroll={handleScroll}
			class="custom-scrollbar h-[min(70vh,600px)] overflow-auto whitespace-pre-line rounded-md border border-gray-700 bg-gray-900 p-4 font-mono text-sm text-gray-300 shadow-inner"
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
			{:else if getFilteredLogs().length === 0}
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
								d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
							/>
						</svg>
						<p>No matching logs</p>
						<p class="mt-1 text-xs text-gray-600">Try a different filter</p>
					</div>
				</div>
			{:else}
				{#each getFilteredLogs() as log}
					<div class="py-0.5">{@html colorizeLog(log)}</div>
				{/each}
			{/if}
		</div>
		{#if !autoScroll}
			<button
				aria-label="Scroll to bottom"
				onclick={() => {
					autoScroll = true;
					scrollToBottom();
				}}
				class="absolute bottom-4 right-4 rounded-full bg-gray-700 p-2 text-white shadow-md transition-all duration-200 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-600"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M19 14l-7 7m0 0l-7-7m7 7V3"
					/>
				</svg>
			</button>
		{/if}
	</div>

	<div class="mt-3 flex items-center justify-between px-1">
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
			{filterText ? `${getFilteredLogs().length} of ${logs.length}` : logs.length} log {logs.length ===
			1
				? 'entry'
				: 'entries'}
		</div>
		<div class="text-sm text-gray-400">
			{autoScroll ? 'Auto-scroll enabled' : 'Auto-scroll disabled'}
		</div>
	</div>
</div>
