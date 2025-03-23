<script lang="ts">
	import Card from '$lib/Card.svelte';
	import { serviceError } from '$lib/dockerService';
	import Spinner from '$lib/Spinner.svelte';
	import { sttOutput, discordOutput } from '$lib/stores';
	import { transcribeAudio, fetchSttModels, sttModels, sttStatus } from '$lib/sttService';
	import ContentPage from '../ContentPage.svelte';
	import ServicePage from './ServicePage.svelte';

	let mediaRecorder: MediaRecorder | null = $state(null);
	let audioChunks: Blob[] = $state([]);
	let transcribedText: string | null = $state(null);
	let isRecording = $state(false);
	let recordingTime = $state(0);
	let recordingTimer: number | null = $state(null);
	let audioStream: MediaStream | null = $state(null);
	let selectedModel = $state('whisper-large-v3-turbo');

	let forwardOutput = $state(true);
	let directInputPrefix = $state('TastiHam: ');
	let directInputText = $state('');

	async function handleTranscribeAudio(audioBlob: Blob, prefix?: string) {
		let transcription = await transcribeAudio(audioBlob, selectedModel);

		if (transcription) {
			transcribedText = prefix ? prefix + transcription.trim() : transcription.trim();
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
			serviceError.set(null);

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
					serviceError.set('No audio data recorded');
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
			serviceError.set(
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
			serviceError.set(
				`Failed to load STT models: ${error instanceof Error ? error.message : String(error)}`
			);
		}
	}

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

<ContentPage name="stt-page">
	<ServicePage serviceName="stt-service">
		<Card title="Speech to Text Settings">
			<div class="flex-start">
				<label class="space-x-2">
					<input type="checkbox" bind:checked={forwardOutput} />
					<span class="text-text-muted">Forward Output</span>
				</label>
			</div>

			<div class="form-group">
				<label for="model">Model</label>
				<select id="model" bind:value={selectedModel} class="form-control">
					{#each $sttModels as modelOption}
						<option value={modelOption.value}>{modelOption.label}</option>
					{/each}
				</select>
			</div>

			<div class="form-control form-group border-border-base p-5">
				<h3 class="text-text-muted mb-2 text-sm font-medium">Direct Text Input</h3>
				<div class="form-group flex flex-row space-x-2">
					<div>
						<label for="prefix">Prefix (optional)</label>
						<input
							type="text"
							id="prefix"
							class="form-control"
							placeholder="e.g. UserName:"
							bind:value={directInputPrefix}
						/>
					</div>
					<div class="w-full">
						<label for="directText">Text</label>
						<input
							type="text"
							id="directText"
							class="form-control"
							placeholder="Hey there, hello!"
							bind:value={directInputText}
						/>
					</div>
				</div>
				<div>
					<button
						onclick={handleDirectTextInput}
						disabled={!directInputText}
						class="btn-primary self-end"
					>
						Send
					</button>
				</div>
			</div>

			<div class="mt-6">
				<button
					onclick={() => (isRecording ? stopRecording() : recordAudio())}
					disabled={isTranscribing}
					class="btn-primary"
				>
					{isRecording ? 'Stop Recording' : 'Start Recording'}
				</button>

				{#if isRecording}
					<div class="flex-start mt-4 p-1">
						<span class="status-indicator bg-danger mr-2 animate-pulse rounded-full"></span>
						<span class="text-text-muted text-sm">Recording: {formatTime(recordingTime)}</span>
					</div>
				{/if}

				{#if isTranscribing}
					<div class="flex-start mt-6">
						<Spinner class="text-text-base icon-lg mr-2" />
						<span class="text-text-muted text-sm">Transcribing...</span>
					</div>
				{/if}
			</div>

			{#if transcribedText}
				<div class="mt-6">
					<h3 class="text-text-muted mb-2 text-lg font-medium">Transcribed Text:</h3>
					<div class="form-control whitespace-pre-wrap p-4">
						{transcribedText}
					</div>
				</div>
			{/if}
		</Card>
	</ServicePage>
</ContentPage>
