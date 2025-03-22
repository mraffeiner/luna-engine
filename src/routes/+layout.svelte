<script lang="ts">
	import '../app.css';
	import Sidebar from '$lib/Sidebar.svelte';
	import { serviceError } from '$lib/dockerService';
	import ErrorBanner from '$lib/ErrorBanner.svelte';

	let { children } = $props();
</script>

<div class="luna-bg-base luna-text-base flex h-screen">
	<Sidebar />
	<main class="flex-1 overflow-auto p-6">
		{#if $serviceError}
			<ErrorBanner errorMessage={serviceError} />
		{/if}

		<div class="mx-auto max-w-7xl">
			{@render children()}
		</div>
	</main>
</div>
