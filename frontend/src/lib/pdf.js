import { jsPDF } from 'jspdf';

const MODEL_ORDER = [
	{ key: 'flux_grid', label: 'FLUX' },
	{ key: 'zimage_grid', label: 'Z-Image' },
	{ key: 'qwen_grid', label: 'Qwen' },
	{ key: 'wan_grid', label: 'WAN' }
];

/**
 * Export a single-page PDF with reference image, title, and 2x2 grid of model outputs.
 *
 * @param {string} triggerWord
 * @param {Record<string, Array<{filename, subfolder?, type?}>>} results - output map from API
 * @param {(img: any) => string} imageUrlFn - function to resolve image objects to URLs
 */
export async function exportValidationPDF(triggerWord, results, imageUrlFn) {
	const doc = new jsPDF({ orientation: 'landscape', format: 'a4' });
	const pw = doc.internal.pageSize.getWidth(); // ~297mm
	const ph = doc.internal.pageSize.getHeight(); // ~210mm
	const margin = 10;
	const headerHeight = 52;

	// --- Fetch all images in parallel for better performance ---
	const refImg = results?.reference_image;
	const modelImages = MODEL_ORDER.map(({ key }) => firstImage(results?.[key]));

	const [refDataUrl, ...modelDataUrls] = await Promise.all([
		refImg ? fetchImageDataUrl(imageUrlFn(refImg)) : Promise.resolve(null),
		...modelImages.map((img) => (img ? fetchImageDataUrl(imageUrlFn(img)) : Promise.resolve(null)))
	]);

	// --- Header: reference image + title ---
	let headerTextX = margin;
	if (refDataUrl) {
		const refDims = await getImageDimensions(refDataUrl);
		const refFit = fitImage(refDims.width, refDims.height, 42, 42);
		doc.addImage(refDataUrl, 'PNG', margin, 6, refFit.w, refFit.h);
		headerTextX = margin + refFit.w + 6;
	}

	doc.setFontSize(18);
	doc.text('LoRA Validation Report', headerTextX, 18);
	doc.setFontSize(10);
	doc.text(`Trigger Word: ${triggerWord}`, headerTextX, 28);
	doc.text(`Date: ${new Date().toLocaleString()}`, headerTextX, 38);

	// --- 2x2 grid of model images ---
	const gridTop = headerHeight;
	const gridWidth = pw - margin * 2;
	const gridHeight = ph - headerHeight - margin;
	const cellWidth = gridWidth / 2;
	const cellHeight = gridHeight / 2;
	const labelHeight = 10;
	const cellPadding = 3;

	for (let i = 0; i < MODEL_ORDER.length; i++) {
		const { label } = MODEL_ORDER[i];
		const dataUrl = modelDataUrls[i];
		if (!dataUrl) continue;

		const col = i % 2;
		const row = Math.floor(i / 2);
		const cellX = margin + col * cellWidth;
		const cellY = gridTop + row * cellHeight;

		// Label
		doc.setFontSize(9);
		doc.setFont(undefined, 'bold');
		doc.text(label, cellX + cellPadding, cellY + 7);
		doc.setFont(undefined, 'normal');

		// Image - maximize size within cell
		const dims = await getImageDimensions(dataUrl);
		const maxImgWidth = cellWidth - cellPadding * 2;
		const maxImgHeight = cellHeight - labelHeight - cellPadding;
		const { w, h } = fitImage(dims.width, dims.height, maxImgWidth, maxImgHeight);
		const imgX = cellX + cellPadding + (maxImgWidth - w) / 2; // center horizontally
		doc.addImage(dataUrl, 'PNG', imgX, cellY + labelHeight, w, h);
	}

	const filename = `${triggerWord.replace(/[^a-zA-Z0-9]/g, '_')}_validation.pdf`;
	doc.save(filename);
}

function firstImage(val) {
	if (!val) return null;
	return Array.isArray(val) ? val[0] || null : val;
}

async function fetchImageDataUrl(url) {
	const res = await fetch(url);
	const blob = await res.blob();
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onloadend = () => resolve(reader.result);
		reader.onerror = () => reject(new Error('Failed to read blob as data URL'));
		reader.readAsDataURL(blob);
	});
}

function getImageDimensions(dataUrl) {
	return new Promise((resolve, reject) => {
		const img = new Image();
		img.onload = () => resolve({ width: img.width, height: img.height });
		img.onerror = () => reject(new Error('Failed to load image for dimensions'));
		img.src = dataUrl;
	});
}

function fitImage(srcW, srcH, maxW, maxH) {
	const ratio = srcW / srcH;
	let w = maxW;
	let h = w / ratio;
	if (h > maxH) {
		h = maxH;
		w = h * ratio;
	}
	return { w, h };
}
