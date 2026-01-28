const BASE = import.meta.env.VITE_API_URL || '';

export async function fetchLoras() {
	const res = await fetch(`${BASE}/api/loras`);
	if (!res.ok) throw new Error('Failed to fetch LoRAs');
	return res.json();
}

export async function fetchPrompts() {
	const res = await fetch(`${BASE}/api/prompts`);
	if (!res.ok) throw new Error('Failed to fetch prompts');
	return res.json();
}

export async function generate(triggerWord, loras, prompts, modelsEnabled, referenceImage = null) {
	const res = await fetch(`${BASE}/api/generate`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			trigger_word: triggerWord,
			loras,
			prompts,
			models_enabled: modelsEnabled,
			reference_image: referenceImage
		})
	});
	if (!res.ok) throw new Error('Failed to start generation');
	return res.json();
}

export async function pollStatus(promptId) {
	const res = await fetch(`${BASE}/api/status/${promptId}`);
	if (!res.ok) throw new Error('Failed to fetch status');
	return res.json();
}

export function imageUrl(img) {
	if (typeof img === 'string') {
		return `${BASE}/api/image/${encodeURIComponent(img)}`;
	}
	const params = new URLSearchParams();
	if (img.subfolder) params.set('subfolder', img.subfolder);
	if (img.type) params.set('type', img.type);
	const qs = params.toString();
	return `${BASE}/api/image/${encodeURIComponent(img.filename)}${qs ? '?' + qs : ''}`;
}

export async function uploadImage(file) {
	const form = new FormData();
	form.append('file', file);
	const res = await fetch(`${BASE}/api/upload-image`, { method: 'POST', body: form });
	if (!res.ok) throw new Error('Failed to upload image');
	return res.json();
}
