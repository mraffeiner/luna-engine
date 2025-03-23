<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import { dockerService } from './docker/dockerService';

	const { visible, serviceName } = $props();

	let autoScroll = $state(false);
	let logsContainer = $state<HTMLDivElement>();
	let logs: string[] = $state([]);
	let filterText = $state('');
	let filteredLogs = $derived(
		filterText ? logs.filter((log) => log.toLowerCase().includes(filterText.toLowerCase())) : logs
	);

	function onscroll() {
		if (logsContainer) {
			const nearBottom =
				logsContainer.scrollHeight - logsContainer.scrollTop - logsContainer.clientHeight < 50;
			autoScroll = nearBottom;
		}
	}

	function scrollToBottom() {
		if (logsContainer) logsContainer.scrollTop = logsContainer.scrollHeight;
	}

	$effect(() => {
		autoScroll = true;
	});

	$effect(() => {
		if (filteredLogs.length > 0 && autoScroll && visible) {
			scrollToBottom();
		}
	});

	$effect(() => {
		const unsubscribe = dockerService.getLogsStore(serviceName).subscribe((updatedLogs) => {
			logs = updatedLogs;
		});

		return () => {
			unsubscribe();
		};
	});
</script>

<div class="card p-6">
	<div class="flex-between mb-4">
		<h3 class="flex items-center">
			<Icon
				path="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
				class="text-primary-light icon-lg mr-2"
			/>
			Service Logs
		</h3>
		<div class="flex items-center gap-4">
			<div class="relative">
				<input
					type="text"
					bind:value={filterText}
					placeholder="Filter logs..."
					class="form-control pl-8.5 text-sm"
				/>
				<Icon
					path="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					class="text-text-disabled icon-sm absolute bottom-3.5 left-3"
				/>
			</div>
			<button onclick={() => dockerService.clearLogs(serviceName)} class="btn-secondary">
				<Icon
					path="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
					class="icon-sm mr-2"
				/>
				Clear
			</button>
		</div>
	</div>

	<div class="relative">
		<div
			bind:this={logsContainer}
			{onscroll}
			class="border-border-base bg-bg-base text-text-subtle h-[min(70vh,600px)] overflow-auto whitespace-pre-line rounded-md border p-4 font-mono text-sm shadow-inner"
		>
			{#if logs.length === 0}
				<div class="text-text-disabled flex-center h-full flex-col">
					<Icon
						path="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						class="text-text-disabled icon-lg mb-2"
					/>
					<p>No logs available</p>
				</div>
			{:else if filteredLogs.length === 0}
				<div class="text-text-disabled flex-center h-full flex-col">
					<Icon
						path="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						class="text-text-disabled icon-lg mb-2"
					/>
					<p>No matching logs</p>
				</div>
			{:else}
				{#each filteredLogs as log}
					<div class="py-0.5">
						{#if log.includes('ERROR')}
							<span class="text-danger-light">{log}</span>
						{:else if log.includes('WARNING')}
							<span class="text-warning-light">{log}</span>
						{:else if log.includes('DEBUG')}
							<span class="text-info-light">{log}</span>
						{:else if log.includes('INFO')}
							<span class="text-success-light">{log}</span>
						{:else}
							<span class="text-text-subtle">{log}</span>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
		{#if !autoScroll}
			<button
				onclick={() => {
					autoScroll = true;
				}}
				class="bg-bg-elevated hover:bg-bg-elevated-30 focus:border-border-focus text-text-base absolute bottom-4 right-4 rounded-full p-2 shadow-md transition-all duration-200 focus:outline-none focus:ring-2"
			>
				<Icon path="M19 14l-7 7m0 0l-7-7m7 7V3" class="icon-sm" />
			</button>
		{/if}
	</div>

	<div class="flex-between mt-3 px-1">
		<div class="text-text-disabled flex items-center text-sm">
			<Icon
				path="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
				class="icon-sm mr-2"
			/>
			{filterText ? `${filteredLogs.length} of ${logs.length}` : logs.length} log {logs.length === 1
				? 'entry'
				: 'entries'}
		</div>
		<div class="text-text-disabled text-sm">
			{autoScroll ? 'Auto-scroll enabled' : 'Auto-scroll disabled'}
		</div>
	</div>
</div>
