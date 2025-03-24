<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import ContentPage from '../ContentPage.svelte';
	import { serviceError } from '../services/docker/dockerService';
	import {
		listTemplateNames,
		saveTemplate,
		deleteTemplate,
		addUserPromptSection,
		type UserPromptSection,
		updateUserPromptSection,
		deleteUserPromptSection,
		loadTemplate,
		userPromptSections,
		templateName,
		systemPrompt,
		userPrompt
	} from './promptPage';
	import { receiveInput, serviceOutput } from '$lib/shared/shared.svelte';

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

	function handleSaveTemplate() {
		saveTemplate($templateName, $systemPrompt);
		templateNames = listTemplateNames();
		selectedTemplate = $templateName;
	}

	function handleDeleteTemplate() {
		if (!selectedTemplate) {
			serviceError.set('No prompt selected to delete.');
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
			serviceError.set('Please enter a name for the dynamic prompt.');
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

	$effect(() => {
		if (selectedTemplate) {
			loadTemplate(selectedTemplate);
		} else if (templateNames.length > 0) {
			selectedTemplate = templateNames[0];
		}
	});

	$effect(() => {
		if (receiveInput.prompt && serviceOutput.llm) {
			updateUserPromptSection('conversation', null, `\nLuna: ${serviceOutput.llm}`, true);
		}
	});

	$effect(() => {
		if (receiveInput.prompt && serviceOutput.stt) {
			updateUserPromptSection('conversation', null, `\n${serviceOutput.stt}`, true);
		}
	});
</script>

<ContentPage name="prompt-page">
	<Card title="Template Settings">
		<div class="">
			<label>
				<input type="checkbox" bind:checked={receiveInput.prompt} />
				<span>Receive Input</span>
			</label>
		</div>

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
			<input id="templateName" type="text" bind:value={$templateName} class="form-control" />
		</div>

		<!-- Main Prompt Template Section -->
		<div class="form-group bg-bg-surface rounded-md">
			<h3 class="text-text-muted mb-4 text-lg font-medium">Main Prompt Template</h3>
			<textarea id="prompt-template" bind:value={$systemPrompt} rows="5" class="form-control"
			></textarea>
		</div>

		<!-- Dynamic Prompts Section -->
		<div class="form-group bg-bg-surface rounded-md">
			<h3 class="text-text-muted mb-4 text-lg font-medium">Dynamic Prompts</h3>

			<!-- Add New Dynamic Prompt -->
			<div class="form-group">
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

				<button onclick={handleAddUserPrompt} class="btn-success">Add Dynamic Prompt</button>
			</div>

			<!-- List of Dynamic Prompts -->
			<div>
				{#if $userPromptSections.length === 0}
					<p class="text-text-disabled">No dynamic prompts added yet.</p>
				{:else}
					{#each $userPromptSections as section}
						<div class="border-border-subtle bg-bg-elevated mb-3 rounded-md border p-4">
							{#if editingPromptId === section.id}
								<!-- Edit Mode -->
								<div class="form-group">
									<label for="editPromptName">Label:</label>
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

								<div class="flex items-center">
									<button onclick={saveEditingPrompt} class="btn-primary mr-4">Save</button>
									<button onclick={cancelEditingPrompt} class="btn-secondary">Cancel</button>
								</div>
							{:else}
								<!-- View Mode -->
								<div class="flex-between mb-1">
									<h4>{section.name}</h4>
									<div class="mb-2 flex items-center">
										<button onclick={() => startEditingPrompt(section)} class="btn-info mr-4">
											Edit
										</button>
										<button
											onclick={() => handleDeleteDynamicPrompt(section.id)}
											class="btn-danger"
										>
											Delete
										</button>
									</div>
								</div>
								<div class="bg-bg-surface text-text-muted whitespace-pre-wrap rounded-md p-2">
									{section.content}
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</div>

		{#if $systemPrompt || $userPrompt}
			<!-- Combined Prompt Preview -->
			<div class="form-group bg-bg-surface rounded-md">
				<h3 class="text-text-muted mb-2 text-lg font-medium">Combined Prompt Preview</h3>
				<div class="form-control whitespace-pre-wrap p-3">
					{$systemPrompt}{$userPrompt ? `${$userPrompt}` : ''}
				</div>
			</div>
		{/if}

		<div class="flex items-center space-x-4">
			<button onclick={handleSaveTemplate} class="btn-primary">Save Prompt</button>

			{#if !deletionConfirmationMode}
				<button onclick={handleDeleteTemplate} class="btn-danger">Delete Prompt</button>
			{:else}
				<div class="flex items-center space-x-2">
					<span class="text-warning-light">Confirm deletion?</span>
					<button onclick={handleDeleteTemplate} class="btn-danger">Yes, Delete</button>
					<button onclick={cancelDeletion} class="btn-secondary">Cancel</button>
				</div>
			{/if}
		</div>
	</Card>
</ContentPage>
