import { defineStore } from "pinia";
import { ref } from "vue";
import type { HouseholdIngredient, BarcodeScanResult, CameraScanResult } from "@/types";
import { ingredientsApi } from "@/services/api";

export const useIngredientsStore = defineStore("ingredients", () => {
  const householdIngredients = ref<HouseholdIngredient[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchHouseholdIngredients(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await ingredientsApi.getHousehold();
      householdIngredients.value = data;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "Failed to fetch ingredients";
    } finally {
      loading.value = false;
    }
  }

  async function addIngredient(data: {
    name?: string;
    barcode?: string;
    quantity?: number;
    unit?: string;
    source?: string;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const { data: newItem } = await ingredientsApi.addToHousehold(data);
      householdIngredients.value.push(newItem);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "Failed to add ingredient";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function removeIngredient(id: string): Promise<void> {
    try {
      await ingredientsApi.removeFromHousehold(id);
      householdIngredients.value = householdIngredients.value.filter((i) => i.id !== id);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error.value = err.response?.data?.detail ?? "Failed to remove ingredient";
    }
  }

  async function scanBarcode(barcode: string): Promise<BarcodeScanResult> {
    const { data } = await ingredientsApi.scanBarcode(barcode);
    return data;
  }

  async function cameraScan(imageBase64: string): Promise<CameraScanResult> {
    const { data } = await ingredientsApi.cameraScan(imageBase64);
    return data;
  }

  return {
    householdIngredients,
    loading,
    error,
    fetchHouseholdIngredients,
    addIngredient,
    removeIngredient,
    scanBarcode,
    cameraScan,
  };
});
