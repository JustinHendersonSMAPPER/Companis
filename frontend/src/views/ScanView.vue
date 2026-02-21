<script setup lang="ts">
import { ref } from "vue";
import { useIngredientsStore } from "@/stores/ingredients";
import type { BarcodeScanResult, CameraScanResult } from "@/types";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";

const store = useIngredientsStore();

const activeTab = ref<"barcode" | "camera">("barcode");
const barcodeInput = ref("");
const barcodeResult = ref<BarcodeScanResult | null>(null);
const cameraResult = ref<CameraScanResult | null>(null);
const scanning = ref(false);
const error = ref<string | null>(null);

const videoRef = ref<HTMLVideoElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const cameraActive = ref(false);

async function handleBarcodeScan(): Promise<void> {
  if (!barcodeInput.value.trim()) return;
  scanning.value = true;
  error.value = null;
  try {
    barcodeResult.value = await store.scanBarcode(barcodeInput.value.trim());
  } catch {
    error.value = "Failed to look up barcode";
  } finally {
    scanning.value = false;
  }
}

async function addBarcodeIngredient(): Promise<void> {
  if (!barcodeResult.value?.found) return;
  try {
    await store.addIngredient({
      name: barcodeResult.value.product_name ?? "Unknown",
      barcode: barcodeResult.value.barcode,
      source: "barcode",
    });
    barcodeResult.value = null;
    barcodeInput.value = "";
  } catch {
    error.value = "Failed to add ingredient";
  }
}

async function startCamera(): Promise<void> {
  error.value = null;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
    });
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      await videoRef.value.play();
      cameraActive.value = true;
    }
  } catch {
    error.value = "Could not access camera. Please check permissions.";
  }
}

function stopCamera(): void {
  if (videoRef.value?.srcObject) {
    const tracks = (videoRef.value.srcObject as MediaStream).getTracks();
    tracks.forEach((track) => track.stop());
    videoRef.value.srcObject = null;
  }
  cameraActive.value = false;
}

async function captureAndScan(): Promise<void> {
  if (!videoRef.value || !canvasRef.value) return;
  scanning.value = true;
  error.value = null;

  const canvas = canvasRef.value;
  const video = videoRef.value;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.drawImage(video, 0, 0);

  const imageBase64 = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];
  if (!imageBase64) return;

  try {
    cameraResult.value = await store.cameraScan(imageBase64);
  } catch {
    error.value = "Failed to analyze image";
  } finally {
    scanning.value = false;
  }
}

async function addDetectedIngredient(name: string): Promise<void> {
  try {
    await store.addIngredient({
      name,
      source: "camera",
    });
  } catch {
    error.value = `Failed to add ${name}`;
  }
}
</script>

<template>
  <div class="scan-view">
    <h1>Scan Ingredients</h1>

    <div class="tab-bar">
      <button
        class="tab"
        :class="{ active: activeTab === 'barcode' }"
        type="button"
        @click="activeTab = 'barcode'"
      >
        Barcode Scanner
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'camera' }"
        type="button"
        @click="activeTab = 'camera'"
      >
        Camera Scan
      </button>
    </div>

    <!-- Barcode Scanner -->
    <div v-if="activeTab === 'barcode'" class="card">
      <h3>Scan Barcode</h3>
      <form @submit.prevent="handleBarcodeScan">
        <div class="form-group">
          <input
            v-model="barcodeInput"
            type="text"
            placeholder="Enter barcode number"
            inputmode="numeric"
          />
        </div>
        <button class="btn-primary full-width" type="submit" :disabled="scanning">
          {{ scanning ? "Looking up..." : "Look Up Barcode" }}
        </button>
      </form>

      <div v-if="barcodeResult" class="result card" style="margin-top: 1rem">
        <div v-if="barcodeResult.found">
          <p><strong>{{ barcodeResult.product_name }}</strong></p>
          <p v-if="barcodeResult.brand" class="text-secondary">{{ barcodeResult.brand }}</p>
          <button class="btn-primary" type="button" style="margin-top: 0.5rem" @click="addBarcodeIngredient">
            Add to Pantry
          </button>
        </div>
        <div v-else>
          <p>Product not found for barcode: {{ barcodeResult.barcode }}</p>
        </div>
      </div>
    </div>

    <!-- Camera Scanner -->
    <div v-if="activeTab === 'camera'" class="card">
      <h3>Camera Ingredient Detection</h3>
      <p class="camera-hint">Point your camera at ingredients to identify them using AI</p>

      <div class="camera-container">
        <video ref="videoRef" class="camera-preview" playsinline />
        <canvas ref="canvasRef" style="display: none" />
      </div>

      <div class="camera-controls">
        <button
          v-if="!cameraActive"
          class="btn-primary"
          type="button"
          @click="startCamera"
        >
          Start Camera
        </button>
        <template v-else>
          <button
            class="btn-primary"
            type="button"
            :disabled="scanning"
            @click="captureAndScan"
          >
            {{ scanning ? "Analyzing..." : "Capture & Scan" }}
          </button>
          <button class="btn-secondary" type="button" @click="stopCamera">Stop Camera</button>
        </template>
      </div>

      <LoadingSpinner v-if="scanning" message="AI is identifying ingredients..." />

      <div v-if="cameraResult" class="detected-results">
        <h4>Detected Ingredients</h4>
        <div
          v-for="(confidence, name) in cameraResult.confidence_scores"
          :key="name"
          class="detected-item"
        >
          <div class="detected-info">
            <span>{{ name }}</span>
            <span class="confidence">{{ Math.round(confidence * 100) }}% confidence</span>
          </div>
          <button class="btn-primary btn-sm" type="button" @click="addDetectedIngredient(String(name))">
            Add
          </button>
        </div>
      </div>
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<style scoped>
.tab-bar {
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0;
}

.tab {
  flex: 1;
  padding: 0.75rem;
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  font-weight: 500;
  color: var(--text-secondary);
}

.tab.active {
  border-color: var(--primary);
  color: var(--primary);
}

.full-width {
  width: 100%;
}

.text-secondary {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.camera-hint {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.camera-container {
  margin: 1rem 0;
  border-radius: var(--radius);
  overflow: hidden;
  background: #000;
}

.camera-preview {
  width: 100%;
  max-height: 300px;
  object-fit: cover;
}

.camera-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.camera-controls button {
  flex: 1;
}

.detected-results {
  margin-top: 1rem;
}

.detected-results h4 {
  margin-bottom: 0.5rem;
}

.detected-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}

.detected-info {
  display: flex;
  flex-direction: column;
}

.confidence {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.btn-sm {
  padding: 0.4rem 0.75rem;
  font-size: 0.875rem;
}
</style>
