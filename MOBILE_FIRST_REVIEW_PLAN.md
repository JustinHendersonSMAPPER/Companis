# Companis Mobile-First UI Review & Implementation Plan

## Expert Team Review Summary

This plan synthesizes findings from a multi-expert review team:

- **UX Expert** - UI patterns, accessibility, responsive design
- **Mobile App Expert** - Capacitor integration, native features, platform readiness
- **Consumer/User Agent** - User journey, feature gaps, competitive analysis
- **Database Expert** - Schema design, performance, scalability
- **E2E Testing Researcher** - Test infrastructure, emulator testing, CI/CD

---

## Executive Assessment: Is Companis Mobile-First?

**Verdict: Partially.** The app has a solid mobile-first *foundation* but critical gaps prevent it from being production-ready as a mobile app.

### What's Working
- Bottom tab navigation (NavBar) is a correct mobile pattern
- Safe area CSS variables (`env(safe-area-inset-*)`) properly handle notched devices
- `viewport-fit=cover` configured in index.html
- Capacitor 6 installed with Camera plugin
- Lazy route loading via dynamic imports reduces initial bundle
- System font stack avoids custom font loading delays
- Vue 3 + Pinia stores are lightweight and efficient
- SQLAlchemy async sessions with proper commit/rollback lifecycle
- UUID primary keys ready for distributed/offline sync scenarios

### What's Broken or Missing
- **Zero `@media` queries** - layout doesn't adapt to tablet/desktop at all
- **No Capacitor plugins initialized** - StatusBar, Keyboard, Haptics installed but never imported or used
- **No ARIA attributes** - navigation, buttons, and forms lack accessibility labels
- **No app lifecycle handlers** - no back button, pause/resume, or deep linking
- **No offline support** - no service worker, no local caching, no sync queue
- **No onboarding flow** - users land on empty home after signup
- **No recipe images** - critical gap for a food app
- **No meal planning** - expected core feature, no database table or UI
- **No Alembic migrations** - `alembic/versions/` directory is empty
- **Touch targets too small** - NavBar padding only `0.25rem 0.5rem` (needs 44px minimum)
- **Profile/settings hidden** - no direct nav access

---

## Phase 1: Critical Foundation Fixes (Week 1-2)

These are blockers that must be resolved before any feature work.

### 1.1 Responsive Design System

**Problem**: Zero `@media` queries in the entire codebase. Mobile layout is forced on all screen sizes.

**Changes**:

| File | Change |
|------|--------|
| `frontend/src/App.vue` | Add responsive breakpoint system (768px tablet, 1024px desktop, 1200px large) |
| `frontend/src/components/common/NavBar.vue` | Bottom nav on mobile, horizontal top nav on tablet+. Increase touch targets to 44px minimum |
| All view components | Add tablet 2-column grid layouts, desktop max-width constraints |

**Implementation**:
```
Mobile (< 768px):    Single column, bottom nav, full-width cards
Tablet (768-1024px): 2-column grid, side nav or top nav, card grid
Desktop (> 1024px):  3-column grid, sidebar nav, max-width 1200px container
```

### 1.2 Accessibility Overhaul

**Problem**: No ARIA attributes anywhere. Emoji icons without labels. Form validation not linked to inputs.

**Changes**:

| File | Change |
|------|--------|
| `NavBar.vue` | Add `aria-label` to all nav links, `aria-current="page"` for active route |
| All icon-only buttons | Add `aria-label` (remove buttons, voice toggle, star ratings) |
| `LoginView.vue`, `RegisterView.vue` | Add `autocomplete` attributes (email, password, name) |
| All forms | Add `aria-describedby` linking error messages to inputs, `aria-required` on required fields |
| `RecipesView.vue` | Add `aria-selected` on tab buttons |
| `ShoppingView.vue` | Replace text `[x]`/`[ ]` with proper `<input type="checkbox">` |

### 1.3 Capacitor Plugin Initialization

**Problem**: StatusBar, Keyboard, Haptics plugins installed but never imported or used anywhere.

**Changes**:

