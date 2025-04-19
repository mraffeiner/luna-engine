<script lang="ts">
	import ServicePage from '../ServicePage.svelte';
	import ContentPage from '$lib/pages/ContentPage.svelte';
	import { modelParams, connect, createParam, deleteParam, loading, setParams } from './vtsService';
	import Spinner from '$lib/components/Spinner.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import Card from '$lib/components/Card.svelte';

	let paramName: string = $state('CustomNewParam');
	let paramMin: number = $state(-1.0);
	let paramMax: number = $state(1.0);
	let paramDefault: number = $state(0.0);

	$effect(() => {
		if ($modelParams) {
			setParams($modelParams);
		}
	});
</script>

<ContentPage name="vts-page">
	<ServicePage serviceName="vts-service">
		<Card title="VTube Studio Controls">
			<div class="form-group">
				<button onclick={connect} disabled={$loading} class="btn-primary">
					{#if $loading}
						<Spinner class="icon-lg text-text-base mr-2" />
					{/if}
					{$loading ? 'Connecting..' : 'Connect'}
				</button>
			</div>

			{#if $modelParams.length > 0}
				<div class="form-control">
					<h3>Available Custom Parameters</h3>
					<div class="grid grid-cols-4 gap-4">
						{#each $modelParams as param}
							<div class="flex-between text-text-muted text-lg font-medium">
								<div class="mb-2">
									<label for={param.name}>{param.name}</label>
									<div class="relative mt-1 px-1">
										<input
											id={param.name}
											type="range"
											min={param.min}
											max={param.max}
											defaultValue={param.defaultValue}
											step="0.1"
											bind:value={param.value}
										/>
										<div class="text-text-disabled flex-center mt-2 px-1 text-xs">
											<span
												class="bg-bg-elevated text-primary-light rounded-md px-2 py-1 font-medium"
											>
												{param.value}
											</span>
										</div>
									</div>
								</div>
								<button type="button" onclick={() => deleteParam(param.name)} class="btn-danger">
									<Icon
										path="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
										class="icon-sm mr-2"
									/>
								</button>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<div class="form-control">
				<h3>New Model Parameter</h3>

				<div class="mb-2">
					<label for="newParamName">Name</label>
					<input type="text" id="newParamName" bind:value={paramName} class="form-control" />
				</div>

				<div class="flex-between">
					<div class="mb-2">
						<label for="newParamMin">Min</label>
						<div class="relative mt-1 px-1">
							<input
								id="newParamMin"
								type="range"
								min="-10"
								max="0"
								step="0.1"
								bind:value={paramMin}
							/>
							<div class="text-text-disabled flex-center mt-2 px-1 text-xs">
								<span class="bg-bg-elevated text-primary-light rounded-md px-2 py-1 font-medium"
									>{paramMin}</span
								>
							</div>
						</div>
					</div>

					<div class="mb-2">
						<label for="newParamDefault">Default</label>
						<div class="relative mt-1 px-1">
							<input
								id="newParamDefault"
								type="range"
								min="-10"
								max="10"
								step="0.1"
								bind:value={paramDefault}
							/>
							<div class="text-text-disabled flex-center mt-2 px-1 text-xs">
								<span class="bg-bg-elevated text-primary-light rounded-md px-2 py-1 font-medium"
									>{paramDefault}</span
								>
							</div>
						</div>
					</div>

					<div class="mb-2">
						<label for="newParamMax">Max</label>
						<div class="relative mt-1 px-1">
							<input
								id="newParamMax"
								type="range"
								min="0"
								max="10"
								step="0.1"
								bind:value={paramMax}
							/>
							<div class="text-text-disabled flex-center mt-2 px-1 text-xs">
								<span class="bg-bg-elevated text-primary-light rounded-md px-2 py-1 font-medium"
									>{paramMax}</span
								>
							</div>
						</div>
					</div>
				</div>

				<button
					onclick={() => createParam(paramName, paramMin, paramMax, paramDefault)}
					class="btn-primary"
				>
					Create
				</button>
			</div>
		</Card>
	</ServicePage>
</ContentPage>
