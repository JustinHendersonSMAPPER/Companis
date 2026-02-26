# Eating Lifestyle Profile Design

**Date:** 2026-02-26
**Status:** Approved

## Overview

Transform SousChefAI from a pantry tracker / recipe finder into a consumer-focused **eating lifestyle** app. The app builds a comprehensive profile of who the user is as an eater — health conditions, cooking attitudes, flavor preferences, budget, meal prep openness — and uses that profile to drive personalized recipe recommendations.

This is not a "healthy eating" app. It's an app that **understands how you want to eat** and helps you do it, whether that means heart-healthy meals, budget-friendly quick dinners, or adventurous weekend cooking projects.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Health data source | Self-reported conditions (checklist) | Avoids HIPAA entirely — no lab values, no medication tracking, no clinical data |
| Medication tracking | None — info note instead | Users told: "If you take medication for a condition, still mark it" |
| Profile UI | Single page with collapsible sections | Simple, discoverable, nothing required |
| Constraint model | Tiered: hard constraints + soft preferences | Allergies and strict health conditions enforced absolutely; everything else guides the AI |
| Flavor preferences | 1-5 slider scales for 6 dimensions | Gives the AI enough to match palates without overwhelming users |
| Re-confirmation | Gentle periodic nudge (60 days health, 90 days other) | Non-blocking banner on home page |
| Architecture | Extend existing models (new tables) | Builds on what exists, per-section `updated_at` for nudge timing |
| AI privacy | Translate conditions to dietary instructions in backend | AI never sees "user has hypertension" — only "prefer low-sodium" |

## Data Model

### New Tables

#### `health_conditions`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `user_id` | UUID | FK to users |
| `condition` | str(100) | Predefined condition key |
| `strictness` | str(20) | "gentle", "moderate", "strict" |
| `notes` | text | Optional user notes |
| `created_at` | datetime | |
| `updated_at` | datetime | For nudge timing |

Predefined conditions:
- `high_cholesterol`
- `hypertension`
- `type_2_diabetes`
- `pre_diabetes`
- `high_triglycerides`
- `heart_disease`
- `kidney_concerns`
- `gout`
- `iron_deficiency`
- `digestive_sensitivity`

#### `cooking_preferences` (one row per user)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `user_id` | UUID | FK to users, unique |
| `health_importance` | str(20) | "not_a_priority", "somewhat", "important", "very_important" |
| `cooking_attitude` | str(30) | "love_it", "its_fine", "necessary_evil", "hate_it" |
| `max_prep_time_minutes` | int | 15, 30, 45, 60, or null (no limit) |
| `skill_level` | str(20) | "beginner", "intermediate", "advanced" |
| `budget_sensitivity` | str(20) | "not_a_factor", "somewhat", "very_important" |
| `meal_prep_openness` | str(20) | "love_it", "sometimes", "no" |
| `updated_at` | datetime | For nudge timing |

#### `flavor_profiles` (one row per user)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `user_id` | UUID | FK to users, unique |
| `spice_tolerance` | int | 1-5 scale |
| `sweetness` | int | 1-5 scale |
| `savory_umami` | int | 1-5 scale |
| `adventurousness` | int | 1-5 scale |
| `richness` | int | 1-5 scale |
| `herb_forward` | int | 1-5 scale |
| `updated_at` | datetime | For nudge timing |

### Existing Tables — Unchanged

- **`dietary_preferences`** — allergies, intolerances, diets, dislikes, religious
- **`health_goals`** — action-oriented goals with targets (e.g., "lose 20 lbs", "train for marathon")

## Health Condition → Dietary Mapping

A backend lookup (`backend/app/services/health_mapping.py`) translates self-reported conditions into concrete dietary instructions. The AI never sees raw condition names.

