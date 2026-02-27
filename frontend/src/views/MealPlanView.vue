<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useNotificationsStore } from "@/stores/notifications";
import api from "@/services/api";

interface MealPlanEntry {
  id: string;
  recipe_id: string;
  recipe_title?: string;
  meal_date: string;
  meal_type: string;
  servings: number;
  notes: string | null;
}

const notifications = useNotificationsStore();
const loading = ref(false);
const entries = ref<MealPlanEntry[]>([]);

const currentWeekStart = ref(getMonday(new Date()));

function getMonday(d: Date): Date {
  const date = new Date(d);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  date.setDate(diff);
  date.setHours(0, 0, 0, 0);
  return date;
}

function formatDate(d: Date): string {
  return d.toISOString().split("T")[0] as string;
}

const weekDays = computed(() => {
  const days: { date: Date; label: string; dateStr: string }[] = [];
  const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  for (let i = 0; i < 7; i++) {
    const d = new Date(currentWeekStart.value);
    d.setDate(d.getDate() + i);
    days.push({
      date: d,
      label: dayNames[i] as string,
      dateStr: formatDate(d),
    });
  }
  return days;
});

const mealTypes = ["breakfast", "lunch", "dinner", "snack"];

function entriesFor(dateStr: string, mealType: string): MealPlanEntry[] {
  return entries.value.filter(
    (e) => e.meal_date.startsWith(dateStr) && e.meal_type === mealType,
  );
}

function prevWeek(): void {
  const d = new Date(currentWeekStart.value);
  d.setDate(d.getDate() - 7);
  currentWeekStart.value = d;
  void loadEntries();
}

function nextWeek(): void {
  const d = new Date(currentWeekStart.value);
  d.setDate(d.getDate() + 7);
  currentWeekStart.value = d;
  void loadEntries();
}

const weekLabel = computed(() => {
  const start = weekDays.value[0]!;
  const end = weekDays.value[6]!;
  return `${start.date.toLocaleDateString("en-US", { month: "short", day: "numeric" })} - ${end.date.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
});

async function loadEntries(): Promise<void> {
  loading.value = true;
  try {
    const startDate = formatDate(weekDays.value[0]!.date);
    const endDate = formatDate(weekDays.value[6]!.date);
    const { data } = await api.get<MealPlanEntry[]>("/meal-plan/", {
      params: { start_date: startDate, end_date: endDate },
    });
    entries.value = data;
  } catch {
    // Endpoint may not exist yet
    entries.value = [];
  } finally {
    loading.value = false;
  }
}

async function removeEntry(id: string): Promise<void> {
  try {
    await api.delete(`/meal-plan/${id}`);
    entries.value = entries.value.filter((e) => e.id !== id);
    notifications.success("Removed from meal plan");
  } catch {
    notifications.error("Failed to remove entry");
  }
}

async function generateShoppingList(): Promise<void> {
  try {
    const startDate = formatDate(weekDays.value[0]!.date);
    const endDate = formatDate(weekDays.value[6]!.date);
    await api.post("/meal-plan/generate-shopping-list", null, {
      params: { start_date: startDate, end_date: endDate },
    });
    notifications.success("Shopping list generated from meal plan!");
  } catch {
    notifications.error("Failed to generate shopping list");
  }
}

onMounted(() => {
  void loadEntries();
});
</script>

<template>
  <div class="meal-plan-view">
    <div class="plan-header">
      <h1>Meal Plan</h1>
      <div class="week-nav">
        <button type="button" class="nav-arrow" aria-label="Previous week" @click="prevWeek">&larr;</button>
        <span class="week-label">{{ weekLabel }}</span>
        <button type="button" class="nav-arrow" aria-label="Next week" @click="nextWeek">&rarr;</button>
      </div>
    </div>

    <button class="btn-secondary generate-btn" type="button" @click="generateShoppingList">
      Generate Shopping List
    </button>

    <div v-if="loading" class="loading-text">Loading meal plan...</div>

    <div class="calendar">
      <div v-for="day in weekDays" :key="day.dateStr" class="day-column card">
        <div class="day-header">
          <span class="day-name">{{ day.label }}</span>
          <span class="day-date">{{ day.date.getDate() }}</span>
        </div>
        <div v-for="type in mealTypes" :key="type" class="meal-slot">
          <span class="meal-type-label">{{ type }}</span>
          <div v-for="entry in entriesFor(day.dateStr, type)" :key="entry.id" class="meal-entry">
            <router-link :to="`/recipes/${entry.recipe_id}`" class="entry-title">
              {{ entry.recipe_title ?? "Recipe" }}
            </router-link>
            <button
              type="button"
              class="entry-remove"
              aria-label="Remove from meal plan"
              @click="removeEntry(entry.id)"
            >
              &times;
            </button>
          </div>
          <div v-if="entriesFor(day.dateStr, type).length === 0" class="empty-slot">
            &mdash;
          </div>
        </div>
      </div>
    </div>

    <p class="hint">
      To add recipes to your meal plan, search for a recipe and use "Add to Meal Plan" from the recipe detail page.
    </p>
  </div>
</template>

<style scoped>
.plan-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.plan-header h1 {
  font-size: 1.5rem;
}

.week-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.nav-arrow {
  background: none;
  font-size: 1.25rem;
  padding: 0.5rem;
  min-height: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
}

.week-label {
  font-weight: 600;
  font-size: 1rem;
}

.generate-btn {
  width: 100%;
  margin-bottom: 1rem;
}

.loading-text {
  text-align: center;
  color: var(--text-secondary);
  padding: 2rem;
}

.calendar {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

@media (min-width: 768px) {
  .calendar {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.5rem;
  }
}

.day-column {
  padding: 0.75rem;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--primary-light);
}

.day-name {
  font-weight: 600;
  font-size: 0.875rem;
}

.day-date {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.meal-slot {
  margin-bottom: 0.5rem;
}

.meal-type-label {
  display: block;
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.meal-entry {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--primary-light);
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  margin-bottom: 0.25rem;
}

.entry-title {
  font-size: 0.8125rem;
  color: var(--primary-dark);
  text-decoration: none;
  font-weight: 500;
}

.entry-remove {
  background: none;
  color: var(--text-secondary);
  font-size: 1rem;
  padding: 0.125rem 0.25rem;
  min-height: auto;
}

.empty-slot {
  font-size: 0.8125rem;
  color: var(--border);
  text-align: center;
}

.hint {
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  margin-top: 1.5rem;
  padding: 1rem;
}
</style>
