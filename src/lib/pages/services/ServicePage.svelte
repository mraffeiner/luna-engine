<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import { containerStatus, dockerService } from './docker/dockerService';
	import LogsDisplay from './LogsDisplay.svelte';

	// Define props using $props rune
	const { children, serviceName } = $props();

	// Get the status for this service using $derived
	const status = $derived(
		$containerStatus[serviceName] || {
			isRunning: false,
			isStarting: false,
			isStopping: false
		}
	);

	let activeTab = $state('configuration');
</script>

<div class="card mb-6 flex flex-wrap items-center gap-4">
	<button
		onclick={() =>
			status.isRunning
				? dockerService.stopContainer(serviceName)
				: dockerService.startContainer(serviceName)}
		class={status.isRunning ? 'btn-danger' : 'btn-success'}
		disabled={status.isStarting || status.isStopping}
	>
		{#if status.isStarting || status.isStopping}
			<Spinner class="text-text-base icon-sm mr-2" />
			<span>Processing...</span>
		{:else if status.isRunning}
			<Icon path="M6 18L18 6M6 6l12 12" class="icon-lg mr-2" />
			<span>Stop Service</span>
		{:else}
			<Icon
				path="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
				class="icon-lg mr-2"
			/>
			<span>Start Service</span>
		{/if}
	</button>

	<div
		class="glass-effect border-border-subtle ml-auto flex items-center rounded-md border px-4 py-2.5 shadow-md"
	>
		<span class="text-text-subtle text-md mr-4 font-semibold">Status</span>
		<div class="flex items-center">
			<span
				class="{status.isRunning ? 'status-running' : 'status-stopped'} {status.isStarting ||
				status.isStopping
					? 'animate-pulse'
					: ''}"
				title={status.isRunning ? 'Running' : 'Stopped'}
			></span>
			<span
				class="text-md ml-2 font-semibold {status.isRunning
					? 'text-success-light'
					: 'text-danger-light'}"
			>
				{status.isRunning ? 'Running' : 'Stopped'}
			</span>
		</div>
	</div>
</div>

<div class="tabs">
	<button
		class="tab-button {activeTab === 'configuration' ? 'tab-button-active' : 'tab-button-inactive'}"
		onclick={() => (activeTab = 'configuration')}
	>
		<Icon
			path="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z"
			class="icon-sm mr-2"
		/>
		Configuration
	</button>
	<button
		class="tab-button {activeTab === 'logs' ? 'tab-button-active' : 'tab-button-inactive'}"
		onclick={() => (activeTab = 'logs')}
	>
		<Icon
			path="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
			class="icon-sm mr-2"
		/>
		Logs
	</button>
</div>

<div class="animate-in" class:hidden={activeTab !== 'configuration'}>
	{@render children()}
</div>
<div class="animate-in" class:hidden={activeTab !== 'logs'}>
	<LogsDisplay visible={activeTab === 'logs'} {serviceName} />
</div>
