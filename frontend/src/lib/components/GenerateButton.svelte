<script>
	let { loading = false, disabled = false, onclick, label = 'Run Validation', title = '' } = $props();
</script>

<span class="block w-full" title={disabled || loading ? title : ''}>
	<button
		{onclick}
		disabled={disabled || loading}
		class="w-full mt-6 px-6 py-3
			bg-gradient-to-b from-metal-600 to-metal-700
			border border-metal-600/50
			text-metal-100 font-semibold rounded-lg
			metal-shimmer raised-metal
			hover:from-metal-500 hover:to-metal-600
			active:from-metal-700 active:to-metal-800
			disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
			transition-all duration-200"
	>
		{label}
	</button>
</span>
