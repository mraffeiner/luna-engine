<script lang="ts">
	import { discordService } from '$lib/discordService';
	import { SvelteMap } from 'svelte/reactivity';
	import { discordOutput } from '$lib/stores';
	import Icon from './Icon.svelte';

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

<div class="card">
	<div class="card-header">
		<h2>
			<Icon
				path="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
				class="luna-text-primary-light icon-lg mr-2"
			/>
			Discord Service
		</h2>
	</div>

	<div class="card-body">
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

		<div class="form-group">
			<label class="flex-start space-x-2">
				<input type="checkbox" bind:checked={forwardOutput} />
				<span class="luna-text-subtle">Forward Output</span>
			</label>
		</div>

		<div class="space-x-md">
			<button onclick={connect} class="btn-primary"> Connect </button>

			<button onclick={disconnect} class="btn-secondary"> Disconnect </button>
		</div>

		{#each [...speakerAudio] as [username, audioUrl]}
			<div class="luna-border-subtle luna-bg-surface mt-6 rounded-lg border p-4">
				<h4 class="flex-start luna-text-subtle mb-2 text-sm font-medium">
					<Icon
						path="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
						class="luna-text-success icon-sm mr-1"
					/>
					{username}
				</h4>
				<audio controls src={audioUrl} class="w-full rounded-md"></audio>
			</div>
		{/each}
	</div>
</div>
