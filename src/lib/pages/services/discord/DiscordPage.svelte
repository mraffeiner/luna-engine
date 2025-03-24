<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import { discordOutput } from '$lib/shared/stores';
	import ServicePage from '../ServicePage.svelte';
	import { discordService } from './discordService';
	import { forwardOutput, speakerAudio } from '$lib/shared/shared.svelte';

	let guildId: string = $state('1194692480805904384');
	let channelId: string = $state('1349007184406642798');

	async function connect() {
		const success = await discordService.connect(guildId, channelId);
		if (success) {
			discordService.connectWebSocket(async (username, audioBlob) => {
				let audioUrl = speakerAudio.get(username);
				if (audioUrl) URL.revokeObjectURL(audioUrl);

				audioUrl = URL.createObjectURL(audioBlob);
				speakerAudio.set(username, audioUrl);
				if (forwardOutput.discord) {
					discordOutput.set({ username: username, audioBlob: audioBlob, audioUrl: audioUrl });
				}
			});
		}
	}

	async function disconnect() {
		await discordService.disconnect();
	}

	// Clean up resources when component is destroyed
	$effect(() => {
		return disconnect;
	});
</script>

<ContentPage name="discord-page">
	<ServicePage serviceName="discord-service">
		<Card title="Discord Settings">
			<div class="flex-start">
				<label class="space-x-2">
					<input type="checkbox" bind:checked={forwardOutput.discord} />
					<span class="text-text-muted">Forward Output</span>
				</label>
			</div>

			<div class="form-group">
				<label for="guildId">Guild ID</label>
				<input type="text" id="guildId" name="guildId" bind:value={guildId} class="form-control" />
			</div>

			<div class="form-group">
				<label for="channelId">Channel ID</label>
				<input
					type="text"
					id="channelId"
					name="channelId"
					bind:value={channelId}
					class="form-control"
				/>
			</div>

			<div class="flex items-center space-x-4">
				<button onclick={connect} class="btn-primary">Connect</button>

				<button onclick={disconnect} class="btn-secondary">Disconnect</button>
			</div>

			{#each [...speakerAudio] as [username, audioUrl]}
				<div class="border-border-subtle bg-bg-surface mt-6 rounded-lg border p-4">
					<h4 class="text-text-subtle mb-2 flex items-center text-sm font-medium">
						<Icon
							path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
							class="text-success icon-sm mr-2"
						/>
						{username}
					</h4>
					<audio controls src={audioUrl} class="w-full rounded-md"></audio>
				</div>
			{/each}
		</Card>
	</ServicePage>
</ContentPage>
