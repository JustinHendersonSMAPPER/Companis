<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useIngredientsStore } from "@/stores/ingredients";
import VoiceInput from "@/components/common/VoiceInput.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import { aiApi } from "@/services/api";

const store = useIngredientsStore();

const newIngredientName = ref("");
const newQuantity = ref<number | undefined>(undefined);
const newUnit = ref("");
const searchQuery = ref("");

onMounted(() => {
  void store.fetchHouseholdIngredients();
});

const filteredIngredients = computed(() => {
  if (!searchQuery.value) return store.householdIngredients;
  const q = searchQuery.value.toLowerCase();
  return store.householdIngredients.filter(
    (i) =>
      i.ingredient.name.toLowerCase().includes(q) ||
      i.ingredient.category?.toLowerCase().includes(q),
  );
});

async function addIngredient(): Promise<void> {
  if (!newIngredientName.value.trim()) return;
  try {
    await store.addIngredient({
      name: newIngredientName.value.trim(),
      quantity: newQuantity.value,
      unit: newUnit.value || undefined,
      source: "manual",
    });
    newIngredientName.value = "";
    newQuantity.value = undefined;
    newUnit.value = "";
  } catch {
    // Error handled by store
  }
}

async function handleVoiceTranscript(transcript: string): Promise<void> {
  try {
    const { data } = await aiApi.parseVoiceInput(transcript);
    const ingredients = data.ingredients ?? [];
    for (const ing of ingredients) {
      await store.addIngredient({
        name: ing.name,
        quantity: ing.quantity ?? undefined,
        unit: ing.unit ?? undefined,
        source: "voice",
      });
    }
  } catch {
    // Fallback: just use the transcript as a name
    await store.addIngredient({
      name: transcript,
      source: "voice",
    });
  }
}

async function removeIngredient(id: string): Promise<void> {
  await store.removeIngredient(id);
}
</script>

<template>
  <div class="ingredients-view">
    <h1>My Pantry</h1>
    <p class="subtitle">Manage your household ingredients</p>

    <div class="add-section card">
      <h3>Add Ingredient</h3>
      <form @submit.prevent="addIngredient">
        <div class="form-group">
          <input v-model="newIngredientName" type="text" placeholder="Ingredient name" required />
        </div>
        <div class="inline-fields">
          <div class="form-group">
            <input v-model.number="newQuantity" type="number" placeholder="Qty" step="0.1" />
          </div>
          <div class="form-group">
            <select v-model="newUnit">
              <option value="">Unit</option>
              <option value="g">grams</option>
              <option value="kg">kg</option>
              <option value="ml">ml</option>
              <option value="L">liters</option>
              <option value="cups">cups</option>
              <option value="tbsp">tbsp</option>
              <option value="tsp">tsp</option>
              <option value="oz">oz</option>
              <option value="lb">lb</option>
              <option value="pcs">pieces</option>
            </select>
          </div>
        </div>
        <button class="btn-primary full-width" type="submit" :disabled="store.loading">
          Add to Pantry
        </button>
      </form>

      <div class="voice-section">
        <p class="voice-label">Or use voice input:</p>
        <VoiceInput @transcript="handleVoiceTranscript" />
      </div>
    </div>

    <div class="list-section">
      <div class="list-header">
        <h2>Ingredients ({{ store.householdIngredients.length }})</h2>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search..."
          class="search-input"
        />
      </div>

      <LoadingSpinner v-if="store.loading" message="Loading ingredients..." />

      <div v-else-if="filteredIngredients.length === 0" class="empty-state">
        <p>No ingredients yet. Add some from above, scan a barcode, or use camera scan.</p>
      </div>

      <div v-else class="ingredient-list">
        <div
          v-for="item in filteredIngredients"
          :key="item.id"
          class="ingredient-item card"
        >
          <div class="ingredient-info">
            <strong>{{ item.ingredient.name }}</strong>
            <span v-if="item.quantity" class="quantity">
              {{ item.quantity }} {{ item.unit ?? "" }}
            </span>
            <span v-if="item.ingredient.category" class="category">
              {{ item.ingredient.category }}
            </span>
            <span class="source-badge">{{ item.source }}</span>
          </div>
          <button class="remove-btn" type="button" @click="removeIngredient(item.id)">
            Remove
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.add-section h3 {
  margin-bottom: 0.75rem;
}

.inline-fields {
  display: flex;
  gap: 0.5rem;
}

.inline-fields .form-group {
  flex: 1;
}

.full-width {
  width: 100%;
}

.voice-section {
  margin-top: 1rem;
  text-align: center;
}

.voice-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 1.5rem 0 0.75rem;
}

.search-input {
  width: auto;
  max-width: 200px;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.ingredient-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
}

.ingredient-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.quantity {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.category {
  font-size: 0.75rem;
  color: var(--primary);
}

.source-badge {
  font-size: 0.7rem;
  background: var(--border);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  width: fit-content;
}

.remove-btn {
  background: none;
  color: var(--error);
  font-size: 0.875rem;
  padding: 0.5rem;
}
</style>
