<script lang="ts">
	import '../app.css';
	import Sidebar from '$lib/Sidebar.svelte';
	import { serviceError, containerService } from '$lib/containerService';
	import { onMount } from 'svelte';
	import { beforeNavigate } from '$app/navigation';
	import { page } from '$app/state';
	import ServicePage from '$lib/ServicePage.svelte';
	import SttForm from '$lib/SttForm.svelte';
	import LlmForm from '$lib/LlmForm.svelte';
	import TtsForm from '$lib/TtsForm.svelte';
	import DiscordForm from '$lib/DiscordForm.svelte';

	let { children } = $props();

	// List of all services in the application
	const services = [
		'discord-service',
		'llm-service',
		'tts-service',
		'stt-service',
		'discord-service'
	];

	function handleBeforeUnload() {
		services.forEach((serviceName) => {
			containerService.stopLogStream(serviceName);
		});
	}

	// Initialize the application
	onMount(() => {
		window.addEventListener('beforeunload', handleBeforeUnload);

		// Clear any existing errors
		serviceError.set(null);

		// Check the status of all services
		services.forEach((serviceName) => {
			containerService.checkContainerStatus(serviceName);
		});

		return () => {
			window.removeEventListener('beforeunload', handleBeforeUnload);
		};
	});

	// Clear errors on navigation
	beforeNavigate(() => {
		serviceError.set(null);
	});

	// Get the current route path
	const currentPath = $derived(page.url.pathname);
</script>

<div class="flex h-screen bg-gray-900 text-white">
	<Sidebar />
	<main class="flex-1 overflow-auto p-4">
		{#if $serviceError}
			<div
				class="mb-6 rounded-lg border border-red-800 bg-red-900 bg-opacity-30 p-4 text-red-400 shadow-md"
			>
				<div class="flex items-start justify-between">
					<div class="flex">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="mr-3 h-6 w-6 flex-shrink-0"
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
						class="ml-4 rounded-full p-1 text-red-400 transition-colors duration-200 hover:bg-red-800 hover:bg-opacity-30 focus:outline-none focus:ring-2 focus:ring-red-700"
						title="Dismiss"
						aria-label="Dismiss error message"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
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

		<!-- Root page (Control Panel Backend) -->
		{#if currentPath === '/'}
			{@render children()}
		{:else}
			<!-- Service Pages - Always mounted, conditionally displayed -->
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

			<div class:hidden={currentPath !== '/discord-service'}>
				<ServicePage serviceName="discord-service" title="Discord Service">
					<DiscordForm />
				</ServicePage>
			</div>
		{/if}
	</main>
</div>