| Condition | Avoid | Prefer | AI Note |
|-----------|-------|--------|---------|
| `high_cholesterol` | Saturated fat, trans fats, fried foods, fatty red meat, full-fat dairy | Lean proteins, fish, olive oil, nuts, oats, beans | Heart-healthy fats (omega-3) |
| `high_triglycerides` | Added sugars, refined carbs, sugary sauces | Whole grains, fatty fish, fiber-rich foods, vegetables | Minimize simple carbs |
| `hypertension` | High sodium, cured meats, heavy soy sauce, pickled foods | Fresh herbs, potassium-rich foods, DASH-diet friendly | Herbs and spices instead of salt |
| `type_2_diabetes` | High glycemic foods, refined sugars, white bread/rice | Low glycemic, whole grains, non-starchy vegetables, lean proteins | Balance carbs across meals |
| `pre_diabetes` | Refined carbs, sugary foods, large starchy portions | Whole grains, fiber, lean proteins, non-starchy vegetables | Same as diabetes, less strict |
| `heart_disease` | Saturated fats, trans fats, excess sodium, fried foods | Mediterranean-style, fish, vegetables, whole grains, olive oil | Combines cholesterol + hypertension |
| `kidney_concerns` | High potassium (if advanced), high phosphorus, excess protein, high sodium | Moderate portions, selected vegetables, rice, pasta | Guidance varies by stage |
| `gout` | Organ meats, red meat, shellfish, beer/alcohol, high-fructose | Low-fat dairy, cherries, vitamin C rich foods, vegetables | Reduce purine-rich foods |
| `iron_deficiency` | (none) | Iron-rich: red meat, spinach, lentils, fortified grains; pair with vitamin C | Absorption-enhancing combos |
| `digestive_sensitivity` | High-FODMAP (if IBS), very spicy, heavy cream, raw cruciferous | Cooked vegetables, gentle spices, easy-to-digest grains, lean proteins | Gentle on stomach |

## AI Prompt Structure

The `_build_recipe_prompt()` method gets restructured:

```
USER REQUEST: "{query}"

=== ABSOLUTE CONSTRAINTS (NEVER VIOLATE) ===
Allergies: [from dietary_preferences where type=allergy]
Religious: [from dietary_preferences where type=religious]
Strict health conditions: [translated dietary instructions for strict conditions]

=== HEALTH CONDITIONS (MODERATE - PREFER TO AVOID) ===
[translated dietary instructions for moderate conditions]

=== USER PROFILE ===
Healthy eating importance: {health_importance}
Cooking attitude: {cooking_attitude} → {mapped description}
Max prep+cook time: {max_prep_time_minutes} minutes
Skill level: {skill_level}
Budget: {budget_sensitivity} → {mapped description}
Meal prep: {meal_prep_openness}

=== FLAVOR PREFERENCES ===
Spice: {spice_tolerance}/5
Sweetness: {sweetness}/5
Savory/Umami: {savory_umami}/5
Adventurousness: {adventurousness}/5
Richness: {richness}/5
Herbs: {herb_forward}/5

=== SOFT PREFERENCES ===
Health goals: [from health_goals]
Gentle health conditions: [translated dietary instructions for gentle conditions]
Family dietary notes: [from family members]

=== AVAILABLE INGREDIENTS ===
[from household pantry]
```

## Profile UI

### Layout

Single scrollable page with collapsible sections:

1. **Profile header** — name, email, avatar, sign out
2. **Your Priorities** — health importance slider (master dial)
3. **Health Conditions** — checklist with strictness dropdowns, medication info note
4. **Cooking Style** — attitude, max time, skill level
5. **Budget & Meal Prep** — budget sensitivity, meal prep openness
6. **Flavor Profile** — 6 slider scales (1-5)
7. **Dietary Preferences** — existing section (unchanged)
8. **Health Goals** — existing section (unchanged)

### Behavior

- All sections collapsible, nothing required
- Auto-save on change (debounced for sliders)
- Section headers show completion (e.g., "Cooking Style (3/3 set)")
- Health conditions section shows medication info note and "Last reviewed" date

### Nudge Banner

Non-blocking banner on HomeView when profile sections are stale:

- Health conditions: nudge at 60 days since `updated_at`
- All other sections: nudge at 90 days since `updated_at`
- "Yes, all good" resets timer
- "Review it" navigates to profile
- Dismiss button (auto-dismisses after 3 days, timer NOT reset)

## Changes Summary

| Area | What Changes |
|------|-------------|
| New models | `HealthCondition`, `CookingPreferences`, `FlavorProfile` |
| New backend | `app/services/health_mapping.py` — condition-to-dietary translation |
| New API endpoints | CRUD for health conditions, cooking prefs, flavor profile |
| Modified backend | `app/services/ai/base.py` — restructured prompt builder |
| Modified frontend | `ProfileView.vue` — redesigned with collapsible sections |
| New frontend component | Nudge banner on HomeView |
| Database migration | Alembic migration for 3 new tables |
| Existing tables | `dietary_preferences` and `health_goals` unchanged |
