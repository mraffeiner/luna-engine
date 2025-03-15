<script lang="ts">
	import { discordService } from '$lib/discordService';
	import { serviceError } from '$lib/containerService';

	let guildId: string = $state('1194692480805904384');
	let channelId: string = $state('1349007184406642798');
	let userAudioBuffers: Map<string, Blob[]> = $state(new Map());
	let lastChunkTime: number = $state(0);
	let currentUserKey: string = $state('user1');
	let userCounter: number = $state(1);
	let audioPlayer: HTMLAudioElement | null = $state(null);

	const TIME_THRESHOLD = 100; // Milliseconds

	async function connect() {
		console.log('Connect function called');
		const success = await discordService.connect(guildId, channelId);
		if (success) {
			await discordService.connectWebSocket((chunk: Blob) => {
				console.log('Received audio chunk:', chunk);
				const now = Date.now();
				if (now - lastChunkTime > TIME_THRESHOLD) {
					// Assume a new "user" is speaking
					userCounter++;
					currentUserKey = `user${userCounter}`;
					console.log('New user key:', currentUserKey);
				}
				lastChunkTime = now;

				if (userAudioBuffers.has(currentUserKey)) {
					userAudioBuffers.set(currentUserKey, [...userAudioBuffers.get(currentUserKey)!, chunk]);
				} else {
					userAudioBuffers.set(currentUserKey, [chunk]);
				}
				userAudioBuffers = userAudioBuffers; // Trigger reactivity
				console.log('userAudioBuffers:', userAudioBuffers);
			});
		}
	}

	async function disconnect() {
		const success = await discordService.disconnect();
	}

	function playAudio(userKey: string) {
		if (userAudioBuffers.has(userKey)) {
			const audioBlob = new Blob(userAudioBuffers.get(userKey), { type: 'audio/wav' });
			const audioUrl = URL.createObjectURL(audioBlob);

			if (!audioPlayer) {
				audioPlayer = new Audio(audioUrl);
			} else {
				audioPlayer.src = audioUrl;
			}

			audioPlayer.play().catch((e) => console.error('Error playing audio:', e));
		}
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

	{#if $serviceError}
		<div class="mb-6 rounded-md border border-red-800 bg-red-900 bg-opacity-30 p-3">
			<p class="flex items-center text-red-400">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="mr-2 h-5 w-5"
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
				{$serviceError}
			</p>
		</div>
	{/if}

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
	<div class="mt-6">
		{#each Array(userCounter) as _, i}
			<button
				onclick={() => playAudio(`user${i + 1}`)}
				class="rounded-md bg-indigo-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-indigo-700"
			>
				Play User {i + 1}
			</button>
		{/each}
	</div>
</div>
