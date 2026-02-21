<script setup lang="ts">
import { ref } from "vue";

const emit = defineEmits<{
  transcript: [text: string];
}>();

const isListening = ref(false);
const transcript = ref("");
const error = ref<string | null>(null);

let recognition: SpeechRecognition | null = null;

function startListening(): void {
  const SpeechRecognitionCtor = window.SpeechRecognition ?? window.webkitSpeechRecognition;

  if (!SpeechRecognitionCtor) {
    error.value = "Speech recognition is not supported in this browser";
    return;
  }

  recognition = new SpeechRecognitionCtor();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    isListening.value = true;
    error.value = null;
  };

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    let finalTranscript = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      if (result?.[0]) {
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          transcript.value = result[0].transcript;
        }
      }
    }
    if (finalTranscript) {
      transcript.value = finalTranscript;
      emit("transcript", finalTranscript);
    }
  };

  recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
    error.value = `Speech recognition error: ${event.error}`;
    isListening.value = false;
  };

  recognition.onend = () => {
    isListening.value = false;
  };

  recognition.start();
}

function stopListening(): void {
  if (recognition) {
    recognition.stop();
  }
}
</script>

<template>
  <div class="voice-input">
    <button
      class="voice-btn"
      :class="{ listening: isListening }"
      type="button"
      @click="isListening ? stopListening() : startListening()"
    >
      {{ isListening ? "Stop" : "Voice" }}
    </button>
    <p v-if="transcript" class="transcript">{{ transcript }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<style scoped>
.voice-input {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.voice-btn {
  background: var(--primary);
  color: white;
  border-radius: 50%;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0;
}

.voice-btn.listening {
  background: var(--error);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.transcript {
  font-size: 0.875rem;
  color: var(--text-secondary);
  text-align: center;
}
</style>
