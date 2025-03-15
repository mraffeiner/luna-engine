<script lang="ts">
	import LogsDisplay from '$lib/LogsDisplay.svelte';
	import { onMount } from 'svelte';
	import { containerService } from '$lib/containerService';

	const serviceName = 'control-panel-backend';

	// Check container status on mount
	onMount(() => {
		containerService.checkContainerStatus(serviceName);
	});
</script>

<div class="p-4">
	<div class="mb-4">
		<h1 class="text-2xl font-bold">Control Panel Backend</h1>
		<p class="mt-2 text-gray-400">
			System logs for the control panel backend service that manages container operations.
		</p>
	</div>

	<div class="mb-4 rounded-md border border-gray-700 bg-gray-800 p-4">
		<h2 class="mb-2 font-semibold">Available Operations</h2>
		<ul class="list-inside list-disc space-y-1 text-gray-300">
			<li>Start/stop service containers</li>
			<li>Stream container logs</li>
			<li>Monitor container status</li>
			<li>Proxy requests to services</li>
		</ul>
	</div>

	<div class="mb-4">
		<h2 class="mb-2 font-semibold">System Logs</h2>
		<LogsDisplay {serviceName} />
	</div>
</div>
