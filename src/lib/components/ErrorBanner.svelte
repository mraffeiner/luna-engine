<script lang="ts">
	import Icon from './Icon.svelte';

	const { errorMessage } = $props();
</script>

<div class="alert-error animate-in px-12 py-5">
	<div class="flex-between">
		<div class="flex-start">
			<Icon
				path="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				class="text-danger icon-lg mr-3"
			/>
			<div>
				<strong class="error-title">Service Error</strong>
				<span class="block">{$errorMessage}</span>
			</div>
		</div>
		<button
			onclick={() => errorMessage.set(null)}
			class="text-danger-light hover:text-danger focus:border-border-focus rounded-full p-1.5"
			title="Dismiss"
		>
			<Icon path="M6 18L18 6M6 6l12 12" class="icon-lg" />
		</button>
	</div>
</div>
