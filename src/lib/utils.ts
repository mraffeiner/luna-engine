/**
 * Utility functions for the control panel
 */

/**
 * Validates and removes think section
 * Only removes think section if tags are properly formatted (one opening and one closing tag)
 * If there are no think tags or they are improperly formatted, returns an error message
 *
 * @param text The text to process
 * @returns The text with think tags removed if properly formatted,
 *          or an error message if no think tags or improperly formatted
 */
export function removeThinkSection(text: string): string {
	if (!text) return text;

	// Check if there are any think tags
	const hasThinkTags = /<think\b[^>]*>|<\/think>/gi.test(text);

	// Count opening and closing think tags
	const openingTagsCount = (text.match(/<think\b[^>]*>/gi) || []).length;
	const closingTagsCount = (text.match(/<\/think>/gi) || []).length;

	// Only process if there's exactly one opening and one closing tag
	if (hasThinkTags && openingTagsCount === 1 && closingTagsCount === 1) {
		// Remove the entire think section including the tags
		return text.replace(/<think\b[^>]*>[\s\S]*?<\/think>/gi, '').trim();
	}

	// Return error message if no think tags or tags are improperly formatted
	return 'Sorry, I spaced out for a moment.';
}
