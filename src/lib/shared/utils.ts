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

/**
 * Splits a string into sentences based on punctuation (. ! ? —), ensuring each resulting sentence
 * has at least a minimum number of words. Shorter sentences are merged with the preceding one.
 *
 * @param text The input text to split.
 * @param minWords The minimum number of words required for a sentence part. Defaults to 1.
 * @returns An array of strings, where each string is a sentence meeting the minimum word count,
 *          or the original text trimmed if it couldn't be split meaningfully.
 */
export function splitByPunctuation(text: string, minWords: number = 1): string[] {
	const trimmedText = text.trim();
	if (!trimmedText) {
		return [];
	}

	// Helper to count words reliably (handles multiple spaces)
	const countWords = (str: string): number => str.split(/\s+/).filter(Boolean).length;

	// Ensure minWords is at least 1
	const effectiveMinWords = Math.max(1, minWords);

	// Split by sentence-ending punctuation followed by whitespace, keeping punctuation.
	const initialParts = trimmedText
		.split(/(?<=[.!?—])\s+/) // Positive lookbehind keeps punctuation
		.filter((p) => p.length > 0); // Filter out empty strings

	// If no meaningful split occurred, return the original trimmed text
	if (initialParts.length <= 1) {
		// Check if the single part meets the word count, otherwise return original if it had words
		if (initialParts.length === 1 && countWords(initialParts[0]) >= effectiveMinWords) {
			return initialParts;
		}
		// If the original text had words but didn't meet minWords after split (or wasn't split)
		if (countWords(trimmedText) > 0) {
			return [trimmedText];
		}
		// If original text was effectively empty or just punctuation/space
		return [];
	}

	const finalParts: string[] = [];
	let currentChunk = '';

	for (const part of initialParts) {
		// Append the next part to the current chunk
		const potentialChunk = currentChunk ? `${currentChunk} ${part}` : part;

		// If the chunk is now long enough, or if it's the *very first* part
		// and already long enough, add it to finalParts.
		if (countWords(potentialChunk) >= effectiveMinWords) {
			finalParts.push(potentialChunk);
			currentChunk = ''; // Reset for the next potential chunk
		} else {
			// Otherwise, keep accumulating
			currentChunk = potentialChunk;
		}
	}

	// If there's a leftover chunk (the last part(s) were too short)
	if (currentChunk) {
		if (finalParts.length > 0) {
			// Append the short remainder to the last valid part
			finalParts[finalParts.length - 1] += ` ${currentChunk}`;
		} else {
			// If *no* parts met the minWords requirement, return the whole text as one part
			// This covers the case where the entire input text is non-empty but shorter than minWords.
			return [trimmedText];
		}
	}

	// Final check: If somehow finalParts ended up empty despite non-empty input, return original.
	// This is a safeguard, potentially redundant with the logic above, but ensures non-empty input yields non-empty output.
	if (finalParts.length === 0 && countWords(trimmedText) > 0) {
		return [trimmedText];
	}

	return finalParts;
}

function escapeRegex(string: string) {
	return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
