import type { TtsEngine } from '$lib/pages/services/tts/ttsService';

export function asyncSleep(ms: number) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

export function normalizeText(text: string): string {
	if (!text) return text;

	// Replace full width exclamation marks and periods with regular ones
	text = text.replace(/\uff01/g, '!');
	// Replace double single quotes with regular quotes
	text = text.replace(/''/g, '"');
	// Replace fancy quotes with regular quotes
	text = text.replace(/[\u201C\u201D\u201E\u201F\u2033\u2036]/g, '"');
	// Replace fancy apostrophes with regular ones
	text = text.replace(/[\u2018\u2019\u201A\u201B\u2032\u2035]/g, "'");

	// Remove quotation marks if remaining text is quoted
	text = text.replace(/(^"|"$)/g, '');
	// Remove emojis and other pictographic characters
	text = text.replace(/\p{Extended_Pictographic}/gu, '');
	// Clean up any doubled spaces
	text = text.replace(/\s{2,}/g, ' ');

	return text.trim();
}

export function normalizeLlmResponse(text: string, isReasoning: boolean, removePrefix: string) {
	if (!text) return text;

	if (isReasoning) {
		// Set of error messages to randomly choose from
		const errorMessages = [
			'Sorry, uh.. I think I spaced out for a moment.',
			'Uh.. wait.. what was I about to say?',
			"Hm.. I have no idea what just happened, but I'm Pretty sure Nova ate my last thought."
		];

		const hasThinkTags = /<think\b[^>]*>|<\/think>/gi.test(text);
		const openingTagsCount = (text.match(/<think\b[^>]*>/gi) || []).length;
		const closingTagsCount = (text.match(/<\/think>/gi) || []).length;

		if (hasThinkTags && openingTagsCount === 1 && closingTagsCount === 1) {
			text = text.replace(/<think\b[^>]*>[\s\S]*?<\/think>/gi, '').trim();
		} else {
			return errorMessages[Math.floor(Math.random() * errorMessages.length)];
		}
	}

	// For preventing doubled prefix on conversation logs
	if (removePrefix && text.startsWith(removePrefix)) {
		text = text.replace(removePrefix, '').trim();
	}

	return normalizeText(text);
}

export function normalizeTtsInput(text: string, ttsEngine: TtsEngine) {
	if (!text) return text;

	const pauseChar = ttsEngine === 'kokoro' ? '\u2014' : '. '; // em dash (—) : period (. )

	// Define a regex that matches all known pause indicators:
	//  • Asterisk: *
	//  • Ellipsis variants: three or more periods, Unicode ellipsis, midline ellipsis,
	//    or three or more fullwidth periods.
	//  • Dash/Tilde variants: en dash, em dash, fullwidth hyphen,
	//    ASCII tilde, modifier letter small tilde, tilde operator, fullwidth tilde.
	const pauseIndicatorsRegex = new RegExp(
		[
			'\\*', // asterisk
			'\\.{3,}', // three or more ASCII periods
			'[\u2026]', // Unicode ellipsis (…)
			'[\u22EF]', // midline horizontal ellipsis (⋯)
			'[\uFF0E]{3,}', // three or more fullwidth periods
			'[\u2013\u2014\uFF0D]', // dash variants: en dash, em dash, fullwidth hyphen
			'[\u007E\u02DC\u223C\uFF5E]' // tilde variants: ASCII tilde, modifier letter small tilde, tilde operator, fullwidth tilde
		].join('|'),
		'g'
	);

	// Add a negative lookahead and lookbehind to avoid replacing hyphens between words
	const wordHyphenRegex = /(?<!\w)-(?!\w)/g; // Matches hyphens not between words

	// Replace every occurrence of any pause indicator with the desired pause character.
	text = text.replace(pauseIndicatorsRegex, pauseChar);

	// Replace isolated hyphens (not between words) with the pause character
	text = text.replace(wordHyphenRegex, pauseChar);

	// Collapse any sequences of the pause character (possibly with whitespace between) into a single instance.
	const escapedPause = escapeRegex(pauseChar);
	const collapseRegex = new RegExp(`(?:\\s*${escapedPause}\\s*){2,}`, 'g');
	text = text.replace(collapseRegex, pauseChar);

	return text;
}

export function splitByPunctuation(text: string, minWords: number = 1): string[] {
	// Helper to count words reliably (handles multiple spaces)
	const countWords = (str: string): number => {
		// Split by any whitespace and filter out empty strings
		return str.split(/\s+/).filter(Boolean).length;
	};

	// Ensure minWords is at least 1
	const effectiveMinWords = Math.max(1, minWords);

	// Split by punctuation followed by whitespace, keeping punctuation.
	// Trim resulting parts and filter out any empty strings.
	const punctuationSplitParts = text
		.split(/(?<=[,.!?—])\s+/) // Positive lookbehind keeps punctuation
		.map((p) => p.trim())
		.filter((p) => p.length > 0);

	// If splitting resulted in nothing (e.g., empty input or just punctuation/space),
	// return based on whether the original trimmed text had content.
	if (punctuationSplitParts.length === 0) {
		const trimmedText = text.trim();
		return trimmedText.length > 0 ? [trimmedText] : [];
	}

	const finalParts: string[] = [];
	let currentChunk = '';

	for (const part of punctuationSplitParts) {
		// Determine the separator (space) needed if currentChunk isn't empty
		const separator = currentChunk ? ' ' : '';
		// Add the new part to the current chunk
		currentChunk = `${currentChunk}${separator}${part}`;

		// Check if the current chunk now meets the minimum word count
		if (countWords(currentChunk) >= effectiveMinWords) {
			finalParts.push(currentChunk);
			currentChunk = ''; // Reset for the next chunk
		}
		// If not long enough, loop continues, accumulating the next part
	}

	// After the loop, if there's anything left in currentChunk,
	// add it as the last part (it might be shorter than minWords).
	if (currentChunk) {
		finalParts.push(currentChunk);
	}

	// Edge case: If the entire text processed resulted in no final parts
	// (e.g., text was shorter than minWords and had no punctuation to force a push),
	// return the original text as a single item if it wasn't empty.
	// This is mostly covered by the `if (currentChunk)` check above,
	// but ensures non-empty short inputs return themselves.
	if (finalParts.length === 0 && text.trim().length > 0) {
		return [text.trim()];
	}

	return finalParts;
}

function escapeRegex(string: string) {
	return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
