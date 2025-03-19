<script lang="ts">
	import '../app.css';
	import Sidebar from '$lib/Sidebar.svelte';
	import { serviceError, dockerService } from '$lib/dockerService';
	import { page } from '$app/state';
	import ServicePage from '$lib/ServicePage.svelte';
	import SttForm from '$lib/SttForm.svelte';
	import LlmForm from '$lib/LlmForm.svelte';
	import TtsForm from '$lib/TtsForm.svelte';
	import DiscordForm from '$lib/DiscordForm.svelte';
	import DockerForm from '$lib/DockerForm.svelte';
	import PromptForm from '$lib/PromptForm.svelte';

	let { children } = $props();

	// Get the current route path
	const currentPath = $derived(page.url.pathname);

	const handleBeforeUnload = () => {
		dockerService.stopLogsStream();
	};

	$effect(() => {
		window.addEventListener('beforeunload', handleBeforeUnload);

		return () => {
			window.removeEventListener('beforeunload', handleBeforeUnload);
		};
	});

	$effect(() => {
		dockerService.startLogsStream();

		return () => {
			dockerService.stopLogsStream();
		};
	});
</script>

<div class="luna-bg-base luna-text-base flex h-screen">
	<Sidebar />
	<main class="flex-1 overflow-auto p-6">
		{#if $serviceError}
			<div class="alert-error animate-fadeIn">
				<div class="flex-between">
					<div class="flex-start">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="icon icon-lg icon-danger mr-3"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
							/>
						</svg>
						<div>
							<strong class="error-title">Service Error</strong>
							<span class="block">{$serviceError}</span>
						</div>
					</div>
					<button
						onclick={() => serviceError.set(null)}
						class="btn-sm luna-text-danger-light hover:luna-bg-danger focus:luna-border-focus rounded-full p-1.5 hover:bg-opacity-30"
						title="Dismiss"
						aria-label="Dismiss error message"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="icon"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				</div>
			</div>
		{/if}

		<div class="animate-fadeIn">
			<!-- Root page (Control Panel Backend) -->
			{#if currentPath === '/'}
				{@render children()}
			{:else}
				<!-- Service Pages - Always mounted, conditionally displayed -->
				<div class:hidden={currentPath !== '/docker-service'}>
					<ServicePage serviceName="docker-service" title="Docker Service">
						<DockerForm />
					</ServicePage>
				</div>

				<div class:hidden={currentPath !== '/discord-service'}>
					<ServicePage serviceName="discord-service" title="Discord Service">
						<DiscordForm />
					</ServicePage>
				</div>

				<div class:hidden={currentPath !== '/stt-service'}>
					<ServicePage serviceName="stt-service" title="Speech-to-Text Service">
						<SttForm />
					</ServicePage>
				</div>

				<div class:hidden={currentPath !== '/llm-service'}>
					<ServicePage serviceName="llm-service" title="LLM Service">
						<LlmForm />
					</ServicePage>
				</div>

				<div class:hidden={currentPath !== '/tts-service'}>
					<ServicePage serviceName="tts-service" title="Text-to-Speech Service">
						<TtsForm />
					</ServicePage>
				</div>

				<div class:hidden={currentPath !== '/prompt-service'}>
					<ServicePage serviceName="prompt-service" title="Prompt Service">
						<PromptForm />
					</ServicePage>
				</div>
			{/if}
		</div>
	</main>
</div>
