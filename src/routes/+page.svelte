<script lang="ts">
	import { dockerService } from '$lib/dockerService';
	import HomePage from '$lib/pages/HomePage.svelte';
	import PromptPage from '$lib/pages/PromptPage.svelte';
	import DiscordPage from '$lib/pages/services/DiscordPage.svelte';
	import DockerPage from '$lib/pages/services/DockerPage.svelte';
	import LlmPage from '$lib/pages/services/LlmPage.svelte';
	import SttPage from '$lib/pages/services/SttPage.svelte';
	import TtsPage from '$lib/pages/services/TtsPage.svelte';

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

<!-- Load all pages to preserve states, conditionally hidden -->
<HomePage />
<DockerPage />
<PromptPage />
<LlmPage />
<TtsPage />
<DiscordPage />
<SttPage />
