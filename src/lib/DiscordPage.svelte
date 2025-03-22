<script lang="ts">
	import { discordService } from '$lib/discordService';
	import { SvelteMap } from 'svelte/reactivity';
	import { discordOutput } from '$lib/stores';
	import Icon from './Icon.svelte';
	import Card from './Card.svelte';

	let guildId: string = $state('1194692480805904384');
	let channelId: string = $state('1349007184406642798');
	let speakerAudio: SvelteMap<string, string> = $state(new SvelteMap());

	let forwardOutput = $state(true);

	async function connect() {
		const success = await discordService.connect(guildId, channelId);
		if (success) {
			discordService.connectWebSocket(async (username, audioBlob) => {
				speakerAudio.set(username, URL.createObjectURL(audioBlob));
				if (forwardOutput) {
					discordOutput.set({ username: username, audioBlob: audioBlob });
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

<Card title="Discord Settings">
	<div class="flex-start">
		<label class="space-x-2">
			<input type="checkbox" bind:checked={forwardOutput} />
			<span class="luna-text-muted">Forward Output</span>
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

	<div class="flex items-center space-x-2">
		<button onclick={connect} class="btn-primary"> Connect </button>

		<button onclick={disconnect} class="btn-secondary"> Disconnect </button>
	</div>

	{#each [...speakerAudio] as [username, audioUrl]}
		<div class="luna-border-subtle luna-bg-surface mt-6 rounded-lg border p-4">
			<h4 class="luna-text-subtle mb-2 flex items-center text-sm font-medium">
				<Icon
					path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
					class="luna-text-success icon-sm mr-2"
				/>
				{username}
			</h4>
			<audio controls src={audioUrl} class="w-full rounded-md"></audio>
		</div>
	{/each}
</Card>
