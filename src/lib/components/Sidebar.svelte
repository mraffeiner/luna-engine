<script lang="ts">
	import Icon from './Icon.svelte';
	import { containerStatus, currentPage } from '$lib/shared/shared.svelte';
	import { PAGES } from '$lib/shared/constants';
</script>

<aside
	class="glass-effect border-border-base bg-bg-surface text-text-base flex h-full w-56 flex-col border-r shadow-xl"
>
	<div class="border-border-base bg-bg-base flex-center border-b">
		<button
			onclick={() => {
				currentPage.id = PAGES[0].id;
				currentPage.name = PAGES[0].name;
			}}
			class="flex-center grow cursor-pointer p-5 pl-2"
		>
			<Icon path="M13 10V3L4 14h7v7l9-11h-7z" class="text-primary-light icon-lg mr-2" />
			<span class="text-xl font-bold {currentPage.id === PAGES[0].id ? 'text-primary-subtle' : ''}"
				>Luna Engine</span
			>
		</button>
	</div>

	<nav class="flex-1 overflow-y-auto">
		<ul>
			{#each PAGES.slice(1, PAGES.length) as page}
				{@const selected = currentPage.id === page.id}
				<li>
					<button
						onclick={() => {
							currentPage.id = page.id;
							currentPage.name = page.name;
						}}
						class="flex w-full cursor-pointer items-center px-4 py-3 {selected
							? 'glass-effect bg-bg-elevated/50 pl-5'
							: ''}"
					>
						{#if page.serviceId}
							{@const status = containerStatus.get(page.serviceId)}
							<Icon
								path={page.icon}
								class="icon-sm mr-2
									{status === 'RUNNING'
									? selected
										? 'text-success-light'
										: 'text-success'
									: selected
										? 'text-danger-light'
										: 'text-danger'}
									{status === 'STARTING' || status === 'STOPPING' ? 'animate-pulse' : ''}"
							/>
						{:else}
							<Icon
								path={page.icon}
								class="icon-sm mr-2 {selected ? 'text-primary' : 'text-primary-light'}"
							/>
						{/if}
						<span class="font-medium {selected ? 'text-primary-light' : ''}">{page.name}</span>
					</button>
				</li>
			{/each}
		</ul>
	</nav>

	<div class="border-border-base border-t p-4">
		<div class="text-text-disabled flex items-center text-sm">
			<Icon path="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" class="icon-sm mr-2" />
			<p>Luna Engine Control Panel</p>
		</div>
	</div>
</aside>
