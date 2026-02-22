# SousChefAI Frontend

Vue 3 SPA with TypeScript, Pinia, and Capacitor for mobile.

## Tech Stack

- **Framework**: Vue 3 (Composition API, `<script setup>`)
- **Build**: Vite 6
- **Language**: TypeScript 5.7
- **State**: Pinia
- **Routing**: Vue Router 4
- **HTTP**: Axios
- **Mobile**: Capacitor 6 (iOS/Android)
- **Testing**: Vitest (unit), Playwright (E2E)
- **Linting**: ESLint with vue + typescript plugins

## Project Structure

```
src/
  App.vue              # Root component
  main.ts              # App bootstrap
  router/index.ts      # Route definitions
  services/api.ts      # Axios client with auth interceptors
  stores/              # Pinia stores
    auth.ts, ingredients.ts, recipes.ts, shopping.ts
  views/               # Page components
    HomeView, LoginView, RegisterView, IngredientsView,
    RecipesView, RecipeDetailView, ShoppingView,
    HouseholdView, ProfileView, ScanView, OAuthCallbackView
  components/common/   # Reusable components
  types/               # TypeScript interfaces
  __tests__/           # Top-level test helpers
```

## Component Patterns

- All components use `<script setup lang="ts">` (Composition API)
- Single File Components (`.vue`)
- Path alias: `@` maps to `src/`

## State Management (Pinia)

Stores in `src/stores/` use `defineStore` with setup syntax. Each store handles its own API calls and state. Available stores: `auth`, `ingredients`, `recipes`, `shopping`.

## API Layer

`src/services/api.ts` creates an Axios instance with `baseURL: "/api"`. The Vite dev server proxies `/api` to `http://localhost:6000`. Features:
- Auto-attaches JWT from `localStorage` to requests
- Auto-refreshes expired tokens (401 interceptor)
- Typed API functions grouped by domain: `authApi`, `usersApi`, `ingredientsApi`, `recipesApi`, `householdApi`, `shoppingApi`, `aiApi`

## Mobile (Capacitor)

Config in `capacitor.config.ts`. App ID: `com.souschefai.app`. Uses Camera plugin for ingredient scanning.

```bash
npm run build                      # build web assets
npx cap add android                # add platform
npx cap add ios
npx cap sync                       # sync web assets to native
npx cap open android               # open in Android Studio
npx cap open ios                   # open in Xcode
```

## Commands

```bash
# Development
npm run dev                        # dev server on port 6001

# Build
npm run build                      # type-check + production build
npm run preview                    # preview production build

# Tests
npm test                           # vitest unit tests
npm run test:watch                 # vitest in watch mode
npm run test:coverage              # unit tests with coverage
npm run test:e2e                   # playwright E2E tests
npm run test:e2e:headed            # E2E with visible browser
npm run test:e2e:ui                # playwright UI mode

# Linting
npm run lint                       # eslint --fix
npm run lint:check                 # eslint (no fix)
npm run type-check                 # vue-tsc type check
```
