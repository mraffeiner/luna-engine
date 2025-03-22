/**
 * Utility functions for the control panel
 */

/**
 * Cleans text by removing thinking tags and non-alphanumeric/punctuation characters.
 *
 * @param text The text to clean.
 * @returns The cleaned text.
 */
export function cleanText(reasoning: boolean, text: string): string {
	if (!text) return text;

	let cleanedText = text;

	if (reasoning) {
		const hasThinkTags = /<think\b[^>]*>|<\/think>/gi.test(cleanedText);

		const openingTagsCount = (text.match(/<think\b[^>]*>/gi) || []).length;
		const closingTagsCount = (text.match(/<\/think>/gi) || []).length;

		if (hasThinkTags && openingTagsCount === 1 && closingTagsCount === 1) {
			cleanedText = text.replace(/<think\b[^>]*>[\s\S]*?<\/think>/gi, '').trim();
		}
	}

	// Handle special characters before processing asterisks and quotes

	// Replace double single quotes with regular quotes (will be handled by quote removal)
	cleanedText = cleanedText.replace(/''/g, '"');

	// Replace full width exclamation marks with regular ones
	cleanedText = cleanedText.replace(/\uff01/g, '!');

	// Replace double dashes and full width dashes with periods
	cleanedText = cleanedText.replace(/--/g, '. ');
	cleanedText = cleanedText.replace(/[\u2014\u2015\uFF0D]/g, '. '); // Full width period

	// Replace other special characters
	cleanedText = cleanedText.replace(/[\u007E\uFF5E\u2053\u223C]/g, '. '); // Replace various tilde-like characters
	cleanedText = cleanedText.replace(/[\u2026]/g, '...'); // Replace ellipsis character with three dots
	cleanedText = cleanedText.replace(/[\u201C\u201D\u201E\u201F\u2033\u2036]/g, '"'); // Replace fancy quotes with regular quotes
	cleanedText = cleanedText.replace(/[\u2018\u2019\u201A\u201B\u2032\u2035]/g, "'"); // Replace fancy apostrophes with regular ones

	// Remove emojis and other pictographic characters
	cleanedText = cleanedText.replace(/\p{Extended_Pictographic}/gu, '');

	// Convert *text* to "text." format
	cleanedText = cleanedText.replace(/\*(.*?)\*/g, (_, content) => {
		// Trim the content and ensure it ends with a period if it doesn't have ending punctuation
		content = content.trim();
		if (!/[.!?]$/.test(content)) {
			content += '.';
		}
		return content + ' ';
	});

	// Remove quotes around text
	cleanedText = cleanedText.replace(/"(.*?)"/g, '$1');

	// Clean up any double spaces that might have been created
	cleanedText = cleanedText.replace(/\s{2,}/g, ' ').trim();

	const hasDoubleLineBreaks = /\n\n/g.test(cleanedText);
	if (!hasDoubleLineBreaks) return cleanedText;

	const errorMessages = [
		'Sorry, uh.. I think I spaced out for a moment.',
		'Uh.. wait.. what was I about to say?',
		"Hm.. I have no idea what just happened, but I'm Pretty sure Nova ate my last thought."
	];
	return errorMessages[Math.floor(Math.random() * errorMessages.length)];
}
