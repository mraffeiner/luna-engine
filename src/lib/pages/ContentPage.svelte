<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import { currentPage } from '$lib/shared.svelte';

	const { children, name } = $props();
</script>

<div class="animate-in my-16" class:hidden={currentPage.id !== name}>
	<h1 class="flex items-center">
		<Icon
			path="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
			class="text-primary-light icon-lg mr-3"
		/>
		{currentPage.name}
	</h1>

	{@render children()}
</div>
