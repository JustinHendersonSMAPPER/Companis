import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("@/views/HomeView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/LoginView.vue"),
    },
    {
      path: "/register",
      name: "register",
      component: () => import("@/views/RegisterView.vue"),
    },
    {
      path: "/oauth/callback/:provider",
      name: "oauth-callback",
      component: () => import("@/views/OAuthCallbackView.vue"),
    },
    {
      path: "/ingredients",
      name: "ingredients",
      component: () => import("@/views/IngredientsView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/scan",
      name: "scan",
      component: () => import("@/views/ScanView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/recipes",
      name: "recipes",
      component: () => import("@/views/RecipesView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/recipes/:id",
      name: "recipe-detail",
      component: () => import("@/views/RecipeDetailView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/shopping",
      name: "shopping",
      component: () => import("@/views/ShoppingView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/household",
      name: "household",
      component: () => import("@/views/HouseholdView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/profile",
      name: "profile",
      component: () => import("@/views/ProfileView.vue"),
      meta: { requiresAuth: true },
    },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem("access_token");
  if (to.meta.requiresAuth && !token) {
    return { name: "login" };
  }
  return true;
});

export default router;
