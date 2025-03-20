<script lang="ts">
	/**
	 * Icon component for consistent SVG icon rendering
	 *
	 * Usage:
	 * <Icon path="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" class="luna-primary-light icon-sm mr-2" />
	 */

	// Props
	const { path, class: className = '' } = $props<{
		path: string;
		class?: string;
	}>();
</script>

<svg
	xmlns="http://www.w3.org/2000/svg"
	class="icon {className}"
	fill="none"
	viewBox="0 0 24 24"
	stroke="currentColor"
	aria-hidden="true"
>
	<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={path} />
</svg>
