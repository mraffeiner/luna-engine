<script lang="ts">
	import EnginePage from '$lib/pages/EnginePage.svelte';
	import PromptPage from '$lib/pages/prompt/PromptPage.svelte';
	import DiscordPage from '$lib/pages/services/discord/DiscordPage.svelte';
	import DockerPage from '$lib/pages/services/docker/DockerPage.svelte';
	import { dockerService } from '$lib/pages/services/docker/dockerService';
	import LlmPage from '$lib/pages/services/llm/LlmPage.svelte';
	import SttPage from '$lib/pages/services/stt/SttPage.svelte';
	import TtsPage from '$lib/pages/services/tts/TtsPage.svelte';
	import { SERVICE_PAGES } from '$lib/shared/constants';
	import { onMount } from 'svelte';

	const cleanup = () => {
		dockerService.stopLogsStream();
	};

	onMount(() => {
		window.addEventListener('beforeunload', cleanup);

		SERVICE_PAGES.forEach((page) => {
			dockerService.checkContainerStatus(page.serviceId);
		});

		dockerService.startLogsStream();

		return () => {
			window.removeEventListener('beforeunload', cleanup);
			cleanup();
		};
	});
</script>

<!-- Load all pages to preserve states, conditionally hidden -->
<DockerPage />
<PromptPage />
<LlmPage />
<SttPage />
<TtsPage />
<DiscordPage />
<!-- Load last to ensure all other pages are fully loaded before engine starts -->
<EnginePage />
