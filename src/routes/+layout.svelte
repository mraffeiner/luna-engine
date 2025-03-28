<script lang="ts">
	import '../app.css';
	import ErrorBanner from '$lib/components/ErrorBanner.svelte';
	import { serviceError } from '$lib/pages/services/docker/dockerService';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import EngineMonitor from '$lib/components/EngineMonitor.svelte';

	let { children } = $props();
</script>

<div class="bg-bg-base flex h-screen">
	<Sidebar />
	<main class="flex-1 overflow-auto">
		<div class="bg-bg-base sticky top-0 z-10">
			{#if $serviceError}
				<ErrorBanner errorMessage={serviceError} />
			{/if}
			<EngineMonitor />
		</div>
		<div class="max-w-3/4 mx-auto p-6">
			{@render children()}
		</div>
	</main>
</div>
