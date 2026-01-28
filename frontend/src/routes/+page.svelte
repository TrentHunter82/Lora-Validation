<script>
	import { onMount, onDestroy } from 'svelte';
	import { fetchLoras, fetchPrompts, generate, pollStatus, uploadImage, imageUrl } from '$lib/api.js';
	import LoraSelector from '$lib/components/LoraSelector.svelte';
	import GenerateButton from '$lib/components/GenerateButton.svelte';
	import StatusIndicator from '$lib/components/StatusIndicator.svelte';
	import ResultGrid from '$lib/components/ResultGrid.svelte';
	import PromptPanel from '$lib/components/PromptPanel.svelte';

	let triggerWord = $state('');
	let loras = $state({ flux: '', zimage: '', qwen: '', wan: '' });
	let lorasEnabled = $state({ flux: true, zimage: true, qwen: true, wan: true });
	let availableLoras = $state({ flux: [], zimage: [], qwen: [], wan: [] });
	let prompts = $state([]);
	let activeCount = $state(9);
	let loading = $state(false);
	let results = $state(null);
	let error = $state(null);
	let connected = $state(false);
	let referenceImage = $state(null); // {name, previewUrl}
	let uploadingImage = $state(false);

	onMount(async () => {
		try {
			const [loraData, promptData] = await Promise.all([
				fetchLoras(),
				fetchPrompts()
			]);
			availableLoras = loraData;
			prompts = promptData;
			activeCount = promptData.length;
			connected = true;
		} catch (e) {
			error = 'Could not connect to backend. Is it running?';
			connected = false;
		}
	});

	let activeModels = $derived(Object.values(lorasEnabled).filter(Boolean).length);

	const POLL_INTERVAL_MS = 2000;
	const MAX_POLL_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes
	const MAX_POLL_ATTEMPTS = MAX_POLL_TIMEOUT_MS / POLL_INTERVAL_MS;
	let pollTimeoutId = null;
	let currentDelay = POLL_INTERVAL_MS;

	function clearPolling() {
		if (pollTimeoutId) {
			clearTimeout(pollTimeoutId);
			pollTimeoutId = null;
		}
		currentDelay = POLL_INTERVAL_MS;
	}

	onDestroy(clearPolling);

	function handleCancel() {
		clearPolling();
		loading = false;
		error = null;
	}

	async function handleImageSelect(event) {
		const file = event.target.files?.[0];
		if (!file) return;

		uploadingImage = true;
		error = null;

		try {
			const result = await uploadImage(file);
			referenceImage = {
				name: result.name,
				previewUrl: URL.createObjectURL(file)
			};
		} catch (e) {
			error = 'Failed to upload reference image';
		} finally {
			uploadingImage = false;
		}
	}

	function clearReferenceImage() {
		if (referenceImage?.previewUrl) {
			URL.revokeObjectURL(referenceImage.previewUrl);
		}
		referenceImage = null;
	}

	async function handleGenerate() {
		if (activeCount === 0) {
			error = 'Enable at least one prompt to run validation.';
			return;
		}
		if (activeModels === 0) {
			error = 'Enable at least one model to run validation.';
			return;
		}

		clearPolling();
		loading = true;
		results = null;
		error = null;

		const payload = prompts.map((p, i) => ({
			text: p.text,
			enabled: i < activeCount
		}));

		try {
			const { prompt_id } = await generate(triggerWord, loras, payload, lorasEnabled, referenceImage?.name);

			let attempts = 0;
			currentDelay = POLL_INTERVAL_MS;

			function schedulePoll() {
				pollTimeoutId = setTimeout(async () => {
					attempts++;
					if (attempts > MAX_POLL_ATTEMPTS) {
						clearPolling();
						error = 'Generation timed out. Check ComfyUI status.';
						loading = false;
						return;
					}
					try {
						const status = await pollStatus(prompt_id);
						if (status.done) {
							clearPolling();
							results = status.outputs;
							loading = false;
						} else {
							// Exponential backoff: 2s → 4s → 8s → ... → 30s max
							currentDelay = Math.min(currentDelay * 1.5, 30000);
							schedulePoll();
						}
					} catch (e) {
						clearPolling();
						error = 'Error checking generation status';
						loading = false;
					}
				}, currentDelay);
			}

			schedulePoll();
		} catch (e) {
			error = e.message || 'Failed to start generation';
			loading = false;
		}
	}
</script>

