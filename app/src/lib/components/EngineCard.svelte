<script lang="ts">
	let { receiveInput = $bindable(), title, children } = $props();
</script>

<div class="card h-full">
	<div class="flex-between mb-2">
		<h3>{title}</h3>
		<label>
			<span>Receive Input</span>
			<input type="checkbox" bind:checked={receiveInput} />
		</label>
	</div>
	<div class="min-h-24 overflow-auto">
		{@render children()}
	</div>
</div>
