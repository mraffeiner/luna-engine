<script lang="ts">
	import { dockerService } from '$lib/dockerService';

	const services = [
		'docker-service',
		'discord-service',
		'stt-service',
		'llm-service',
		'tts-service',
		'prompt-service'
	];

	$effect(() => {
		services.forEach((serviceName) => {
			dockerService.checkContainerStatus(serviceName);
		});
	});
</script>

<div class="p-4">
	<h1 class="mb-4 text-2xl font-bold">Welcome to the Luna Engine Control Panel</h1>
	<p class="luna-text-disabled">
		This control panel allows you to manage the various services that make up the Luna Engine. You
		can start and stop services, view their logs, and monitor their status.
	</p>
</div>
