import { jsPDF } from 'jspdf';

const MODEL_ORDER = [
	{ key: 'flux_grid', label: 'FLUX' },
	{ key: 'zimage_grid', label: 'Z-Image' },
	{ key: 'qwen_grid', label: 'Qwen' },
	{ key: 'wan_grid', label: 'WAN' }
];

/**
 * Export single-page portrait PDF with all models stacked vertically.
 */
export async function exportValidationPDF(triggerWord, results, imageUrlFn) {
	const doc = new jsPDF({ orientation: 'portrait', format: 'a4' });
	const pw = doc.internal.pageSize.getWidth(); // 210mm
	const ph = doc.internal.pageSize.getHeight(); // 297mm
	const margin = 8;

	// --- Fetch all images in parallel ---
	const refImg = results?.reference_image;
	const modelImages = MODEL_ORDER.map(({ key }) => firstImage(results?.[key]));

	const [refDataUrl, ...modelDataUrls] = await Promise.all([
		refImg ? fetchImageDataUrl(imageUrlFn(refImg)) : Promise.resolve(null),
		...modelImages.map((img) => (img ? fetchImageDataUrl(imageUrlFn(img)) : Promise.resolve(null)))
	]);

	// --- Header ---
	doc.setFontSize(14);
	doc.setFont(undefined, 'bold');
	doc.text('LoRA Validation Report', margin, 12);
	doc.setFont(undefined, 'normal');
	doc.setFontSize(9);
	doc.text(`Trigger: ${triggerWord}  |  ${new Date().toLocaleDateString()}`, margin, 20);

	// Reference image in top-right
	if (refDataUrl) {
		const refDims = await getImageDimensions(refDataUrl);
		const refFit = fitImage(refDims.width, refDims.height, 25, 22);
		doc.addImage(refDataUrl, 'PNG', pw - margin - refFit.w, 4, refFit.w, refFit.h);
	}

	// --- 4 rows layout (stacked vertically) ---
	const headerHeight = 28;
	const availableHeight = ph - headerHeight - margin;
	const availableWidth = pw - margin * 2;
	const rowHeight = availableHeight / 4;
	const labelWidth = 22;
	const rowPadding = 2;

	for (let i = 0; i < MODEL_ORDER.length; i++) {
		const { label } = MODEL_ORDER[i];
		const dataUrl = modelDataUrls[i];

		const rowY = headerHeight + i * rowHeight;

		// Label on left
		doc.setFontSize(9);
		doc.setFont(undefined, 'bold');
		doc.text(label, margin, rowY + rowHeight / 2 + 3);
		doc.setFont(undefined, 'normal');

		if (!dataUrl) {
			doc.setFontSize(8);
			doc.setTextColor(150);
			doc.text('No output', margin + labelWidth, rowY + rowHeight / 2 + 3);
			doc.setTextColor(0);
			continue;
		}

		// Image - fill the row
		const dims = await getImageDimensions(dataUrl);
		const maxImgWidth = availableWidth - labelWidth - rowPadding;
		const maxImgHeight = rowHeight - rowPadding * 2;
		const { w, h } = fitImage(dims.width, dims.height, maxImgWidth, maxImgHeight);

		const imgX = margin + labelWidth + (maxImgWidth - w) / 2;
		const imgY = rowY + (rowHeight - h) / 2;

		doc.addImage(dataUrl, 'PNG', imgX, imgY, w, h);
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
