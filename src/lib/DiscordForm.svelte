<script lang="ts">
	import { discordService } from '$lib/discordService';
	import { SvelteMap } from 'svelte/reactivity';
	import { discordOutput } from '$lib/stores';

	let guildId: string = $state('1194692480805904384');
	let channelId: string = $state('1349007184406642798');
	let speakerAudio: SvelteMap<string, string> = $state(new SvelteMap());
	let forwardToStt = $state(false);

	async function connect() {
		const success = await discordService.connect(guildId, channelId);
		if (success) {
			await discordService.connectWebSocket(async (username, audioBlob) => {
				speakerAudio.set(username, URL.createObjectURL(audioBlob));
				if (forwardToStt) {
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

<div class="card p-6">
	<h2 class="mb-6 flex items-center">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="mr-2 h-6 w-6 text-indigo-400"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
			/>
		</svg>
		Discord Service
	</h2>

	<div class="mt-4">
		<label for="guildId" class="block text-sm font-medium text-gray-300">Guild ID</label>
		<input
			type="text"
			id="guildId"
			name="guildId"
			bind:value={guildId}
			class="mt-1 block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
		/>
	</div>
	<div class="mt-4">
		<label for="channelId" class="block text-sm font-medium text-gray-300">Channel ID</label>
		<input
			type="text"
			id="channelId"
			name="channelId"
			bind:value={channelId}
			class="mt-1 block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
		/>
	</div>
	<div class="mt-4">
		<label class="inline-flex items-center space-x-2">
			<input
				type="checkbox"
				class="rounded border-gray-600 text-indigo-600 focus:ring-indigo-500"
				bind:checked={forwardToStt}
			/>
			<span class="text-gray-300">Forward to STT</span>
		</label>
	</div>

	<div class="mt-6">
		<button
			onclick={connect}
			class="rounded-md bg-indigo-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-indigo-700"
		>
			Connect
		</button>

		<button
			onclick={disconnect}
			class="rounded-md bg-indigo-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-indigo-700"
		>
			Disconnect
		</button>
	</div>

	{#each [...speakerAudio] as [username, audioUrl]}
		<div class="mt-6 rounded-lg border border-gray-600 bg-gray-800 p-4">
			<h4 class="mb-2 flex items-center text-sm font-medium text-gray-300">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="mr-1 h-4 w-4 text-green-500"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
					/>
				</svg>
				{username}
			</h4>
			<audio controls src={audioUrl} class="w-full rounded-md"></audio>
		</div>
	{/each}
</div>
