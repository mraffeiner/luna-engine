export function asyncSleep(ms: number) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

function escapeRegex(str: string): string {
	return str.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
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

export function normalizeTtsInput(text: string, pauseChar: string = '—') {
	if (!text) return text;

	// Define a regex that matches all known pause indicators:
	//  • Asterisk: *
	//  • Ellipsis variants: three or more periods, Unicode ellipsis, midline ellipsis,
	//    or three or more fullwidth periods.
	//  • Dash/Tilde variants: ASCII hyphen, en dash, em dash, fullwidth hyphen,
	//    ASCII tilde, modifier letter small tilde, tilde operator, fullwidth tilde.
	const pauseIndicatorsRegex = new RegExp(
		[
			'\\*', // asterisk
			'\\.{3,}', // three or more ASCII periods
			'[\u2026]', // Unicode ellipsis (…)
			'[\u22EF]', // midline horizontal ellipsis (⋯)
			'[\uFF0E]{3,}', // three or more fullwidth periods
			'[\u002D\u2013\u2014\uFF0D]', // hyphen variants: ASCII hyphen, en dash, em dash, fullwidth hyphen
			'[\u007E\u02DC\u223C\uFF5E]' // tilde variants: ASCII tilde, modifier letter small tilde, tilde operator, fullwidth tilde
		].join('|'),
		'g'
	);

	// Replace every occurrence of any pause indicator with the desired pause character.
	text = text.replace(pauseIndicatorsRegex, pauseChar);

	// Collapse any sequences of the pause character (possibly with whitespace between) into a single instance.
	const escapedPause = escapeRegex(pauseChar);
	const collapseRegex = new RegExp(`(?:\\s*${escapedPause}\\s*){2,}`, 'g');
	text = text.replace(collapseRegex, pauseChar);

	return text;
}