| File | Change |
|------|--------|
| `frontend/src/main.ts` | Initialize Capacitor plugins on app mount (StatusBar color/style, Keyboard resize mode) |
| `frontend/src/services/platformService.ts` | NEW - Platform detection utilities (`isNative()`, `isPlatform()`) |
| `frontend/src/services/capacitorLifecycle.ts` | NEW - App lifecycle handlers (back button, pause/resume, deep linking) |
| `frontend/src/views/ScanView.vue` | Replace `navigator.mediaDevices` with Capacitor Camera plugin + web fallback |

### 1.4 Database Migration Bootstrap

**Problem**: `alembic/versions/` is empty. No migration history. Schema created implicitly on startup.

**Changes**:

| File | Change |
|------|--------|
| `backend/alembic/versions/` | Generate initial migration from current models |
| `backend/app/main.py` | Remove implicit `init_db()` table creation from startup lifespan |
| `backend/app/models/recipe.py` | Add composite index on `(recipe_id, user_id)` for RecipeRating |
| `backend/app/models/recipe.py` | Add `UniqueConstraint('recipe_id', 'user_id')` on UserFavorite |
| `backend/app/models/household.py` | Add `UniqueConstraint('household_id', 'user_id')` on FamilyMember |
| Multiple models | Add `index=True` to `household_id` foreign keys in child tables |
| `backend/app/models/shopping.py` | Add `index=True` to `is_purchased` column |

### 1.5 Color Contrast & Typography

**Problem**: `--text-secondary: #757575` is borderline WCAG AA on white. Small text (0.7rem) too small.

**Changes**:

| File | Change |
|------|--------|
| `frontend/src/App.vue` | Darken `--text-secondary` to `#616161` for 5.5:1 contrast. Set explicit `line-height: 1.5` on body |
| Multiple views | Increase minimum font size from 0.7rem to 0.8125rem (13px) for all readable text |
| `RecipeDetailView.vue` | Status badges: increase from 0.7rem to 0.8125rem |
| `HomeView.vue` | Chip text: increase from 0.75rem to 0.8125rem |

---

## Phase 2: User Experience & Core Features (Week 3-5)

### 2.1 Onboarding Wizard

**Problem**: After registration, users land on empty home with no guidance. Must manually find profile settings.

**Cross-team note**: The database already has DietaryPreference, HealthGoal, and Household models - the onboarding just needs to collect this data.

**New files**:

| File | Purpose |
|------|---------|
| `frontend/src/views/OnboardingView.vue` | 5-step post-signup wizard |
| `frontend/src/components/onboarding/DietaryStep.vue` | Dietary restrictions (allergy/intolerance/diet) with preset quick-picks |
| `frontend/src/components/onboarding/HealthGoalsStep.vue` | Health goal selection |
| `frontend/src/components/onboarding/HouseholdStep.vue` | Add family members |
| `frontend/src/components/onboarding/PantryStep.vue` | Quick-add common pantry staples |
| `frontend/src/components/onboarding/WelcomeStep.vue` | App introduction and explanation |
| `frontend/src/stores/onboarding.ts` | Wizard state management |

**Modified files**:

| File | Change |
|------|--------|
| `frontend/src/router/index.ts` | Add `/onboarding` route, redirect new users after registration |
| `frontend/src/views/RegisterView.vue` | Redirect to `/onboarding` instead of `/` after signup |

**Steps**: Welcome -> Dietary Restrictions -> Health Goals -> Household -> Initial Pantry. Each step skippable. Progress indicator shown.

### 2.2 Profile Accessibility

**Problem**: Profile and Household pages have no direct navigation link. Users can't find settings.

**Changes**:

| File | Change |
|------|--------|
| `frontend/src/components/common/NavBar.vue` | Add user avatar/icon to header area with dropdown menu |
| `frontend/src/components/common/UserMenu.vue` | NEW - Avatar dropdown with Profile, Household, Settings, Logout |
| `frontend/src/App.vue` | Add header bar above main content for user menu placement |

### 2.3 Recipe Detail Improvements

**Problem**: No images, instructions as raw text block, no nutrition info, no step-by-step cooking mode.

**Changes**:

