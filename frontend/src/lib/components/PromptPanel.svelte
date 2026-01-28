<script>
	let { prompts = $bindable([]), activeCount = $bindable(9) } = $props();
</script>

<div class="bg-gradient-to-b from-metal-800/80 to-metal-900/90 backdrop-blur-sm rounded-xl shadow-xl border border-white/5 brushed-metal overflow-hidden mb-8">
	<!-- Header with Slider -->
	<div class="px-6 py-4 border-b border-white/5">
		<div class="flex items-center justify-between mb-3">
			<h2 class="text-lg font-semibold text-metal-100">Prompts</h2>
			<span class="text-xs font-medium px-2 py-0.5 rounded-full {activeCount > 0 ? 'bg-led-green/20 text-led-green' : 'bg-metal-700 text-metal-400'}">
				{activeCount} / {prompts.length} active
			</span>
		</div>
		<div class="flex items-center gap-4">
			<input
				type="range"
				min="0"
				max={prompts.length}
				bind:value={activeCount}
				class="flex-1 h-1.5 rounded-full appearance-none cursor-pointer
					bg-metal-700 accent-led-green
					[&::-webkit-slider-thumb]:appearance-none
					[&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
					[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-led-green
					[&::-webkit-slider-thumb]:shadow-[0_0_8px_rgba(34,197,94,0.6)]
					[&::-webkit-slider-thumb]:cursor-pointer
					[&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4
					[&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-led-green
					[&::-moz-range-thumb]:border-0
					[&::-moz-range-thumb]:shadow-[0_0_8px_rgba(34,197,94,0.6)]
					[&::-moz-range-thumb]:cursor-pointer"
			/>
			<span class="text-metal-100 font-mono text-sm w-6 text-center">{activeCount}</span>
		</div>
	</div>

	<!-- Prompt List — only show up to activeCount -->
	{#if activeCount > 0}
		<div class="p-4 space-y-3 max-h-[32rem] overflow-y-auto">
			{#each prompts.slice(0, activeCount) as prompt, i}
				<div class="flex gap-3 items-start">
					<!-- LED dot -->
					<div class="mt-3 flex-shrink-0">
						<div class="w-2 h-2 rounded-full bg-led-green led-glow text-led-green"></div>
					</div>

					<!-- Prompt Text -->
					<div class="flex-1 min-w-0">
						<span class="text-xs text-metal-500 font-medium uppercase tracking-wide">
							Prompt {i + 1}
						</span>
						<textarea
							bind:value={prompt.text}
							rows="2"
							class="mt-1 w-full bg-metal-900 border border-white/5 rounded-lg px-3 py-2 text-sm
								text-metal-100 placeholder-metal-500 recessed focus-metal
								resize-none transition-all duration-200"
							placeholder="Enter prompt text..."
						></textarea>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="p-6 text-center text-metal-500 text-sm">
			Slide to add prompts
		</div>
	{/if}
</div>
