<script lang="ts">
	import '../app.css';
	import ErrorBanner from '$lib/components/ErrorBanner.svelte';
	import { serviceError } from '$lib/pages/services/docker/dockerService';
	import Sidebar from '$lib/components/Sidebar.svelte';

	let { children } = $props();
</script>

<div class="bg-bg-base flex h-screen">
	<Sidebar />
	<main class="flex-1 overflow-auto p-6">
		{#if $serviceError}
			<ErrorBanner errorMessage={serviceError} />
		{/if}

		<div class="max-w-3/4 mx-auto">
			{@render children()}
		</div>
	</main>
</div>