| File | Change |
|------|--------|
| `frontend/src/views/RecipeDetailView.vue` | Display `image_url` with fallback placeholder. Format instructions into numbered steps. Show `calorie_estimate` and nutrition data. Add ingredient substitution display |
| `frontend/src/components/recipes/InstructionSteps.vue` | NEW - Parses instruction text into interactive numbered steps with checkbox completion |
| `frontend/src/components/recipes/NutritionCard.vue` | NEW - Displays calorie/nutrition summary |
| `frontend/src/components/common/Toast.vue` | NEW - Success/error toast notifications for favorites, ratings, cart additions |
| `frontend/src/stores/notifications.ts` | NEW - Toast notification state management |

### 2.4 Recipe Search Enhancements

**Problem**: Dietary filters sent to API but not visible in UI. Duplicate search on Home and Recipes pages. No sorting.

**Changes**:

| File | Change |
|------|--------|
| `frontend/src/views/HomeView.vue` | Add dietary filter chips (Vegetarian, Vegan, Gluten-Free, etc.) above search. Show result count. Add sort dropdown |
| `frontend/src/views/RecipesView.vue` | Remove duplicate search; focus on browse/discover with filter sidebar on tablet+ |
| `frontend/src/components/recipes/DietaryFilterChips.vue` | NEW - Reusable dietary filter chip group |
| `frontend/src/components/recipes/RecipeCard.vue` | NEW - Extracted recipe card component with image support, consistent across Home and Recipes |

### 2.5 Optimize Recipe Detail Queries

**Problem**: Recipe detail endpoint makes 4 separate database queries (recipe, avg rating, user rating, is_favorite). N+1 risk.

**Changes**:

| File | Change |
|------|--------|
| `backend/app/api/recipes.py` | Combine recipe + avg rating + user rating + favorite status into single query with joins |

---

## Phase 3: Mobile Native Features (Week 5-7)

### 3.1 Offline Support

**Problem**: No service worker, no data caching, no offline capability. Every action requires network.

**New files**:

| File | Purpose |
|------|---------|
| `frontend/public/service-worker.js` | Cache app shell and static assets for offline loading |
| `frontend/src/services/offlineService.ts` | IndexedDB via Dexie for local recipe/ingredient caching |
| `frontend/src/services/syncService.ts` | Queue offline mutations and sync when reconnected |
| `frontend/src/composables/useNetworkStatus.ts` | Reactive online/offline detection with UI indicator |

**Modified files**:

| File | Change |
|------|--------|
| `frontend/src/main.ts` | Register service worker |
| `frontend/src/App.vue` | Show offline indicator banner when disconnected |
| `frontend/src/stores/recipes.ts` | Cache fetched recipes to IndexedDB |
| `frontend/src/stores/ingredients.ts` | Cache ingredient list to IndexedDB |

### 3.2 Gesture Support

**Problem**: No swipe, pull-to-refresh, or long-press gestures. Basic tap-only interaction.

**New files**:

| File | Purpose |
|------|---------|
| `frontend/src/components/common/PullToRefresh.vue` | Pull-down refresh wrapper for list views |
| `frontend/src/composables/useSwipeNavigation.ts` | Swipe-right-to-go-back on iOS |

**Modified files**:

| File | Change |
|------|--------|
| `frontend/src/views/IngredientsView.vue` | Add pull-to-refresh, swipe-to-delete on ingredient items |
| `frontend/src/views/RecipesView.vue` | Add pull-to-refresh on recipe list |
| `frontend/src/views/ShoppingView.vue` | Swipe-to-complete on shopping items |

### 3.3 Mobile Security Hardening

**Problem**: Auth tokens stored in localStorage (insecure on native). No PKCE for OAuth.

**Changes**:

| File | Change |
|------|--------|
| `frontend/src/services/secureStorage.ts` | NEW - Capacitor Secure Storage wrapper with localStorage fallback for web |
| `frontend/src/services/api.ts` | Use secure storage for tokens instead of localStorage |
| `frontend/src/services/auth.ts` | Implement PKCE flow for OAuth on native platforms |

**New dependency**: `@capacitor-community/secure-storage-plugin`

### 3.4 App Store Preparation

**Problem**: No icons, splash screens, or app metadata. Not store-ready.

**New files/directories**:

