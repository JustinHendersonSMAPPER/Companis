<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useShoppingStore } from "@/stores/shopping";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";

const store = useShoppingStore();

const newItemName = ref("");
const newItemQuantity = ref<number | undefined>(undefined);
const newItemUnit = ref("");

onMounted(() => {
  void store.fetchCarts();
});

async function createNewCart(): Promise<void> {
  await store.createCart("Shopping List");
}

async function addItem(cartId: string): Promise<void> {
  if (!newItemName.value.trim()) return;
  await store.addItem(cartId, {
    name: newItemName.value.trim(),
    quantity: newItemQuantity.value,
    unit: newItemUnit.value || undefined,
  });
  newItemName.value = "";
  newItemQuantity.value = undefined;
  newItemUnit.value = "";
}

async function toggleItem(cartId: string, itemId: string): Promise<void> {
  await store.togglePurchased(cartId, itemId);
}

async function removeItem(cartId: string, itemId: string): Promise<void> {
  await store.removeItem(cartId, itemId);
}
</script>

<template>
  <div class="shopping-view">
    <h1>Shopping Lists</h1>

    <LoadingSpinner v-if="store.loading" message="Loading shopping lists..." />

    <div v-if="store.carts.length === 0 && !store.loading" class="empty-state">
      <p>No shopping lists yet.</p>
      <button class="btn-primary" type="button" @click="createNewCart">
        Create Shopping List
      </button>
    </div>

    <div v-for="cart in store.carts" :key="cart.id" class="cart-section">
      <h2>{{ cart.name }}</h2>

      <form class="add-item-form" @submit.prevent="addItem(cart.id)">
        <input v-model="newItemName" type="text" placeholder="Add item..." />
        <input v-model.number="newItemQuantity" type="number" placeholder="Qty" step="0.1" />
        <button class="btn-primary" type="submit">Add</button>
      </form>

      <div v-if="cart.items.length === 0" class="empty-cart">
        <p>No items in this list yet.</p>
      </div>

      <div class="item-list">
        <div
          v-for="item in cart.items"
          :key="item.id"
          class="cart-item"
          :class="{ purchased: item.is_purchased }"
        >
          <input
            type="checkbox"
            class="check-input"
            :checked="item.is_purchased"
            :aria-label="`Mark ${item.name} as ${item.is_purchased ? 'not purchased' : 'purchased'}`"
            @change="toggleItem(cart.id, item.id)"
          />
          <div class="item-info">
            <span class="item-name">{{ item.name }}</span>
            <span v-if="item.quantity" class="item-qty">
              {{ item.quantity }} {{ item.unit ?? "" }}
            </span>
            <span v-if="item.notes" class="item-notes">{{ item.notes }}</span>
          </div>
          <button class="remove-btn" type="button" aria-label="Remove item" @click="removeItem(cart.id, item.id)">
            &times;
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  text-align: center;
  padding: 2rem;
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.cart-section {
  margin-bottom: 2rem;
}

.cart-section h2 {
  margin-bottom: 0.75rem;
}

.add-item-form {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.add-item-form input:first-child {
  flex: 2;
}

.add-item-form input:nth-child(2) {
  flex: 1;
  max-width: 80px;
}

.empty-cart {
  text-align: center;
  padding: 1rem;
  color: var(--text-secondary);
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}

.cart-item.purchased .item-name {
  text-decoration: line-through;
  color: var(--text-secondary);
}

.check-input {
  width: auto;
  min-width: 20px;
  min-height: 20px;
  accent-color: var(--primary);
  cursor: pointer;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.item-name {
  font-weight: 500;
}

.item-qty {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.item-notes {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-style: italic;
}

.remove-btn {
  background: none;
  color: var(--error);
  font-size: 1.25rem;
  padding: 0.25rem 0.5rem;
  min-height: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
