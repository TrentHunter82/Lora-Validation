<script>
	let {
		status = 'running',
		modelCount = 4,
		progress = null
	} = $props();

	const MODEL_ORDER = ['flux_grid', 'zimage_grid', 'qwen_grid', 'wan_grid'];
	const MODEL_LABELS = {
		flux_grid: 'FLUX',
		zimage_grid: 'Z-Image',
		qwen_grid: 'Qwen',
		wan_grid: 'WAN'
	};

	let completedModels = $derived(progress?.completed || []);
	let currentModel = $derived(progress?.current_model || null);
	let percent = $derived(progress?.percent || 0);

	function getModelStatus(modelKey) {
		if (completedModels.includes(modelKey)) return 'complete';
		// Map current_model (e.g., 'flux') to grid key (e.g., 'flux_grid')
		if (currentModel && modelKey.startsWith(currentModel)) return 'active';
		return 'pending';
	}
</script>

<div class="py-8">
	{#if status !== 'complete'}
		<!-- Progress Header -->
		<div class="text-center mb-6">
			<p class="text-lg font-medium text-metal-100">
				Generating... {percent}%
			</p>
			<p class="text-sm text-metal-400 mt-1">
				{completedModels.length}/{modelCount} models complete
			</p>
		</div>

		<!-- Progress Bar -->
		<div class="max-w-md mx-auto mb-8">
			<div class="h-3 bg-metal-800 rounded-full overflow-hidden border border-white/10">
				<div
					class="h-full bg-gradient-to-r from-led-orange to-led-green transition-all duration-500 ease-out"
					style="width: {percent}%"
				></div>
			</div>
		</div>

		<!-- Model Status Grid -->
		<div class="grid grid-cols-2 gap-3 max-w-sm mx-auto">
			{#each MODEL_ORDER as modelKey}
				{@const modelStatus = getModelStatus(modelKey)}
				<div
					class="flex items-center gap-2 px-3 py-2 rounded-lg transition-colors
						{modelStatus === 'complete' ? 'bg-led-green/10 border border-led-green/30' :
						 modelStatus === 'active' ? 'bg-led-orange/10 border border-led-orange/30' :
						 'bg-metal-800/50 border border-white/5'}"
				>
					{#if modelStatus === 'complete'}
						<svg class="w-5 h-5 text-led-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					{:else if modelStatus === 'active'}
						<div
							class="w-4 h-4 border-2 border-led-orange border-t-transparent rounded-full animate-spin"
						></div>
					{:else}
						<div class="w-5 h-5 rounded-full border-2 border-metal-600"></div>
					{/if}
					<span class="text-sm font-medium {modelStatus === 'complete' ? 'text-led-green' : modelStatus === 'active' ? 'text-led-orange' : 'text-metal-400'}">
						{MODEL_LABELS[modelKey]}
					</span>
				</div>
			{/each}
		</div>

		<!-- Status Message -->
		<p class="text-center text-sm text-metal-500 mt-6">
			{#if progress?.status === 'queued'}
				Waiting in queue...
			{:else if currentModel}
				Processing {MODEL_LABELS[currentModel + '_grid'] || currentModel}...
			{:else}
				Processing workflow...
			{/if}
		</p>
	{/if}
</div>