| Path | Purpose |
|------|---------|
| `frontend/resources/icon.png` | Source icon (1024x1024) for auto-generation |
| `frontend/resources/splash.png` | Source splash screen for auto-generation |
| `frontend/scripts/generate-icons.sh` | ImageMagick script to generate all platform icon sizes |
| Capacitor `android/` and `ios/` | Generated platform directories (via `npx cap add`) |

**Modified files**:

| File | Change |
|------|--------|
| `frontend/capacitor.config.ts` | Add SplashScreen, StatusBar, Keyboard plugin configs. Add iOS and Android specific settings |
| `frontend/package.json` | Add `cap:sync`, `cap:open:android`, `cap:open:ios`, `cap:build:*` scripts |

---

## Phase 4: Meal Planning & Engagement (Week 7-9)

### 4.1 Meal Planning Feature

**Cross-team note**: Database expert confirmed no meal plan table exists. Consumer agent identified this as the #1 missing competitive feature.

**Database changes**:

| File | Change |
|------|--------|
| `backend/app/models/meal_plan.py` | NEW - MealPlan model (household_id, meal_date, meal_type, recipe_id, servings, notes) |
| `backend/app/api/meal_plan.py` | NEW - CRUD endpoints for meal plan management |
| `backend/app/services/meal_plan.py` | NEW - Meal plan service with auto-shopping-list generation |
| `backend/alembic/versions/` | New migration for meal_plan table |

**Frontend changes**:

| File | Change |
|------|---------|
| `frontend/src/views/MealPlanView.vue` | NEW - Weekly calendar view with drag-drop recipe assignment |
| `frontend/src/stores/mealplan.ts` | NEW - Meal plan state management |
| `frontend/src/router/index.ts` | Add `/meal-plan` route |
| `frontend/src/components/common/NavBar.vue` | Add meal plan to navigation (replace or reorganize 5 tabs) |

### 4.2 Cooking History

**Database changes**:

| File | Change |
|------|--------|
| `backend/app/models/cooking_history.py` | NEW - CookingHistory model (user_id, recipe_id, cooked_date, notes) |
| `backend/alembic/versions/` | New migration |

**Frontend changes**:

| File | Change |
|------|--------|
| `frontend/src/views/RecipeDetailView.vue` | Add "I cooked this" button with date logging |
| `frontend/src/views/ProfileView.vue` | Show cooking history summary |

### 4.3 Recipe Collections

**Problem**: Favorites are a flat list with no organization.

**Database changes**:

| File | Change |
|------|--------|
| `backend/app/models/recipe.py` | Add RecipeCollection model with many-to-many to recipes |
| `backend/alembic/versions/` | New migration |

**Frontend changes**:

| File | Change |
|------|--------|
| `frontend/src/views/RecipesView.vue` | Favorites tab → Collections view with folders/tags |

---

## Phase 5: Comprehensive E2E Testing Framework (Parallel Track)

This phase runs in parallel with Phases 1-4.

### 5.1 Fix & Enhance Existing Playwright Setup

**Problem**: Only Chromium configured. No mobile viewports. Mismatched ports (5173 vs 6001).

**Changes**:

| File | Change |
|------|--------|
| `frontend/playwright.config.ts` | Fix baseURL to `localhost:6001`. Add Firefox, WebKit projects. Add mobile viewports (Pixel 5, iPhone 12, iPad). Enable video recording on failure. Add JUnit + JSON reporters |

**Updated Playwright projects**:
```
Desktop: Chromium, Firefox, WebKit
Mobile:  Pixel 5 (Chrome), iPhone 12 (Safari)
Tablet:  iPad (gen 7)
```

### 5.2 Full Live Development Environment Testing

**Problem**: Need backend + frontend + database running together for realistic E2E tests.

**New files**:

| File | Purpose |
|------|---------|
| `docker-compose.test.yml` | Dedicated test environment with isolated test database, backend, and frontend containers |
| `backend/tests/fixtures/seed_data.py` | Realistic test data seeding (users, recipes, ingredients, households) |
| `frontend/e2e/fixtures/test-users.ts` | Test user credentials and expected data |
| `frontend/e2e/helpers/api-setup.ts` | Helper to seed test data via API before E2E runs |

**Modified files**:

| File | Change |
|------|--------|
| `frontend/playwright.config.ts` | webServer section updated to use docker-compose.test.yml for CI, local dev servers for development |
| `frontend/package.json` | Add `test:e2e:docker` script |

