<script lang="ts">
	import {
		alertConnectionStatus,
		alerts,
		connect,
		disconnect,
		formatTimestamp
	} from '$lib/pages/services/alerts/alertsService';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import Card from '$lib/components/Card.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { onMount, tick } from 'svelte';
	import ServicePage from '../ServicePage.svelte';

	// State for auto-scrolling
	let alertContainer: HTMLElement | undefined = $state();
	let shouldScroll = $derived(
		!!alertContainer &&
			alertContainer.scrollHeight - alertContainer.clientHeight - alertContainer.scrollTop < 50
	);

	// Helper for platform colors
	function getPlatformClass(platform: string | undefined): string {
		switch (platform) {
			case 'twitch':
				return 'text-purple-400';
			case 'youtube':
				return 'text-red-500';
			case 'kick':
				return 'text-green-300';
			default:
				return 'text-text-disabled';
		}
	}

	// Helper for alert type colors/icons
	function getAlertStyle(type: string | undefined): { color: string; icon: string } {
		switch (type) {
			case 'follow':
				return {
					color: 'text-info',
					icon: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z'
				}; // User add
			case 'sub':
			case 'resub':
			case 'giftsub':
			case 'communitygiftsub':
				return {
					color: 'text-primary',
					icon: 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z'
				}; // Star
			case 'tip':
				return {
					color: 'text-success',
					icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z'
				}; // Currency Dollar
			case 'cheer':
				return {
					color: 'text-success-dark',
					icon: 'M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
				}; // Emoji Happy
			case 'raid':
				return { color: 'text-warning', icon: 'M13 10V3L4 14h7v7l9-11h-7z' }; // Lightning Bolt
			case 'host':
				return {
					color: 'text-warning-dark',
					icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
				}; // Home
			case 'test':
				return {
					color: 'text-info-dark',
					icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z'
				}; // Beaker
			case 'redemption': // Added
				return {
					color: 'text-info-light',
					icon: 'M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4H5z'
				}; // Gift
			case 'merch': // Added
				return {
					color: 'text-primary-light',
					icon: 'M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z'
				}; // Shopping Bag
			case 'charityCampaignDonation': // Added
				return {
					color: 'text-success-light',
					icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z'
				}; // Heart

			default:
				return {
					color: 'text-text-base',
					icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
				}; // Question Mark Circle
		}
	}

	// Auto scroll effect
	$effect(() => {
		if (!shouldScroll) return;
		// Wait for the DOM to update after new message added
		tick().then(() => {
			if (alertContainer) {
				alertContainer.scrollTop = alertContainer.scrollHeight;
			}
		});
	});

	onMount(() => {
		connect();
		return () => {
			disconnect();
		};
	});
</script>

<ContentPage name="alerts-page">
	<ServicePage serviceName="alerts-service">
		<Card title="Stream Alerts">
			<!-- Connection Status -->
			<div class="text-text-muted mb-2 text-xs">
				Feed Status: <span
					class:text-success-light={$alertConnectionStatus === 'connected'}
					class:text-warning-light={$alertConnectionStatus === 'connecting'}
					class:text-danger-light={$alertConnectionStatus === 'disconnected' ||
						$alertConnectionStatus === 'error'}>{$alertConnectionStatus}</span
				>
			</div>

			<!-- Alert List -->
			<div
				bind:this={alertContainer}
				class="border-border-base bg-bg-surface flex h-96 flex-grow flex-col overflow-y-auto rounded border p-3"
				style="max-height: 70vh;"
			>
				{#if $alerts.length === 0}
					<p class="text-text-muted m-auto text-center">
						{#if $alertConnectionStatus === 'connected'}
							Connected. Waiting for alerts...
						{:else if $alertConnectionStatus === 'connecting'}
							Connecting to alert feed...
						{:else}
							Disconnected from alert feed. Check status.
						{/if}
					</p>
				{:else}
					<!-- Display alerts newest first (store adds to beginning) -->
					{#each $alerts as alert}
						{@const style = getAlertStyle(alert.type)}
						{@const platformClass = getPlatformClass(alert.platform)}

						<div class="mb-2 flex items-start break-words text-sm">
							<!-- Icon Column -->
							<div class="mr-2 pt-0.5">
								<Icon path={style.icon} class="icon-sm {style.color}" />
							</div>
							<!-- Content Column -->
							<div class="flex-1">
								<!-- Header -->
								<div class="mb-0.5">
									<span class="text-text-muted mr-1">[{formatTimestamp(alert.timestamp)}]</span>
									<span class="font-semibold {platformClass}"
										>[{alert.platform?.toUpperCase()}]</span
									>
									<span class="mx-1 font-semibold {style.color}">[{alert.type?.toUpperCase()}]</span
									>
									<!-- Body -->
									{#if alert.type === 'follow'}
										<span class="font-semibold">{alert.user}</span> just followed!
									{:else if alert.type === 'sub' || alert.type === 'resub'}
										<span class="font-semibold">{alert.user}</span> subscribed
										{#if alert.tier}(Tier {alert.tier}){/if}
										{#if alert.type === 'resub'}for {alert.amount} months!{/if}
									{:else if alert.type === 'giftsub'}
										<span class="font-semibold">{alert.gifter || 'Someone'}</span> gifted a sub to
										<span class="font-semibold">{alert.recipient}!</span>
									{:else if alert.type === 'communitygiftsub'}
										<span class="font-semibold">{alert.gifter || 'Someone'}</span> gifted {alert.amount}
										subs to the community!
									{:else if alert.type === 'tip'}
										<span class="font-semibold">{alert.user}</span> tipped
										<span class="font-semibold">{alert.amount} {alert.currency}!</span>
									{:else if alert.type === 'cheer'}
										<span class="font-semibold">{alert.user}</span> cheered
										<span class="font-semibold">{alert.amount} bits!</span>
									{:else if alert.type === 'raid'}
										<span class="font-semibold">{alert.user}</span> raided with {alert.amount} viewers!
									{:else if alert.type === 'host'}
										<span class="font-semibold">{alert.user}</span> is hosting with {alert.amount} viewers!
									{:else if alert.type === 'test'}
										Test Event from <span class="font-semibold"
											>{alert.user || 'StreamElements'}</span
										>
										{#if alert.amount}(Amount: {alert.amount}){/if}
									{:else if alert.type === 'redemption'}
										<span class="font-semibold">{alert.user || 'Someone'}</span> redeemed
										{#if alert.message}<span class="font-semibold"> {alert.message}</span>{/if}!
									{:else if alert.type === 'merch'}
										<span class="font-semibold">{alert.user || 'Someone'}</span> purchased merch!
										{#if alert.message}<span class="text-text-subtle ml-1">
												({alert.message})</span
											>{/if}
									{:else if alert.type === 'charityCampaignDonation'}
										<span class="font-semibold">{alert.user || 'Someone'}</span> donated
										<span class="font-semibold">{alert.amount} {alert.currency}</span> to charity!
									{:else}
										<!-- Fallback for unknown -->
										<span class="font-semibold">{alert.user || 'Someone'}</span> triggered {alert.type}
										{#if alert.amount}({alert.amount}){/if}
									{/if}

									{#if alert.message}
										<span class="text-text-subtle ml-1 italic">"{alert.message}"</span>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</Card>
	</ServicePage>
</ContentPage>