<div class="max-w-6xl mx-auto px-8">
	<h1 class="text-3xl font-bold mb-8 text-metal-100 tracking-tight">LoRA Validation Tool</h1>

	<!-- Configuration Panel -->
	<div class="bg-gradient-to-b from-metal-800/80 to-metal-900/90 backdrop-blur-sm rounded-xl shadow-xl border border-white/5 brushed-metal overflow-hidden mb-8">
		<div class="px-6 py-4 border-b border-white/5">
			<div class="flex items-center justify-between">
				<h2 class="text-lg font-semibold text-metal-100">Configuration</h2>
				<div class="flex items-center gap-2">
					<div class="w-2 h-2 rounded-full led-glow {connected ? 'bg-led-green text-led-green' : 'bg-led-red text-led-red'}"></div>
					<span class="text-xs text-metal-400">{connected ? 'ComfyUI Connected' : 'Disconnected'}</span>
				</div>
			</div>
		</div>

		<div class="p-6">
			<div class="grid grid-cols-2 gap-6">
				<label class="block">
					<span class="block text-sm font-medium text-metal-300 mb-1">Trigger Word</span>
					<input
						type="text"
						bind:value={triggerWord}
						placeholder="e.g. Queen Corgi"
						class="w-full bg-metal-900 border border-white/5 rounded-lg px-4 py-2 text-metal-100 placeholder-metal-500 recessed focus-metal"
					/>
				</label>

				<div class="block">
					<span class="block text-sm font-medium text-metal-300 mb-1">Reference Image</span>
					<div class="flex items-center gap-3">
						{#if referenceImage}
							<div class="relative">
								<img
									src={referenceImage.previewUrl}
									alt="Reference"
									class="w-12 h-12 rounded-lg object-cover border border-white/10"
								/>
								<button
									onclick={clearReferenceImage}
									class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-metal-700 border border-white/10 text-metal-300 hover:text-white hover:bg-led-red/50 flex items-center justify-center text-xs"
									title="Remove image"
								>
									×
								</button>
							</div>
							<span class="text-sm text-metal-400 truncate max-w-[150px]">{referenceImage.name}</span>
						{:else}
							<label class="cursor-pointer">
								<input
									type="file"
									accept="image/*"
									onchange={handleImageSelect}
									class="hidden"
									disabled={uploadingImage}
								/>
								<span class="inline-flex items-center gap-2 px-3 py-2 bg-metal-900 border border-white/5 rounded-lg text-sm text-metal-300 hover:border-white/10 hover:text-metal-100 transition-colors recessed">
									{#if uploadingImage}
										<span class="w-4 h-4 border-2 border-metal-500 border-t-metal-200 rounded-full animate-spin"></span>
										Uploading...
									{:else}
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
										</svg>
										Choose Image
									{/if}
								</span>
							</label>
						{/if}
					</div>
				</div>

				<LoraSelector label="FLUX LoRA" options={availableLoras.flux} bind:value={loras.flux} bind:enabled={lorasEnabled.flux} />
				<LoraSelector label="Z-Image LoRA" options={availableLoras.zimage} bind:value={loras.zimage} bind:enabled={lorasEnabled.zimage} />
				<LoraSelector label="Qwen LoRA" options={availableLoras.qwen} bind:value={loras.qwen} bind:enabled={lorasEnabled.qwen} />
				<LoraSelector label="WAN LoRA" options={availableLoras.wan} bind:value={loras.wan} bind:enabled={lorasEnabled.wan} />
			</div>
		</div>
	</div>

	<!-- Prompt Panel -->
	{#if prompts.length > 0}
		<PromptPanel bind:prompts bind:activeCount />
	{/if}

	<!-- Generate -->
	<div class="mb-8 flex gap-3">
		<GenerateButton
			{loading}
			disabled={!triggerWord || activeCount === 0 || activeModels === 0}
			onclick={handleGenerate}
			label={loading ? 'Generating...' : `Run Validation (${activeCount} prompt${activeCount !== 1 ? 's' : ''}, ${activeModels} model${activeModels !== 1 ? 's' : ''})`}
			title={!triggerWord ? 'Enter a trigger word to start' : activeCount === 0 ? 'Enable at least one prompt' : activeModels === 0 ? 'Enable at least one model' : ''}
		/>
		{#if loading}
			<button
				onclick={handleCancel}
				class="px-4 py-2 rounded-lg border border-led-red/50 text-led-red hover:bg-led-red/10 transition-colors"
			>
				Cancel
			</button>
		{/if}
	</div>

	<!-- Error -->
	{#if error}
		<div class="bg-metal-900 border border-led-red/50 text-led-red rounded-lg p-4 mb-8 recessed">
			<div class="flex items-center gap-2">
				<div class="w-2 h-2 rounded-full bg-led-red led-glow text-led-red flex-shrink-0"></div>
				<span>{error}</span>
			</div>
		</div>
	{/if}

	<!-- Loading -->
	{#if loading}
		<StatusIndicator status="running" modelCount={activeModels} />
	{/if}

	<!-- Results -->
	{#if results}
		<ResultGrid {results} {triggerWord} />
	{/if}
</div>
