<script lang="ts">
	import {
		chatMessages,
		platformStatus,
		webSocketStatus,
		chatService,
		type ConnectionStatus,
		type Platform
	} from './chatService';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import ServicePage from '../ServicePage.svelte';
	import Card from '$lib/components/Card.svelte';
	import Icon from '$lib/components/Icon.svelte'; // Import Icon component
	import { onMount, tick } from 'svelte';

	let chatContainer: HTMLElement | undefined = $state();
	let shouldScroll = $derived(
		!!chatContainer &&
			$chatMessages &&
			chatContainer.scrollHeight - chatContainer.clientHeight - chatContainer.scrollTop < 50
	);

	function formatTimestamp(isoString: string): string {
		try {
			if (!isoString || typeof isoString !== 'string') return '??:??:??';
			const date = new Date(isoString);
			if (isNaN(date.getTime())) return '??:??:??';
			return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
		} catch (e) {
			console.error('Error formatting timestamp:', e, 'Input:', isoString);
			return '??:??:??';
		}
	}

	// Get CSS class for platform text color based on theme
	function getPlatformClass(platform: Platform | 'system' | 'unknown'): string {
		switch (platform) {
			case 'twitch':
				return 'text-purple-400';
			case 'youtube':
				return 'text-red-500';
			case 'system':
				return 'text-warning-light'; // Use warning for system messages
			default:
				return 'text-text-disabled';
		}
	}

	// Get CSS class for status text color based on theme
	function getStatusColor(status: ConnectionStatus | undefined): string {
		switch (status) {
			case 'connected':
				return 'text-success-light';
			case 'connecting':
			case 'authenticated':
				return 'text-warning-light';
			case 'disconnected':
				return 'text-text-disabled';
			case 'auth_required':
				return 'text-primary-light';
			case 'error':
			case 'error_config':
			case 'error_api':
			case 'error_quota':
			case 'error_chat_ended':
			case 'error_auth':
			case 'error_no_live_chat':
				return 'text-danger-light';
			default:
				return 'text-text-disabled';
		}
	}

	// Auto scroll
	$effect(() => {
		if (!shouldScroll) return;

		tick().then(() => {
			chatContainer!.scrollTop = chatContainer!.scrollHeight;
		});
	});

	onMount(() => {
		chatService.connectWebSocket();
	});
</script>

<ContentPage name="chat-page">
	<ServicePage serviceName="chat-service">
		<Card title="Stream Chat">
			<!-- Platform Connection Controls -->
			<div class="border-border-base mb-4 grid grid-cols-1 gap-4 border-b pb-4 md:grid-cols-2">
				<!-- Twitch Controls -->
				<div>
					<h4 class="text-info-light mb-2 text-lg font-semibold">Twitch</h4>
					<div class="flex items-center space-x-2">
						<button class="btn-primary" onclick={() => chatService.connectPlatform('twitch')}>
							<Icon path="M13 10V3L4 14h7v7l9-11h-7z" class="icon-sm mr-1" />
							Connect
						</button>
						<button class="btn-danger" onclick={() => chatService.disconnectPlatform('twitch')}>
							<Icon path="M6 18L18 6M6 6l12 12" class="icon-sm mr-1" />
							Disconnect
						</button>
						<span class="text-text-subtle text-sm">
							Status: <span class={getStatusColor($platformStatus.twitch)}
								>{$platformStatus.twitch}</span
							>
						</span>
					</div>
				</div>

				<!-- YouTube Controls -->
				<div>
					<h4 class="text-danger-light mb-2 text-lg font-semibold">YouTube</h4>
					<div class="flex items-center space-x-2">
						<button class="btn-primary" onclick={() => chatService.connectPlatform('youtube')}>
							<Icon path="M13 10V3L4 14h7v7l9-11h-7z" class="icon-sm mr-1" /> Connect
						</button>
						<button class="btn-danger" onclick={() => chatService.disconnectPlatform('youtube')}>
							<Icon path="M6 18L18 6M6 6l12 12" class="icon-sm mr-1" /> Disconnect
						</button>
						<span class="text-text-subtle text-sm">
							Status: <span class={getStatusColor($platformStatus.youtube)}
								>{$platformStatus.youtube}</span
							>
						</span>
					</div>
					{#if $platformStatus.youtube === 'auth_required'}
						<div class="text-primary-light mt-2 text-sm">
							<Icon
								path="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
								class="icon-sm mr-1 inline-block align-text-bottom"
							/>
							Auth URL copied to clipboard! Paste it into your browser and grant access
						</div>
					{:else if $platformStatus.youtube === 'error_no_live_chat'}
						<div class="text-danger-light mt-2 text-sm">
							<Icon
								path="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
								class="icon-sm mr-1 inline-block align-text-bottom"
							/>
							Could not find an active YouTube live stream chat to connect to.
						</div>
					{/if}
				</div>
			</div>

			<!-- WebSocket Status -->
			<div class="text-text-muted mb-4 text-xs">
				WebSocket Feed Status: <span
					class:text-green-400={$webSocketStatus === 'connected'}
					class:text-yellow-400={$webSocketStatus === 'connecting'}
					class:text-red-400={$webSocketStatus === 'disconnected' || $webSocketStatus === 'error'}
					>{$webSocketStatus}</span
				>
			</div>

			<!-- Chat Messages Area -->
			<div
				bind:this={chatContainer}
				class="chat-container border-border-base bg-bg-surface h-96 flex-grow overflow-y-auto rounded border p-3"
				style="max-height: 60vh;"
			>
				{#if $chatMessages.length === 0}
					<p class="text-text-muted text-center">Connect a platform to see messages...</p>
				{:else}
					{#each $chatMessages as message, i (message.timestamp + message.author + i)}
						<div class="mb-2 break-words text-sm">
							<span class="text-text-muted mr-1">[{formatTimestamp(message.timestamp)}]</span>
							{#if message.platform !== 'system'}
								<span class="font-semibold {getPlatformClass(message.platform)}">
									[{message.platform.toUpperCase()}]
								</span>
								<span class="text-primary-light mx-1 font-semibold">{message.author}:</span>
							{/if}
							<span
								class:italic={message.platform === 'system'}
								class:text-warning-light={message.platform === 'system'}>{message.text}</span
							>
						</div>
					{/each}
				{/if}
			</div>
		</Card>
	</ServicePage>
</ContentPage>
