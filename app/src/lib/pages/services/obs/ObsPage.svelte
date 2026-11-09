<script lang="ts">
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import ServicePage from '../ServicePage.svelte';
	import Card from '$lib/components/Card.svelte';
	import { subtitles } from '$lib/shared/shared.svelte';
	import { sendSubtitle } from './obsService';

	$effect(() => {
		sendSubtitle(subtitles.text.trim());
	});
</script>

<ContentPage name="obs-page">
	<ServicePage serviceName="obs-service">
		<!-- Configuration Tab Content -->
		<Card title="OBS Subtitles">
			<div
				class="border-border-base bg-bg-surface min-h-[6rem] whitespace-pre-wrap rounded border p-3 text-sm"
			>
				{#if subtitles.text}
					{subtitles.text}
				{:else}
					<span class="text-text-disabled italic">No subtitle text currently set...</span>
				{/if}
			</div>
		</Card>
	</ServicePage>
</ContentPage>
