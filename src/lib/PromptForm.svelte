<script lang="ts">
	import { tick } from 'svelte';
	import {
		systemPrompt,
		promptError,
		templateName,
		saveTemplate,
		loadTemplate,
		listTemplateNames,
		deleteTemplate,
		userPromptSections,
		userPrompt,
		addUserPromptSection,
		updateUserPromptSection,
		deleteUserPromptSection,
		type UserPromptSection
	} from './promptService';
	import { llmOutput, promptOutput, sttOutput } from './stores';
	import Icon from './Icon.svelte';
	import { removeThinkSection } from './utils';

	let templateNames: string[] = $state(listTemplateNames());
	let selectedTemplate: string = $state('Luna Thinking');

	// For adding new user prompts
	let newUserPromptName: string = $state('');
	let newUserPromptContent: string = $state('');

	// For editing user prompts
	let editingPromptId: string | null = $state(null);
	let editPromptName: string = $state('');
	let editPromptContent: string = $state('');

	// For prompt deletion confirmation
	let deletionConfirmationMode: boolean = $state(false);

	let forwardOutput = $state(true);

	function handleSaveTemplate() {
		saveTemplate($templateName, $systemPrompt);
		templateNames = listTemplateNames();
		selectedTemplate = $templateName;
	}

	function handleDeleteTemplate() {
		if (!selectedTemplate) {
			promptError.set('No prompt selected to delete.');
			return;
		}

		if (!deletionConfirmationMode) {
			// Enter confirmation mode
			deletionConfirmationMode = true;
			return;
		}

		// If we're already in confirmation mode, proceed with deletion
		deleteTemplate(selectedTemplate);
		const i = templateNames.indexOf(selectedTemplate);
		templateNames.splice(i, 1);
		selectedTemplate = templateNames.length > 0 ? templateNames[i] : '';

		// Exit confirmation mode
		deletionConfirmationMode = false;
	}

	function cancelDeletion() {
		deletionConfirmationMode = false;
	}

	function handleAddUserPrompt() {
		if (newUserPromptName.trim() === '') {
			promptError.set('Please enter a name for the dynamic prompt.');
			return;
		}

		addUserPromptSection(newUserPromptName, newUserPromptContent);
		newUserPromptName = '';
		newUserPromptContent = '';
	}

	function startEditingPrompt(section: UserPromptSection) {
		editingPromptId = section.id;
		editPromptName = section.name;
		editPromptContent = section.content;
	}

	function saveEditingPrompt() {
		if (editingPromptId) {
			updateUserPromptSection(editingPromptId, editPromptName, editPromptContent);
			cancelEditingPrompt();
		}
	}

	function cancelEditingPrompt() {
		editingPromptId = null;
		editPromptName = '';
		editPromptContent = '';
	}

	function handleDeleteDynamicPrompt(id: string) {
		deleteUserPromptSection(id);
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
		if (selectedTemplate) {
			loadTemplate(selectedTemplate);
		} else if (templateNames.length > 0) {
			selectedTemplate = templateNames[0];
		}
	});

	$effect(() => {
		const unsubscribe = llmOutput.subscribe((newText) => {
			if (newText) {
				const processedText = removeThinkSection(newText);

				userPromptSections.update((sections) =>
					updateConversation(sections, `Luna: ${processedText}`)
				);
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
		<h2>
			<Icon
				path="M16 4v12l-4-2-4 2V4M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
				class="luna-text-primary-light icon-lg mr-2"
			/>
			Prompt Templates
		</h2>
	</div>

	<div class="card-body">
		{#if $promptError}
			<div class="alert-error">
				<p class="flex-start">
					<Icon
						path="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
						class="luna-text-danger mr-2"
					/>
					{$promptError}
				</p>
			</div>
		{/if}

		<div class="form-group">
			<label for="savedTemplates">Saved Templates:</label>
			<select id="savedTemplates" bind:value={selectedTemplate} class="form-control">
				<option value="">Select a saved prompt</option>
				{#each templateNames as name}
					<option value={name}>{name}</option>
				{/each}
			</select>
		</div>

		<div class="form-group">
			<label for="templateName">Template Name:</label>
			<input type="text" id="templateName" bind:value={$templateName} class="form-control" />
		</div>

		<!-- Main Prompt Template Section -->
		<div class="form-group luna-border-subtle luna-bg-surface rounded-md border p-4">
			<h3 class="luna-text-muted mb-4 text-lg font-medium">Main Prompt Template</h3>
			<textarea id="prompt-template" bind:value={$systemPrompt} rows="5" class="form-control"
			></textarea>
		</div>

		<!-- Dynamic Prompts Section -->
		<div class="form-group luna-border-subtle luna-bg-surface rounded-md border p-4">
			<h3 class="luna-text-muted mb-4 text-lg font-medium">Dynamic Prompts</h3>

			<!-- Add New Dynamic Prompt -->
			<div class="luna-border-base luna-bg-elevated mb-6 rounded-md border p-3">
				<div class="form-group">
					<label for="newDynamicName">Name:</label>
					<input
						type="text"
						id="newDynamicName"
						bind:value={newUserPromptName}
						class="form-control"
						placeholder="Enter prompt name"
					/>
				</div>

				<div class="form-group">
					<label for="newDynamicContent">Content:</label>
					<textarea
						id="newDynamicContent"
						bind:value={newUserPromptContent}
						rows="3"
						class="form-control"
						placeholder="Enter prompt content"
					></textarea>
				</div>

				<button onclick={handleAddUserPrompt} class="btn-success"> Add Dynamic Prompt </button>
			</div>

			<!-- List of Dynamic Prompts -->
			<div>
				{#if $userPromptSections.length === 0}
					<p class="luna-text-disabled">No dynamic prompts added yet.</p>
				{:else}
					{#each $userPromptSections as section}
						<div class="luna-border-base luna-bg-elevated mb-3 rounded-md border p-3">
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
									<h5 class="text-md luna-text-primary-light font-medium">{section.name}</h5>
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
								<div class="luna-bg-surface luna-text-muted whitespace-pre-wrap rounded-md p-2">
									{section.content}
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Combined Prompt Preview -->
		<div class="form-group luna-border-subtle luna-bg-surface rounded-md border p-4">
			<h3 class="luna-text-muted mb-2 text-lg font-medium">Combined Prompt Preview</h3>
			<div class="form-control whitespace-pre-wrap p-3">
				{$systemPrompt}{$userPrompt ? `${$userPrompt}` : ''}
			</div>
		</div>

		<div class="form-group">
			<label class="flex-start space-x-2">
				<input type="checkbox" bind:checked={forwardOutput} />
				<span class="luna-text-muted">Forward Output</span>
			</label>
		</div>

		<div class="space-x-md">
			<button onclick={handleSaveTemplate} class="btn-primary"> Save Prompt </button>

			{#if !deletionConfirmationMode}
				<button onclick={handleDeleteTemplate} class="btn-danger"> Delete Prompt </button>
			{:else}
				<div class="flex-start space-x-sm">
					<span class="luna-text-warning-light">Confirm deletion?</span>
					<button onclick={handleDeleteTemplate} class="btn-danger"> Yes, Delete </button>
					<button onclick={cancelDeletion} class="btn-secondary"> Cancel </button>
				</div>
			{/if}
		</div>
	</div>
</div>
