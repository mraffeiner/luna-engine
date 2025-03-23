<script>
	import Card from '$lib/components/Card.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import { SERVICE_PAGES } from '$lib/shared/constants';
	import { containerStatus } from '$lib/shared/shared.svelte';
	import ServicePage from '../ServicePage.svelte';
	import { dockerService } from './dockerService';

	const pageId = 'docker-page';
	const serviceId = 'docker-service';
</script>

<ContentPage name={pageId}>
	<ServicePage serviceName={serviceId}>
		<div class="grid grid-cols-4 gap-4">
			{#each SERVICE_PAGES.filter((p) => p.serviceId !== serviceId) as page}
				{@const status = containerStatus.get(page.serviceId)}
				<Card title={page.name}>
					<div class="flex-between space-x-5">
						<div
							class="glass-effect border-border-subtle ml-auto flex items-center rounded-md border px-4 py-2.5 shadow-md"
						>
							<span class="text-text-subtle text-md mr-4 font-semibold">Status</span>
							<div class="flex items-center">
								<span
									class="{status === 'RUNNING' ? 'status-running' : 'status-stopped'} {status ===
										'STARTING' || status === 'STOPPING'
										? 'animate-pulse'
										: ''}"
									title={status === 'RUNNING' ? 'Running' : 'Stopped'}
								></span>
								<span
									class="text-md ml-2 font-semibold {status === 'RUNNING'
										? 'text-success-light'
										: 'text-danger-light'}"
								>
									{status === 'RUNNING' ? 'Running' : 'Stopped'}
								</span>
							</div>
						</div>

						<button
							onclick={() =>
								status === 'RUNNING'
									? dockerService.stopContainer(page.serviceId)
									: dockerService.startContainer(page.serviceId)}
							class="flex-center w-16 {status === 'RUNNING' ? 'btn-danger' : 'btn-success'}"
							disabled={status === 'STARTING' || status === 'STOPPING'}
						>
							{#if status === 'STARTING' || status === 'STOPPING'}
								<Spinner class="text-text-base icon-sm mr-2" />
							{:else if status === 'RUNNING'}
								<span>Stop</span>
							{:else}
								<span>Start</span>
							{/if}
						</button>
					</div>
				</Card>
			{/each}
		</div>
	</ServicePage>
</ContentPage>
