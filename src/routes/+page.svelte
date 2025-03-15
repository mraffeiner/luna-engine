<script lang="ts">
	import { onMount } from 'svelte';
	import { containerService } from '$lib/containerService';

	const services = [
		'docker-service',
		'llm-service',
		'tts-service',
		'stt-service',
		'discord-service'
	];

	onMount(() => {
		services.forEach((serviceName) => {
			containerService.checkContainerStatus(serviceName);
		});
	});
</script>

<div class="p-4">
	<h1 class="mb-4 text-2xl font-bold">Welcome to the Luna Engine Control Panel</h1>
	<p class="text-gray-400">
		This control panel allows you to manage the various services that make up the Luna Engine. You
		can start and stop services, view their logs, and monitor their status.
	</p>
</div>
