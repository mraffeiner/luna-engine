<script lang="ts">
	import { sttOutput, discordOutput } from './stores';

	import { transcribeAudio, sttError, sttStatus } from './sttService';

	let mediaRecorder: MediaRecorder | null = $state(null);
	let audioChunks: Blob[] = $state([]);
	let transcribedText: string | null = $state(null);
	let isRecording = $state(false);
	let recordingTime = $state(0);
	let recordingTimer: number | null = $state(null);
	let audioStream: MediaStream | null = $state(null);

	let forwardToLlm = $state(false);

	async function handleTranscribeAudio(audioBlob: Blob, prefix?: string) {
		// Transcribe the audio
		const transcription = await transcribeAudio(audioBlob);

		if (transcription) {
			transcribedText = prefix ? prefix + transcription : transcription;
		}

		isRecording = false;

		// Release media stream
		if (audioStream) {
			audioStream.getTracks().forEach((track) => track.stop());
			audioStream = null;
		}

		if (forwardToLlm && transcribedText) {
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

	const buttonLabel = $derived(isRecording ? 'Stop Recording' : 'Start Recording');
	const isTranscribing = $derived($sttStatus === 'transcribing');

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
				d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
			/>
		</svg>
		Speech-to-Text
	</h2>

	{#if $sttError}
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
				{$sttError}
			</p>
		</div>
	{/if}

	<div class="mt-4">
		<label class="inline-flex items-center space-x-2">
			<input
				type="checkbox"
				class="rounded border-gray-600 text-indigo-600 focus:ring-indigo-500"
				bind:checked={forwardToLlm}
			/>
			<span class="text-gray-200">Forward to LLM</span>
		</label>
	</div>

	<div class="mt-6">
		<button
			onclick={() => (isRecording ? stopRecording() : recordAudio())}
			disabled={isTranscribing}
			class="rounded-md bg-indigo-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-indigo-700 disabled:bg-gray-500"
		>
			{buttonLabel}
		</button>

		{#if isRecording}
			<div class="mt-8">
				<span class="mr-2 h-3 w-3 animate-pulse rounded-full bg-red-500"></span>
				<span class="text-sm text-gray-300">Recording: {formatTime(recordingTime)}</span>
			</div>
		{/if}

		{#if isTranscribing}
			<div class="mt-8">
				<span
					class="mr-2 h-3 w-3 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"
				></span>
				<span class="text-sm text-gray-300">Transcribing...</span>
			</div>
		{/if}
	</div>

	{#if transcribedText}
		<div class="mt-6">
			<h3 class="mb-2 text-lg font-medium text-gray-200">Transcribed Text:</h3>
			<div class="whitespace-pre-wrap rounded-md border border-gray-600 bg-gray-700 p-4 text-white">
				{transcribedText}
			</div>
		</div>
	{/if}
</div>
