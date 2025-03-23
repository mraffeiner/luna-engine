<script lang="ts">
	import HomePage from '$lib/pages/HomePage.svelte';
	import PromptPage from '$lib/pages/prompt/PromptPage.svelte';
	import DiscordPage from '$lib/pages/services/discord/DiscordPage.svelte';
	import DockerPage from '$lib/pages/services/docker/DockerPage.svelte';
	import { dockerService } from '$lib/pages/services/docker/dockerService';
	import LlmPage from '$lib/pages/services/llm/LlmPage.svelte';
	import SttPage from '$lib/pages/services/stt/SttPage.svelte';
	import TtsPage from '$lib/pages/services/tts/TtsPage.svelte';

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
