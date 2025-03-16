<script lang="ts">
	import {
		promptTemplate,
		promptError,
		promptName,
		savePromptTemplate,
		loadPromptTemplate,
		listPromptNames,
		deletePromptTemplate,
		dynamicPrompt,
		fetchDynamicPrompt
	} from './promptService';

	let promptNames: string[] = $state(listPromptNames());
	let selectedPrompt: string = $state('');

	function handleSavePrompt() {
		savePromptTemplate($promptName, $promptTemplate);
		promptNames = listPromptNames();
		selectedPrompt = $promptName;
	}

	function handleDeletePrompt() {
		if (selectedPrompt) {
			deletePromptTemplate(selectedPrompt);
			const i = promptNames.indexOf(selectedPrompt);
			promptNames.splice(i, 1);
			selectedPrompt = promptNames.length > 0 ? promptNames[i] : '';
		} else {
			promptError.set('No prompt selected to delete.');
		}
	}

	$effect(() => {
		if (selectedPrompt) {
			loadPromptTemplate(selectedPrompt);
		} else if (promptNames.length > 0) {
			selectedPrompt = promptNames[0];
		}
	});

	$effect(() => {
		fetchDynamicPrompt();
	});
</script>

<div class="card p-6">
	<h2 class="mb-6 flex items-center">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="mr-2 h-6 w-6 text-indigo-400"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M16 4v12l-4-2-4 2V4M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
			/>
		</svg>
		Prompt Templates
	</h2>

	{#if $promptError}
		<div class="mb-6 rounded-md border border-red-800 bg-red-900 bg-opacity-30 p-3">
			<p class="flex items-center text-red-400">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="mr-2 h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
					/>
				</svg>
				{$promptError}
			</p>
		</div>
	{/if}

	<div class="mb-4">
		<label for="prompt-name" class="mb-2 block text-sm font-medium text-gray-300"
			>Prompt Name:</label
		>
		<input
			type="text"
			id="prompt-name"
			bind:value={$promptName}
			class="block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
		/>
	</div>

	<div class="mb-4">
		<label for="prompt-template" class="mb-2 block text-sm font-medium text-gray-300"
			>Prompt Template:</label
		>
		<textarea
			id="prompt-template"
			bind:value={$promptTemplate}
			class="block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
		></textarea>
	</div>

	<div class="mb-6">
		<button
			onclick={handleSavePrompt}
			class="rounded-md bg-indigo-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-indigo-700"
			>Save</button
		>
		<button
			onclick={handleDeletePrompt}
			class="ml-2 rounded-md bg-red-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-red-700"
			>Delete</button
		>
	</div>

	<h2 class="mb-2 text-lg font-medium text-gray-300">Saved Prompts</h2>
	<select
		bind:value={selectedPrompt}
		class="mb-4 rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
	>
		{#each promptNames as name}
			<option value={name}>{name}</option>
		{/each}
	</select>

	<h2 class="mb-2 text-lg font-medium text-gray-300">Dynamic Prompt</h2>
	<div class="mb-4 rounded-md border border-gray-600 bg-gray-700 p-2 text-white">
		{$dynamicPrompt}
	</div>
</div>