### 5.3 Android Emulator E2E Testing

**Approach**: Appium + WebDriverIO for Capacitor Android app testing.

**New files**:

| File | Purpose |
|------|---------|
| `frontend/wdio.android.conf.js` | WebDriverIO config for Android emulator (UiAutomator2 driver, com.companis.app package) |
| `frontend/e2e/android/login.spec.ts` | Android login flow test |
| `frontend/e2e/android/camera-permissions.spec.ts` | Camera permission handling test |
| `frontend/e2e/android/navigation.spec.ts` | Native navigation and back button test |
| `frontend/e2e/android/offline.spec.ts` | Offline mode behavior test |

**New dependencies**: `appium`, `webdriverio`, `@wdio/cli`, `@wdio/mocha-framework`

**New scripts**:
```json
{
  "android:build": "npm run build && npx cap sync android && cd android && ./gradlew assembleDebug",
  "android:test": "npm run android:build && wdio run wdio.android.conf.js"
}
```

**Requirements**: Android SDK, Android emulator (Pixel 5 API 34), Appium server

### 5.4 iOS Simulator E2E Testing

**Approach**: XCUITest via Xcode for native iOS testing + Detox as alternative.

**New files**:

| File | Purpose |
|------|---------|
| `frontend/e2e/ios/LoginUITests.swift` | XCUITest login flow |
| `frontend/e2e/ios/CameraPermissionTests.swift` | Camera permission handling |
| `frontend/e2e/ios/NavigationTests.swift` | Navigation and gestures |
| `frontend/.detoxrc.js` | Detox configuration (alternative to XCUITest) |

**New scripts**:
```json
{
  "ios:build": "npm run build && npx cap sync ios",
  "ios:test": "xcodebuild test -workspace ios/App/App.xcworkspace -scheme App -destination 'platform=iOS Simulator,name=iPhone 15'"
}
```

**Requirements**: macOS, Xcode, iOS Simulator (iPhone 15)

### 5.5 Browser Emulation Testing

Already covered by Playwright mobile device emulation in 5.1, but additional:

**New files**:

| File | Purpose |
|------|---------|
| `frontend/e2e/visual-regression.spec.ts` | Screenshot comparison tests for all pages across viewports |
| `frontend/e2e/accessibility.spec.ts` | axe-core accessibility audit on every page |
| `frontend/e2e/network-conditions.spec.ts` | Slow network, offline, and network failure tests |
| `frontend/e2e/performance.spec.ts` | Lighthouse CI integration for performance budgets |

**New dependency**: `@axe-core/playwright`

### 5.6 CI/CD Pipeline

**New files**:

| File | Purpose |
|------|---------|
| `.github/workflows/test.yml` | Comprehensive CI pipeline |

**Pipeline jobs**:

```
backend-unit-tests:      pytest tests/unit/ + ruff + pyright
backend-integration:     pytest tests/integration/
frontend-unit-tests:     vitest + eslint + vue-tsc
frontend-e2e-browsers:   Playwright (Chromium, Firefox, WebKit)
frontend-e2e-mobile:     Playwright (Pixel 5, iPhone 12 viewports)
android-e2e:             Appium on Android emulator (scheduled, not every PR)
ios-e2e:                 XCUITest on iOS simulator (macOS runner, scheduled)
visual-regression:       Playwright screenshot comparison
accessibility-audit:     axe-core scan
```

**Test reporting**: HTML reports uploaded as artifacts. JUnit XML for PR status checks. Slack webhook for failures.

---

## Phase 6: Production Readiness (Week 9-10)

### 6.1 PostgreSQL Migration

**Problem**: SQLite has file-level write locks. Multiple concurrent mobile users will deadlock.

**Changes**:

| File | Change |
|------|--------|
| `backend/app/config.py` | Add PostgreSQL connection string option alongside SQLite |
| `backend/app/database.py` | Add connection pooling config (`pool_size=20, max_overflow=40, pool_pre_ping=True`) |
| `docker-compose.yml` | Add PostgreSQL service container |
| `backend/alembic/env.py` | Support both SQLite and PostgreSQL |

