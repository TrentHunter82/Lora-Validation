<script>
	import '../app.css';

	let { children } = $props();
</script>

<div class="bg-metal-950 noise-texture min-h-screen py-8">
	{@render children()}
</div>
