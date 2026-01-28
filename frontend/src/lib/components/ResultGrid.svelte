<script>
	import { imageUrl } from '$lib/api.js';
	import { exportValidationPDF } from '$lib/pdf.js';

	let { results, triggerWord = '' } = $props();

	const models = [
		{ key: 'flux_grid', label: 'FLUX' },
		{ key: 'zimage_grid', label: 'Z-Image' },
		{ key: 'qwen_grid', label: 'Qwen' },
		{ key: 'wan_grid', label: 'WAN' }
	];

	let exportError = $state(null);
	let lightboxSrc = $state(null);
	let lightboxAlt = $state('');

	// Get first image from result (the composed grid)
	function getFirstImage(val) {
		if (!val) return null;
		return Array.isArray(val) ? val[0] || null : val;
	}

	function openLightbox(src, alt) {
		lightboxSrc = src;
		lightboxAlt = alt;
	}

	function closeLightbox() {
		lightboxSrc = null;
	}

	function handleKeydown(e) {
		if (e.key === 'Escape') closeLightbox();
	}

	async function handleExport() {
		try {
			exportError = null;
			await exportValidationPDF(triggerWord, results, imageUrl);
		} catch (e) {
			exportError = e.message || 'PDF export failed';
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="bg-gradient-to-b from-metal-800/80 to-metal-900/90 backdrop-blur-sm rounded-xl shadow-xl border border-white/5 brushed-metal overflow-hidden">
	<div class="flex items-center justify-between px-6 py-4 border-b border-white/5">
		<div class="flex items-center gap-4">
			{#if results?.reference_image}
				<button
					class="shrink-0 cursor-zoom-in"
					onclick={() => openLightbox(imageUrl(results.reference_image), 'Reference image')}
				>
					<img
						src={imageUrl(results.reference_image)}
						alt="Reference"
						class="w-28 h-28 rounded-lg object-cover border border-white/10"
					/>
				</button>
			{/if}
			<div>
				<h2 class="text-xl font-semibold text-metal-100">Results</h2>
				<p class="text-metal-400 text-sm mt-1">Trigger: {triggerWord}</p>
			</div>
		</div>
		<div class="flex items-center gap-3">
			{#if exportError}
				<span class="text-led-red text-sm">{exportError}</span>
			{/if}
			<button
				onclick={handleExport}
				class="bg-gradient-to-b from-led-green/80 to-led-green/90 text-white px-4 py-2 rounded-lg
					border border-led-green/50 metal-shimmer raised-metal
					hover:from-led-green hover:to-led-green/80
					transition-all duration-200"
			>
				Export to PDF
			</button>
		</div>
	</div>

	<div class="p-6">
		<!-- Per-model grids -->
		<div class="grid grid-cols-2 gap-4">
			{#each models as { key, label }}
				{@const img = getFirstImage(results?.[key])}
				{#if img}
					<button
						class="bg-metal-800/50 rounded-lg border border-white/5 p-3 cursor-zoom-in"
						onclick={() => openLightbox(imageUrl(img), label + ' grid')}
					>
						<p class="font-medium text-metal-200 mb-2 text-sm uppercase tracking-wide">{label}</p>
						<img src={imageUrl(img)} alt="{label} grid" class="rounded w-full" />
					</button>
				{/if}
			{/each}
		</div>
	</div>
</div>

<!-- Lightbox -->
{#if lightboxSrc}
	<button
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm cursor-zoom-out"
		onclick={closeLightbox}
	>
		<img
			src={lightboxSrc}
			alt={lightboxAlt}
			class="max-w-[95vw] max-h-[95vh] object-contain rounded-lg shadow-2xl"
		/>
	</button>
{/if}
