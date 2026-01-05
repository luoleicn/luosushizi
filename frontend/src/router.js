import { createRouter, createWebHistory } from "vue-router";

import LoginPage from "./pages/LoginPage.vue";
import InputPage from "./pages/InputPage.vue";
import StudyPage from "./pages/StudyPage.vue";
import StatsPage from "./pages/StatsPage.vue";
import { getAuthState, refreshAuth } from "./store/auth";

const routes = [
  { path: "/", redirect: "/study" },
  { path: "/login", component: LoginPage },
  { path: "/input", component: InputPage },
  { path: "/study", component: StudyPage },
  { path: "/stats", component: StatsPage },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  refreshAuth();
  const { token } = getAuthState();
  if (!token && to.path !== "/login") {
    return "/login";
  }
  if (token && to.path === "/login") {
    return "/study";
  }
  return true;
});

export default router;
