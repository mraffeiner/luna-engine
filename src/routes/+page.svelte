<script lang="ts">
	import DiscordPage from '$lib/DiscordPage.svelte';
	import DockerPage from '$lib/DockerPage.svelte';
	import { dockerService } from '$lib/dockerService';
	import LlmPage from '$lib/LlmPage.svelte';
	import PromptPage from '$lib/PromptPage.svelte';
	import ServicePage from '$lib/ServicePage.svelte';
	import { currentPage } from '$lib/shared.svelte';
	import SttPage from '$lib/SttPage.svelte';
	import TtsPage from '$lib/TtsPage.svelte';

	const services = [
		'docker-service',
		'llm-service',
		'tts-service',
		'discord-service',
		'stt-service'
	];

	const cleanup = () => {
		dockerService.stopLogsStream();
	};

	$effect(() => {
		services.forEach((serviceName) => {
			dockerService.checkContainerStatus(serviceName);
		});
	});

	$effect(() => {
		dockerService.startLogsStream();

		return () => {
			cleanup();
		};
	});

	$effect(() => {
		window.addEventListener('beforeunload', cleanup);

		return () => {
			window.removeEventListener('beforeunload', cleanup);
		};
	});
</script>

<!-- Service and Configuration Pages - Always mounted, conditionally displayed -->
<div class="animate-fadeIn" class:hidden={currentPage.id !== 'home'}>
	<h1 class="mb-4 text-2xl font-bold">Welcome to the Luna Engine Control Panel</h1>
	<p class="luna-text-disabled">
		This control panel allows you to manage the various services that make up the Luna Engine and
		configure various aspects of the engine pipeline.
	</p>
</div>
<div class="animate-fadeIn" class:hidden={currentPage.id !== 'docker-service'}>
	<ServicePage serviceName="docker-service" title="Docker Service">
		<DockerPage />
	</ServicePage>
</div>
<div class="animate-fadeIn" class:hidden={currentPage.id !== 'prompt-templates'}>
	<PromptPage title="Prompt Templates" />
</div>
<div class="animate-fadeIn" class:hidden={currentPage.id !== 'llm-service'}>
	<ServicePage serviceName="llm-service" title="Large Language Model Service">
		<LlmPage />
	</ServicePage>
</div>
<div class="animate-fadeIn" class:hidden={currentPage.id !== 'tts-service'}>
	<ServicePage serviceName="tts-service" title="Text-to-Speech Service">
		<TtsPage />
	</ServicePage>
</div>
<div class="animate-fadeIn" class:hidden={currentPage.id !== 'discord-service'}>
	<ServicePage serviceName="discord-service" title="Discord Service">
		<DiscordPage />
	</ServicePage>
</div>
<div class="animate-fadeIn" class:hidden={currentPage.id !== 'stt-service'}>
	<ServicePage serviceName="stt-service" title="Speech-to-Text Service">
		<SttPage />
	</ServicePage>
</div>
