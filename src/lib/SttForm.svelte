<script lang="ts">
	import { sttOutput, discordOutput } from './stores';
	import { transcribeAudio, sttError, sttStatus, fetchSttModels, sttModels } from './sttService';
	import Icon from './Icon.svelte';
	import Spinner from './Spinner.svelte';

	let mediaRecorder: MediaRecorder | null = $state(null);
	let audioChunks: Blob[] = $state([]);
	let transcribedText: string | null = $state(null);
	let isRecording = $state(false);
	let recordingTime = $state(0);
	let recordingTimer: number | null = $state(null);
	let audioStream: MediaStream | null = $state(null);
	let selectedModel = $state('distil-whisper-large-v3-en');
	let localErrorMessage = $state<string | null>(null);

	let forwardOutput = $state(true);
	let directInputPrefix = $state('TastiHam: ');
	let directInputText = $state('');

	const displayError = $derived($sttError || localErrorMessage);

	async function handleTranscribeAudio(audioBlob: Blob, prefix?: string) {
		let transcription = await transcribeAudio(audioBlob, selectedModel);

		if (transcription) {
			transcribedText = (prefix ? prefix + transcription : transcription).trim();
		}

		isRecording = false;

		// Release media stream
		if (audioStream) {
			audioStream.getTracks().forEach((track) => track.stop());
			audioStream = null;
		}

		if (forwardOutput && transcribedText) {
			sttOutput.set(transcribedText);
		}
	}

	// Cleanup function to stop recording and release resources
	function cleanup() {
		if (mediaRecorder && mediaRecorder.state !== 'inactive') {
			mediaRecorder.stop();
		}

		if (audioStream) {
			audioStream.getTracks().forEach((track) => track.stop());
			audioStream = null;
		}

		if (recordingTimer) {
			window.clearInterval(recordingTimer);
			recordingTimer = null;
		}

		isRecording = false;
	}

	async function recordAudio() {
		try {
			// Reset state
			transcribedText = null;
			audioChunks = [];
			recordingTime = 0;
			sttError.set(null);

			// Get audio stream
			audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

			// Configure media recorder
			const options = {
				audioBitsPerSecond: 128000,
				mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp3'
			};

			mediaRecorder = new MediaRecorder(audioStream, options);

			// Set up event handlers
			mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					audioChunks = [...audioChunks, event.data];
				}
			};

			mediaRecorder.onstop = async () => {
				if (recordingTimer) {
					window.clearInterval(recordingTimer);
					recordingTimer = null;
				}

				if (audioChunks.length === 0) {
					sttError.set('No audio data recorded');
					isRecording = false;
					return;
				}

				// Create audio blob from chunks
				const audioBlob = new Blob(audioChunks, { type: options.mimeType });
				audioChunks = []; // Clear chunks after processing

				await handleTranscribeAudio(audioBlob);
			};

			// Start recording
			mediaRecorder.start(1000); // Collect data every second
			isRecording = true;

			// Start timer
			recordingTimer = window.setInterval(() => {
				recordingTime += 1;
			}, 1000);
		} catch (error) {
			sttError.set(
				`Error accessing microphone: ${error instanceof Error ? error.message : String(error)}`
			);
			isRecording = false;
		}
	}

	function stopRecording() {
		if (mediaRecorder && mediaRecorder.state !== 'inactive') {
			mediaRecorder.stop();
		}
	}

	function formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
	}

	function handleDirectTextInput() {
		// Set the transcribed text with the prefix
		transcribedText = directInputPrefix ? directInputPrefix + directInputText : directInputText;

		// Forward the text if the checkbox is checked
		if (forwardOutput && transcribedText) {
			sttOutput.set(transcribedText);
		}

		// Clear the input text after forwarding
		directInputText = '';
	}

	// Fetch available models on component initialization
	async function loadModels() {
		try {
			await fetchSttModels();
			// If no model is selected yet and we have models, select the first one
			if (!selectedModel && $sttModels.length > 0) {
				selectedModel = $sttModels[0].value;
			}
		} catch (error) {
			localErrorMessage = `Failed to load STT models: ${error instanceof Error ? error.message : String(error)}`;
		}
	}

	const buttonLabel = $derived(isRecording ? 'Stop Recording' : 'Start Recording');
	const isTranscribing = $derived($sttStatus === 'transcribing');

	// Load models when component is mounted
	$effect(() => {
		loadModels();
	});

	// Clean up resources when component is destroyed
	$effect(() => {
		const unsubscribe = discordOutput.subscribe(async (newAudio) => {
			if (newAudio) {
				await handleTranscribeAudio(newAudio.audioBlob, newAudio.username + ': ');
			}
		});
		return () => {
			unsubscribe;
			cleanup;
		};
	});
</script>

<div class="card">
	<div class="card-header">
		<h2>
			<Icon
				path="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
				class="luna-text-primary-light icon-lg mr-2"
			/>
			Speech-to-Text
		</h2>
	</div>

	<div class="card-body">
		{#if displayError}
			<div class="alert-error">
				<p class="flex-start">
					<Icon
						path="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
						class="luna-text-danger icon-lg mr-2"
					/>
					{displayError}
				</p>
			</div>
		{/if}

		<div class="form-group">
			<label for="model">Model</label>
			<select id="model" bind:value={selectedModel} class="form-control">
				{#each $sttModels as modelOption}
					<option value={modelOption.value}>{modelOption.label}</option>
				{/each}
			</select>
		</div>

		<div class="form-group">
			<label class="flex-start space-x-2">
				<input type="checkbox" bind:checked={forwardOutput} />
				<span class="luna-text-muted">Forward Output</span>
			</label>
		</div>

		<div class="form-group luna-border-base border-t pt-4">
			<h3 class="luna-text-muted mb-2 text-sm font-medium">Direct Text Input</h3>
			<div class="space-y-3">
				<div class="form-group">
					<label for="prefix" class="luna-text-disabled text-xs">Prefix (optional)</label>
					<input
						type="text"
						id="prefix"
						class="form-control"
						placeholder="e.g. User:"
						bind:value={directInputPrefix}
					/>
				</div>
				<div class="form-group">
					<label for="directText" class="luna-text-disabled text-xs">Text</label>
					<textarea
						id="directText"
						rows="3"
						class="form-control"
						placeholder="Enter text to forward directly"
						bind:value={directInputText}
					></textarea>
				</div>
				<button
					onclick={handleDirectTextInput}
					disabled={!directInputText}
					class="btn-primary self-start"
				>
					Forward Text
				</button>
			</div>
		</div>

		<div class="form-group">
			<button
				onclick={() => (isRecording ? stopRecording() : recordAudio())}
				disabled={isTranscribing}
				class="btn-primary"
			>
				{buttonLabel}
			</button>

			{#if isRecording}
				<div class="flex-start mt-4">
					<span class="status-indicator status-pulse luna-bg-danger mr-2"></span>
					<span class="luna-text-muted text-sm">Recording: {formatTime(recordingTime)}</span>
				</div>
			{/if}

			{#if isTranscribing}
				<div class="flex-start mt-4">
					<Spinner class="icon-lg mr-2" />
					<span class="luna-text-muted text-sm">Transcribing...</span>
				</div>
			{/if}
		</div>

		{#if transcribedText}
			<div class="form-group">
				<h3 class="luna-text-muted mb-2 text-lg font-medium">Transcribed Text:</h3>
				<div class="form-control whitespace-pre-wrap p-4">
					{transcribedText}
				</div>
			</div>
		{/if}
	</div>
</div>
