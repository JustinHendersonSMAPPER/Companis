import { defineStore } from "pinia";
import { ref } from "vue";
import type { ShoppingCart } from "@/types";
import { shoppingApi } from "@/services/api";

export const useShoppingStore = defineStore("shopping", () => {
  const carts = ref<ShoppingCart[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchCarts(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await shoppingApi.getCarts();
      carts.value = data;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "Failed to fetch shopping carts";
    } finally {
      loading.value = false;
    }
  }

  async function createCart(name?: string): Promise<void> {
    const { data } = await shoppingApi.createCart({ name });
    carts.value.push(data);
  }

  async function addItem(
    cartId: string,
    data: { name: string; quantity?: number; unit?: string },
  ): Promise<void> {
    const { data: item } = await shoppingApi.addItem(cartId, data);
    const cart = carts.value.find((c) => c.id === cartId);
    if (cart) cart.items.push(item);
  }

  async function togglePurchased(cartId: string, itemId: string): Promise<void> {
    const cart = carts.value.find((c) => c.id === cartId);
    const item = cart?.items.find((i) => i.id === itemId);
    if (item) {
      const { data } = await shoppingApi.updateItem(cartId, itemId, {
        is_purchased: !item.is_purchased,
      });
      Object.assign(item, data);
    }
  }

  async function removeItem(cartId: string, itemId: string): Promise<void> {
    await shoppingApi.removeItem(cartId, itemId);
    const cart = carts.value.find((c) => c.id === cartId);
    if (cart) {
      cart.items = cart.items.filter((i) => i.id !== itemId);
    }
  }

  async function addMissingIngredients(recipeId: string, names: string[]): Promise<void> {
    await shoppingApi.addMissingIngredients({
      recipe_id: recipeId,
      ingredient_names: names,
    });
    await fetchCarts();
  }

  return {
    carts,
    loading,
    error,
    fetchCarts,
    createCart,
    addItem,
    togglePurchased,
    removeItem,
    addMissingIngredients,
  };
});
