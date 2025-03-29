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
	import { engineStates, receiveInput, serviceOutput } from '$lib/shared/shared.svelte';
	import { SUPPORTED_PLATFORMS } from '$lib/shared/constants';

	let templateNames: string[] = $state(listTemplateNames());
	let selectedTemplate: string = $state('Luna Base');

	// For adding new user prompts
	let newUserPromptName: string = $state('');
	let newUserPromptContent: string = $state('');
	let newUserPromptLimit: number = $state(0);

	// For editing user prompts
	let editingPromptId: string | null = $state(null);
	let editPromptName: string = $state('');
	let editPromptContent: string = $state('');
	let editPromptLimit: number = $state(0);

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

		addUserPromptSection(newUserPromptName, newUserPromptContent, newUserPromptLimit);
		newUserPromptName = '';
		newUserPromptContent = '';
		newUserPromptLimit = 0;
	}

	function startEditingPrompt(section: UserPromptSection) {
		editingPromptId = section.id;
		editPromptName = section.name;
		editPromptContent = section.content;
		editPromptLimit = section.limit;
	}

	function saveEditingPrompt() {
		if (editingPromptId) {
			updateUserPromptSection(editingPromptId, editPromptName, editPromptContent, editPromptLimit);
			cancelEditingPrompt();
		}
	}

	function cancelEditingPrompt() {
		editingPromptId = null;
		editPromptName = '';
		editPromptContent = '';
		editPromptLimit = 0;
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
		if (receiveInput.prompt && serviceOutput.llm.prepass) {
			updateUserPromptSection(
				'conversation',
				null,
				`Luna: ${serviceOutput.llm.prepass}`,
				null,
				true
			);
		}
	});

	$effect(() => {
		if (receiveInput.prompt && serviceOutput.chat) {
			const newMessage = serviceOutput.chat.shift();
			if (newMessage && SUPPORTED_PLATFORMS.includes(newMessage.platform as any)) {
				updateUserPromptSection(
					'new-chat-messages',
					null,
					`[${newMessage.platform.charAt(0).toUpperCase() + newMessage.platform.slice(1)}] ${newMessage.author}: ${newMessage.text}`,
					null,
					true
				);
				engineStates.hasNewMessages = true;
			}
		}
	});

	$effect(() => {
		if (receiveInput.prompt && serviceOutput.stt) {
			const newTranscript = serviceOutput.stt.shift();
			if (newTranscript) {
				updateUserPromptSection(
					'new-chat-messages',
					null,
					`[Discord] ${newTranscript.username}: ${newTranscript.transcript}`,
					null,
					true
				);
				engineStates.hasNewMessages = true;
			}
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

		<!-- System Prompt -->
		<div class="form-group bg-bg-surface rounded-md">
			<h3 class="text-text-muted mb-4 text-lg font-medium">System Prompt</h3>
			<textarea id="prompt-template" bind:value={$systemPrompt} rows="5" class="form-control"
			></textarea>
		</div>

		<!-- Dynamic Prompts Section -->
		<div class="form-group bg-bg-surface rounded-md">
			<h3 class="text-text-muted mb-4 text-lg font-medium">Dynamic User Prompts</h3>

			<!-- Add New Dynamic Prompt -->
			<div class="form-group">
				<div class="form-group">
					<label for="newUserPromptName">Name:</label>
					<input
						type="text"
						id="newUserPromptName"
						bind:value={newUserPromptName}
						class="form-control"
						placeholder="Enter prompt name"
					/>
				</div>

				<div class="form-group">
					<label for="newUserPromptContent">Content:</label>
					<textarea
						id="newUserPromptContent"
						bind:value={newUserPromptContent}
						rows="3"
						class="form-control"
						placeholder="Enter prompt content"
					></textarea>
				</div>

				<div class="form-group">
					<label for="newUserPromptLimit">Character Limit:</label>
					<div class="relative mt-1 px-1">
						<input
							id="newUserPromptLimit"
							type="range"
							min="0"
							max="40000"
							step="2000"
							bind:value={newUserPromptLimit}
						/>
						<div class="text-text-disabled flex-between mt-2 px-1 text-base">
							<span>Min</span>
							<span class="text-text-subtle px-2 py-1 font-semibold">{newUserPromptLimit}</span>
							<span>Max</span>
						</div>
					</div>
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

								<div class="form-group">
									<label for="editPromptLimit">Character Limit:</label>
									<div class="relative mt-1 px-1">
										<input
											id="editPromptLimit"
											type="range"
											min="0"
											max="40000"
											step="2000"
											bind:value={editPromptLimit}
										/>
										<div class="text-text-disabled flex-between mt-2 px-1 text-base">
											<span>Min</span>
											<span class="text-text-subtle px-2 py-1 font-semibold">
												{editPromptLimit}
											</span>
											<span>Max</span>
										</div>
									</div>
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
