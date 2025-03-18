<script lang="ts">
	import {
		promptTemplate,
		promptError,
		promptName,
		savePromptTemplate,
		loadPromptTemplate,
		listPromptNames,
		deletePromptTemplate,
		dynamicPrompts,
		combinedPrompt,
		addDynamicPrompt,
		updateDynamicPrompt,
		deleteDynamicPrompt,
		type DynamicPrompt
	} from './promptService';

	let promptNames: string[] = $state(listPromptNames());
	let selectedPrompt: string = $state('');

	// For adding new dynamic prompts
	let newDynamicPromptName: string = $state('');
	let newDynamicPromptContent: string = $state('');

	// For editing dynamic prompts
	let editingPromptId: string | null = $state(null);
	let editPromptName: string = $state('');
	let editPromptContent: string = $state('');

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

	function handleAddDynamicPrompt() {
		if (newDynamicPromptName.trim() === '') {
			promptError.set('Please enter a name for the dynamic prompt.');
			return;
		}

		addDynamicPrompt(newDynamicPromptName, newDynamicPromptContent);
		newDynamicPromptName = '';
		newDynamicPromptContent = '';
	}

	function startEditingPrompt(prompt: DynamicPrompt) {
		editingPromptId = prompt.id;
		editPromptName = prompt.name;
		editPromptContent = prompt.content;
	}

	function saveEditingPrompt() {
		if (editingPromptId) {
			updateDynamicPrompt(editingPromptId, editPromptName, editPromptContent);
			cancelEditingPrompt();
		}
	}

	function cancelEditingPrompt() {
		editingPromptId = null;
		editPromptName = '';
		editPromptContent = '';
	}

	function handleDeleteDynamicPrompt(id: string) {
		deleteDynamicPrompt(id);
		if (editingPromptId === id) {
			cancelEditingPrompt();
		}
	}

	$effect(() => {
		if (selectedPrompt) {
			loadPromptTemplate(selectedPrompt);
		} else if (promptNames.length > 0) {
			selectedPrompt = promptNames[0];
		}
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
		<label for="saved-prompts" class="mb-2 block text-sm font-medium text-gray-300"
			>Saved Prompts:</label
		>
		<select
			id="saved-prompts"
			bind:value={selectedPrompt}
			class="block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
		>
			<option value="">Select a saved prompt</option>
			{#each promptNames as name}
				<option value={name}>{name}</option>
			{/each}
		</select>
	</div>

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

	<!-- Main Prompt Template Section -->
	<div class="mb-6 rounded-md border border-gray-600 bg-gray-800 p-4">
		<h3 class="mb-4 text-lg font-medium text-gray-300">Main Prompt Template</h3>

		<div class="mb-4">
			<textarea
				id="prompt-template"
				bind:value={$promptTemplate}
				rows="5"
				class="block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
			></textarea>
		</div>
	</div>

	<!-- Dynamic Prompts Section -->
	<div class="mb-6 rounded-md border border-gray-600 bg-gray-800 p-4">
		<h3 class="mb-4 text-lg font-medium text-gray-300">Dynamic Prompts</h3>

		<!-- Add New Dynamic Prompt -->
		<div class="mb-6 rounded-md border border-gray-700 bg-gray-700 p-3">
			<div class="mb-3">
				<label for="new-dynamic-name" class="mb-1 block text-sm font-medium text-gray-300"
					>Name:</label
				>
				<input
					type="text"
					id="new-dynamic-name"
					bind:value={newDynamicPromptName}
					class="block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
					placeholder="Enter prompt name"
				/>
			</div>

			<div class="mb-3">
				<label for="new-dynamic-content" class="mb-1 block text-sm font-medium text-gray-300"
					>Content:</label
				>
				<textarea
					id="new-dynamic-content"
					bind:value={newDynamicPromptContent}
					rows="3"
					class="block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
					placeholder="Enter prompt content"
				></textarea>
			</div>

			<button
				onclick={handleAddDynamicPrompt}
				class="rounded-md bg-green-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-green-700"
				>Add Dynamic Prompt</button
			>
		</div>

		<!-- List of Dynamic Prompts -->
		<div>
			{#if $dynamicPrompts.length === 0}
				<p class="text-gray-400">No dynamic prompts added yet.</p>
			{:else}
				{#each $dynamicPrompts as prompt}
					<div class="mb-3 rounded-md border border-gray-700 bg-gray-700 p-3">
						{#if editingPromptId === prompt.id}
							<!-- Edit Mode -->
							<div class="mb-2">
								<label for="editPromptName" class="mb-1 block text-sm font-medium text-gray-300"
									>Name:</label
								>
								<input
									id="editPromptName"
									type="text"
									bind:value={editPromptName}
									class="block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
								/>
							</div>

							<div class="mb-2">
								<label for="editPromptContent" class="mb-1 block text-sm font-medium text-gray-300"
									>Content:</label
								>
								<textarea
									id="editPromptContent"
									bind:value={editPromptContent}
									rows="3"
									class="block w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-gray-200 focus:border-indigo-500 focus:ring-indigo-500"
								></textarea>
							</div>

							<div class="flex space-x-2">
								<button
									onclick={saveEditingPrompt}
									class="rounded-md bg-indigo-600 px-3 py-1 text-sm text-white transition-colors duration-200 hover:bg-indigo-700"
									>Save</button
								>
								<button
									onclick={cancelEditingPrompt}
									class="rounded-md bg-gray-600 px-3 py-1 text-sm text-white transition-colors duration-200 hover:bg-gray-700"
									>Cancel</button
								>
							</div>
						{:else}
							<!-- View Mode -->
							<div class="mb-1 flex items-center justify-between">
								<h5 class="text-md font-medium text-indigo-300">{prompt.name}</h5>
								<div class="flex space-x-2">
									<button
										onclick={() => startEditingPrompt(prompt)}
										class="rounded-md bg-blue-600 px-2 py-1 text-xs text-white transition-colors duration-200 hover:bg-blue-700"
										>Edit</button
									>
									<button
										onclick={() => handleDeleteDynamicPrompt(prompt.id)}
										class="rounded-md bg-red-600 px-2 py-1 text-xs text-white transition-colors duration-200 hover:bg-red-700"
										>Delete</button
									>
								</div>
							</div>
							<div class="rounded-md bg-gray-800 p-2 text-gray-300">
								<pre class="whitespace-pre-wrap">{prompt.content}</pre>
							</div>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</div>

	<!-- Combined Prompt Preview -->
	<div class="mb-6 rounded-md border border-gray-600 bg-gray-800 p-4">
		<h3 class="mb-2 text-lg font-medium text-gray-300">Combined Prompt Preview</h3>
		<div class="rounded-md border border-gray-600 bg-gray-700 p-3 text-white">
			<pre class="whitespace-pre-wrap">{$combinedPrompt}</pre>
		</div>
	</div>

	<div class="flex space-x-2">
		<button
			onclick={handleSavePrompt}
			class="rounded-md bg-indigo-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-indigo-700"
			>Save Prompt</button
		>
		<button
			onclick={handleDeletePrompt}
			class="rounded-md bg-red-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-red-700"
			>Delete Prompt</button
		>
	</div>
</div>
