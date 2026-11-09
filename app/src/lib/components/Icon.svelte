<script lang="ts">
	/**
	 * Icon component for consistent SVG icon rendering
	 *
	 * Usage:
	 * <Icon path="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" class="text-primary-light icon-sm mr-2" />
	 */

	// Props
	const {
		path,
		class: className = '',
		strokeWidth = '2'
	} = $props<{
		path: string;
		strokeWidth?: string;
		class?: string;
	}>();
</script>

<svg
	xmlns="http://www.w3.org/2000/svg"
	class={className}
	fill="none"
	viewBox="0 0 24 24"
	stroke="currentColor"
	aria-hidden="true"
>
	<path stroke-linecap="round" stroke-linejoin="round" stroke-width={strokeWidth} d={path} />
</svg>
