/**
 * Utility functions for the control panel
 */

export function asyncSleep(ms: number) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Cleans text by removing thinking tags and non-alphanumeric/punctuation characters.
 *
 * @param text The text to clean.
 * @returns The cleaned text.
 */
export function cleanText(reasoning: boolean, text: string): string {
	if (!text) return text;

	let cleanedText = text;

	const errorMessages = [
		'Sorry, uh.. I think I spaced out for a moment.',
		'Uh.. wait.. what was I about to say?',
		"Hm.. I have no idea what just happened, but I'm Pretty sure Nova ate my last thought."
	];

	if (reasoning) {
		const hasThinkTags = /<think\b[^>]*>|<\/think>/gi.test(cleanedText);

		const openingTagsCount = (text.match(/<think\b[^>]*>/gi) || []).length;
		const closingTagsCount = (text.match(/<\/think>/gi) || []).length;

		if (hasThinkTags && openingTagsCount === 1 && closingTagsCount === 1) {
			cleanedText = text.replace(/<think\b[^>]*>[\s\S]*?<\/think>/gi, '').trim();
		} else {
			return errorMessages[Math.floor(Math.random() * errorMessages.length)];
		}
	}

	// Replace double single quotes with regular quotes (will be handled by quote removal)
	cleanedText = cleanedText.replace(/''/g, '"');

	// Replace full width exclamation marks and periods with regular ones
	cleanedText = cleanedText.replace(/\uff01/g, '!');
	cleanedText = cleanedText.replace(/[\u2014\u2015\uFF0D]/g, '. ');
	// Replace various tilde-like characters
	cleanedText = cleanedText.replace(/[\u007E\uFF5E\u2053\u223C]/g, '..');
	// Replace fancy quotes with regular quotes
	cleanedText = cleanedText.replace(/[\u201C\u201D\u201E\u201F\u2033\u2036]/g, '"');
	// Replace fancy apostrophes with regular ones
	cleanedText = cleanedText.replace(/[\u2018\u2019\u201A\u201B\u2032\u2035]/g, "'");

	// Replace enclosed asterisks with quotation marks
	cleanedText = cleanedText.replace(/\*\*(.*?)\*\*/g, '"$1"');
	// Remove remaining asterisks
	cleanedText = cleanedText.replace(/\*/g, '');

	// Remove Luna: prefix
	cleanedText = cleanedText.replace(/^Luna: /, '');

	// Remove quotation marks if remaining text is quoted
	cleanedText = cleanedText.replace(/(^"|"$)/g, '');

	// Remove emojis and other pictographic characters
	cleanedText = cleanedText.replace(/\p{Extended_Pictographic}/gu, '');

	// Clean up any double spaces that might have been created
	cleanedText = cleanedText.replace(/\s{2,}/g, ' ');

	return cleanedText.trim();
}
