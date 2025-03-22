<script lang="ts">
	import { onNavigate } from '$app/navigation';
	import LogsDisplay from './LogsDisplay.svelte';
	import { dockerService, containerStatus, serviceError } from './dockerService';
	import Icon from './Icon.svelte';
	import Spinner from './Spinner.svelte';

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

	onNavigate(() => {
		serviceError.set(null);
	});
</script>

<div class="mb-6">
	<h1 class="flex items-center">
		<Icon
			path="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
			class="luna-text-primary-light icon-lg mr-3"
		/>
		{title}
	</h1>
</div>

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
			<Spinner class="icon-sm mr-2" />
			<span>Processing...</span>
		{:else if status.isRunning}
			<Icon path="M6 18L18 6M6 6l12 12" class="icon-sm mr-2" />
			<span>Stop Service</span>
		{:else}
			<Icon
				path="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
				class="icon-sm mr-2"
			/>
			<span>Start Service</span>
		{/if}
	</button>

	<div
		class="glass-effect luna-border-subtle ml-auto flex items-center rounded-md border px-4 py-2.5 shadow-md"
	>
		<span class="luna-text-subtle mr-2 text-sm font-medium">Status:</span>
		<div class="flex items-center">
			<span
				class="{status.isRunning ? 'status-running' : 'status-stopped'} {status.isStarting ||
				status.isStopping
					? 'status-pulse'
					: ''}"
				title={status.isRunning ? 'Running' : 'Stopped'}
			></span>
			<span
				class="ml-2 text-sm font-medium {status.isRunning
					? 'luna-text-success-light'
					: 'luna-text-danger-light'}"
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

<div class="animate-fadeIn" class:hidden={activeTab !== 'configuration'}>
	{@render children()}
</div>
<div class="animate-fadeIn" class:hidden={activeTab !== 'logs'}>
	<LogsDisplay {serviceName} />
</div>
