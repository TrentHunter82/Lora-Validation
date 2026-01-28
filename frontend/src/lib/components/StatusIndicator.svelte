<script>
	let { status = 'running', modelCount = 4 } = $props();
</script>

<div class="text-center py-12">
	{#if status !== 'complete'}
		<div
			class="w-12 h-12 border-4 border-led-orange border-t-transparent rounded-full animate-spin mx-auto"
			style="box-shadow: 0 0 12px rgba(249, 115, 22, 0.5);"
		></div>
		<p class="text-metal-200 mt-4">Running validation across {modelCount} model{modelCount !== 1 ? 's' : ''}...</p>
		<p class="text-sm text-metal-400">This may take a few minutes</p>
	{/if}
</div>
