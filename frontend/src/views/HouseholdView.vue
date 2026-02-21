<script setup lang="ts">
import { ref, onMounted } from "vue";
import type { FamilyMember, Household } from "@/types";
import { householdApi } from "@/services/api";

const household = ref<Household | null>(null);
const members = ref<FamilyMember[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const newMemberName = ref("");
const newMemberRole = ref("member");
const newMemberDietaryNotes = ref("");

onMounted(() => {
  void fetchData();
});

async function fetchData(): Promise<void> {
  loading.value = true;
  try {
    const [hRes, mRes] = await Promise.all([householdApi.get(), householdApi.getMembers()]);
    household.value = hRes.data;
    members.value = mRes.data;
  } catch {
    error.value = "Failed to load household data";
  } finally {
    loading.value = false;
  }
}

async function addMember(): Promise<void> {
  if (!newMemberName.value.trim()) return;
  try {
    const { data } = await householdApi.addMember({
      name: newMemberName.value.trim(),
      role: newMemberRole.value,
      dietary_notes: newMemberDietaryNotes.value || undefined,
    });
    members.value.push(data);
    newMemberName.value = "";
    newMemberRole.value = "member";
    newMemberDietaryNotes.value = "";
  } catch {
    error.value = "Failed to add member";
  }
}

async function removeMember(id: string): Promise<void> {
  try {
    await householdApi.removeMember(id);
    members.value = members.value.filter((m) => m.id !== id);
  } catch {
    error.value = "Failed to remove member";
  }
}
</script>

<template>
  <div class="household-view">
    <h1>My Household</h1>

    <div v-if="household" class="household-info card">
      <h2>{{ household.name }}</h2>
    </div>

    <div class="add-member card">
      <h3>Add Family Member</h3>
      <form @submit.prevent="addMember">
        <div class="form-group">
          <label for="memberName">Name</label>
          <input id="memberName" v-model="newMemberName" type="text" placeholder="Member name" required />
        </div>
        <div class="form-group">
          <label for="memberRole">Role</label>
          <select id="memberRole" v-model="newMemberRole">
            <option value="member">Member</option>
            <option value="child">Child</option>
            <option value="parent">Parent</option>
          </select>
        </div>
        <div class="form-group">
          <label for="dietaryNotes">Dietary Notes</label>
          <textarea
            id="dietaryNotes"
            v-model="newMemberDietaryNotes"
            placeholder="e.g., allergic to nuts, lactose intolerant..."
            rows="2"
          />
        </div>
        <button class="btn-primary full-width" type="submit">Add Member</button>
      </form>
    </div>

    <div class="members-section">
      <h3>Family Members ({{ members.length }})</h3>
      <div v-for="member in members" :key="member.id" class="member-card card">
        <div class="member-info">
          <strong>{{ member.name }}</strong>
          <span class="role-badge">{{ member.role }}</span>
          <p v-if="member.dietary_notes" class="dietary-notes">{{ member.dietary_notes }}</p>
        </div>
        <button
          v-if="member.role !== 'owner'"
          class="remove-btn"
          type="button"
          @click="removeMember(member.id)"
        >
          Remove
        </button>
      </div>
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<style scoped>
.household-info h2 {
  color: var(--primary);
}

.add-member {
  margin-top: 1rem;
}

.add-member h3 {
  margin-bottom: 0.75rem;
}

.full-width {
  width: 100%;
}

.members-section {
  margin-top: 1.5rem;
}

.members-section h3 {
  margin-bottom: 0.75rem;
}

.member-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem 1rem;
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.role-badge {
  font-size: 0.75rem;
  background: var(--border);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  width: fit-content;
  text-transform: capitalize;
}

.dietary-notes {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.remove-btn {
  background: none;
  color: var(--error);
  font-size: 0.875rem;
  padding: 0.5rem;
}
</style>
