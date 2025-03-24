<script lang="ts">
	let { forward = $bindable(), title, children } = $props();
</script>

<div class="card h-full">
	<div class="flex-between mb-2 items-baseline">
		<h3>{title}</h3>
		<label>
			<span class="text-text-subtle mr-2 text-base font-bold">Forward</span>
			<input type="checkbox" bind:checked={forward} />
		</label>
	</div>
	<div class="min-h-24">
		{@render children()}
	</div>
</div>
