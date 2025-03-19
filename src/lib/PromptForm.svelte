<script lang="ts">
	import { tick } from 'svelte';
	import {
		systemPrompt,
		promptError,
		promptName,
		savePromptTemplate,
		loadPromptTemplate,
		listPromptNames,
		deletePromptTemplate,
		userPromptSections,
		userPrompt,
		addDynamicPrompt,
		updateDynamicPrompt,
		deleteDynamicPrompt,
		type UserPromptSection
	} from './promptService';
	import { llmOutput, promptOutput, sttOutput } from './stores';

	let promptNames: string[] = $state(listPromptNames());
	let selectedPrompt: string = $state('Luna Thinking');

	// For adding new dynamic prompts
	let newDynamicPromptName: string = $state('');
	let newDynamicPromptContent: string = $state('');

	// For editing dynamic prompts
	let editingPromptId: string | null = $state(null);
	let editPromptName: string = $state('');
	let editPromptContent: string = $state('');

	// For prompt deletion confirmation
	let deletionConfirmationMode: boolean = $state(false);

	let forwardOutput = $state(true);

	function handleSavePrompt() {
		savePromptTemplate($promptName, $systemPrompt);
		promptNames = listPromptNames();
		selectedPrompt = $promptName;
	}

	function handleDeletePrompt() {
		if (!selectedPrompt) {
			promptError.set('No prompt selected to delete.');
			return;
		}

		if (!deletionConfirmationMode) {
			// Enter confirmation mode
			deletionConfirmationMode = true;
			return;
		}

		// If we're already in confirmation mode, proceed with deletion
		deletePromptTemplate(selectedPrompt);
		const i = promptNames.indexOf(selectedPrompt);
		promptNames.splice(i, 1);
		selectedPrompt = promptNames.length > 0 ? promptNames[i] : '';

		// Exit confirmation mode
		deletionConfirmationMode = false;
	}

	function cancelDeletion() {
		deletionConfirmationMode = false;
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

	function startEditingPrompt(section: UserPromptSection) {
		editingPromptId = section.id;
		editPromptName = section.name;
		editPromptContent = section.content;
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

	function updateConversation(sections: UserPromptSection[], newText: string): UserPromptSection[] {
		const conversationSection = sections?.find((section) => section.name === 'Conversation');
		if (conversationSection) {
			conversationSection.content += `\n${newText.trim()}`;
		}
		return sections;
	}

	$effect(() => {
		if (selectedPrompt) {
			loadPromptTemplate(selectedPrompt);
		} else if (promptNames.length > 0) {
			selectedPrompt = promptNames[0];
		}
	});

	$effect(() => {
		const unsubscribe = llmOutput.subscribe((newText) => {
			if (newText) {
				userPromptSections.update((sections) => updateConversation(sections, `Luna: ${newText}`));
			}
		});

		return () => {
			unsubscribe;
		};
	});

	$effect(() => {
		const unsubscribe = sttOutput.subscribe(async (newText) => {
			if (newText) {
				userPromptSections.update((sections) => updateConversation(sections, newText));
				if (forwardOutput) {
					await tick();
					promptOutput.set({
						systemPrompt: $systemPrompt,
						userPrompt: $userPrompt
					});
				}
			}
		});

		return () => {
			unsubscribe;
		};
	});
</script>

<div class="card">
	<div class="card-header">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="icon icon-lg icon-primary mr-2"
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
		<h2>Prompt Templates</h2>
	</div>

	<div class="card-body">
		{#if $promptError}
			<div class="alert-error">
				<p class="flex-start">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="icon icon-danger mr-2"
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

		<div class="form-group">
			<label for="saved-prompts">Saved Prompts:</label>
			<select id="saved-prompts" bind:value={selectedPrompt} class="form-control">
				<option value="">Select a saved prompt</option>
				{#each promptNames as name}
					<option value={name}>{name}</option>
				{/each}
			</select>
		</div>

		<div class="form-group">
			<label for="prompt-name">Prompt Name:</label>
			<input type="text" id="prompt-name" bind:value={$promptName} class="form-control" />
		</div>

		<!-- Main Prompt Template Section -->
		<div class="form-group rounded-md border border-gray-600 bg-gray-800 p-4">
			<h3 class="mb-4 text-lg font-medium text-gray-300">Main Prompt Template</h3>
			<textarea id="prompt-template" bind:value={$systemPrompt} rows="5" class="form-control"
			></textarea>
		</div>

		<!-- Dynamic Prompts Section -->
		<div class="form-group rounded-md border border-gray-600 bg-gray-800 p-4">
			<h3 class="mb-4 text-lg font-medium text-gray-300">Dynamic Prompts</h3>

			<!-- Add New Dynamic Prompt -->
			<div class="mb-6 rounded-md border border-gray-700 bg-gray-700 p-3">
				<div class="form-group">
					<label for="new-dynamic-name">Name:</label>
					<input
						type="text"
						id="new-dynamic-name"
						bind:value={newDynamicPromptName}
						class="form-control"
						placeholder="Enter prompt name"
					/>
				</div>

				<div class="form-group">
					<label for="new-dynamic-content">Content:</label>
					<textarea
						id="new-dynamic-content"
						bind:value={newDynamicPromptContent}
						rows="3"
						class="form-control"
						placeholder="Enter prompt content"
					></textarea>
				</div>

				<button onclick={handleAddDynamicPrompt} class="btn-success"> Add Dynamic Prompt </button>
			</div>

			<!-- List of Dynamic Prompts -->
			<div>
				{#if $userPromptSections.length === 0}
					<p class="text-gray-400">No dynamic prompts added yet.</p>
				{:else}
					{#each $userPromptSections as section}
						<div class="mb-3 rounded-md border border-gray-700 bg-gray-700 p-3">
							{#if editingPromptId === section.id}
								<!-- Edit Mode -->
								<div class="form-group">
									<label for="editPromptName">Name:</label>
									<input
										id="editPromptName"
										type="text"
										bind:value={editPromptName}
										class="form-control"
									/>
								</div>

								<div class="form-group">
									<label for="editPromptContent">Content:</label>
									<textarea
										id="editPromptContent"
										bind:value={editPromptContent}
										rows="3"
										class="form-control"
									></textarea>
								</div>

								<div class="space-x-sm">
									<button onclick={saveEditingPrompt} class="btn-primary btn-sm"> Save </button>
									<button onclick={cancelEditingPrompt} class="btn-secondary btn-sm">
										Cancel
									</button>
								</div>
							{:else}
								<!-- View Mode -->
								<div class="flex-between mb-1">
									<h5 class="text-md font-medium text-indigo-300">{section.name}</h5>
									<div class="space-x-sm">
										<button onclick={() => startEditingPrompt(section)} class="btn-info btn-sm">
											Edit
										</button>
										<button
											onclick={() => handleDeleteDynamicPrompt(section.id)}
											class="btn-danger btn-sm"
										>
											Delete
										</button>
									</div>
								</div>
								<div class="rounded-md bg-gray-800 p-2 text-gray-300">
									<pre class="whitespace-pre-wrap">{section.content}</pre>
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Combined Prompt Preview -->
		<div class="form-group rounded-md border border-gray-600 bg-gray-800 p-4">
			<h3 class="mb-2 text-lg font-medium text-gray-300">Combined Prompt Preview</h3>
			<div class="form-control whitespace-pre-wrap p-3">
				<pre>{$systemPrompt}{$userPrompt ? `${$userPrompt}` : ''}</pre>
			</div>
		</div>

		<div class="form-group">
			<label class="flex-start space-x-2">
				<input type="checkbox" bind:checked={forwardOutput} />
				<span class="text-gray-300">Forward Output</span>
			</label>
		</div>

		<div class="space-x-md">
			<button onclick={handleSavePrompt} class="btn-primary"> Save Prompt </button>

			{#if !deletionConfirmationMode}
				<button onclick={handleDeletePrompt} class="btn-danger"> Delete Prompt </button>
			{:else}
				<div class="flex-start space-x-sm">
					<span class="text-yellow-400">Confirm deletion?</span>
					<button onclick={handleDeletePrompt} class="btn-danger"> Yes, Delete </button>
					<button onclick={cancelDeletion} class="btn-secondary"> Cancel </button>
				</div>
			{/if}
		</div>
	</div>
</div>