### 6.2 Soft Deletes for Mobile Sync

**Problem**: Hard deletes via CASCADE prevent offline sync conflict resolution.

**Changes**:

| File | Change |
|------|--------|
| All models | Add `deleted_at: Optional[datetime]` column (nullable). Filter out deleted records in queries |
| `backend/app/models/base.py` | NEW - SoftDeleteMixin with `deleted_at` field and `is_deleted` property |

### 6.3 API Query Optimization

**Changes**:

| File | Change |
|------|--------|
| `backend/app/api/recipes.py` | Combine 4 queries into 1 joined query for recipe detail |
| `backend/app/api/ingredients.py` | Add pagination (limit/offset) for large ingredient lists |
| `backend/app/api/recipes.py` | Add pagination for recipe search results |

---

## Testing Strategy Summary

| Layer | Tool | Scope | When |
|-------|------|-------|------|
| Backend Unit | pytest | Models, services, utils | Every commit |
| Backend Integration | pytest + httpx | API endpoints with test DB | Every PR |
| Frontend Unit | Vitest + Vue Test Utils | Components, stores, services | Every commit |
| Frontend E2E (Desktop) | Playwright | Full flows in Chrome, Firefox, Safari | Every PR |
| Frontend E2E (Mobile Viewport) | Playwright | Pixel 5, iPhone 12 emulation in browser | Every PR |
| Visual Regression | Playwright screenshots | All pages, all viewports | Every PR |
| Accessibility | axe-core + Playwright | WCAG AA compliance scan | Every PR |
| Android Native | Appium + WebDriverIO | Native app on Android emulator | Nightly/Release |
| iOS Native | XCUITest/Detox | Native app on iOS simulator | Nightly/Release |
| Performance | Lighthouse CI | Core Web Vitals budgets | Weekly/Release |
| Full Stack | docker-compose.test.yml | Backend + Frontend + DB integration | Release |

---

## Implementation Timeline

```
Week 1-2:  Phase 1 - Critical Foundation (responsive, a11y, Capacitor init, DB migrations)
Week 3-5:  Phase 2 - UX & Core Features (onboarding, recipe improvements, search)
           Phase 5.1-5.2 - Testing foundation (Playwright enhancement, docker test env)
Week 5-7:  Phase 3 - Mobile Native (offline, gestures, security, app store prep)
           Phase 5.3-5.4 - Native testing (Android Appium, iOS XCUITest)
Week 7-9:  Phase 4 - Engagement Features (meal planning, cooking history, collections)
           Phase 5.5-5.6 - Testing polish (visual regression, CI/CD pipeline)
Week 9-10: Phase 6 - Production Readiness (PostgreSQL, soft deletes, query optimization)
```

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| SQLite write locks in production | HIGH | Phase 6.1 PostgreSQL migration |
| No migrations = schema drift | HIGH | Phase 1.4 bootstrap Alembic |
| Accessibility lawsuits (ADA) | HIGH | Phase 1.2 ARIA overhaul |
| iOS App Store rejection (missing metadata) | MEDIUM | Phase 3.4 app store prep |
| Offline data loss | MEDIUM | Phase 3.1 offline + Phase 6.2 soft deletes |
| Poor mobile UX = low retention | MEDIUM | Phase 2.1 onboarding + Phase 2.3 recipe improvements |
| Flaky E2E tests slow development | LOW | Phase 5.6 retry strategies + test isolation |

---

## Decision Points for Your Review

1. **Navigation restructure**: Adding meal planning means 6 nav items. Should we use a "More" tab, reorganize to 5 items (combine Pantry+Scan), or use a drawer?

2. **PostgreSQL timing**: Should we migrate to PostgreSQL earlier (Phase 1) or keep SQLite through development and migrate at production?

3. **Native testing priority**: Android emulator and iOS simulator testing requires significant setup. Should we prioritize Playwright mobile viewport emulation first and defer native testing to a later milestone?

4. **Offline scope**: Full offline with IndexedDB sync queue is complex. Should we start with read-only offline cache (view cached recipes/ingredients when offline) and add write sync later?

5. **Onboarding depth**: 5-step wizard vs. a simpler 2-step (dietary restrictions + health goals only) with progressive profiling over time?
