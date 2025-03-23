<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import LogsDisplay from './LogsDisplay.svelte';

	const { children, serviceName } = $props();

	let activeTab = $state('configuration');
</script>

<div class="tabs">
	<button
		class="tab-button rounded-tl-xl {activeTab === 'configuration'
			? 'tab-button-active'
			: 'tab-button-inactive'}"
		onclick={() => (activeTab = 'configuration')}
	>
		<Icon
			path="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z"
			class="icon-sm mr-2"
		/>
		Configuration
	</button>
	<button
		class="tab-button rounded-tr-xl {activeTab === 'logs'
			? 'tab-button-active'
			: 'tab-button-inactive'}"
		onclick={() => (activeTab = 'logs')}
	>
		<Icon
			path="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
			class="icon-sm mr-2"
		/>
		Logs
	</button>
</div>

<div class="animate-in" class:hidden={activeTab !== 'configuration'}>
	{@render children()}
</div>
<div class="animate-in" class:hidden={activeTab !== 'logs'}>
	<LogsDisplay visible={activeTab === 'logs'} {serviceName} />
</div>
