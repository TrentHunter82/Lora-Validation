<script>
	let { label, options = [], value = $bindable(''), enabled = $bindable(true) } = $props();
</script>

<div class="block {enabled ? '' : 'opacity-40'}">
	<div class="flex items-center justify-between mb-1">
		<span class="text-sm font-medium text-metal-300">{label}</span>
		<button
			onclick={() => enabled = !enabled}
			aria-label="Toggle {label}"
			class="flex-shrink-0 w-8 h-4 rounded-full transition-all duration-200 relative
				{enabled
					? 'bg-led-green/30 border-led-green/50'
					: 'bg-metal-800 border-metal-700'}
				border"
		>
			<div
				class="absolute top-0.5 w-2.5 h-2.5 rounded-full transition-all duration-200
					{enabled
						? 'left-4 bg-led-green led-glow text-led-green'
						: 'left-0.5 bg-metal-500'}"
			></div>
		</button>
	</div>
	<select
		bind:value
		disabled={!enabled}
		class="w-full bg-metal-900 border border-white/5 rounded-lg px-4 py-2 text-metal-100 recessed focus-metal
			disabled:text-metal-500 disabled:cursor-not-allowed transition-all duration-200"
	>
		<option value="" class="bg-metal-900 text-metal-400">Select a LoRA...</option>
		{#each options as opt}
			<option value={opt} class="bg-metal-900 text-metal-100">{opt}</option>
		{/each}
	</select>
</div>
