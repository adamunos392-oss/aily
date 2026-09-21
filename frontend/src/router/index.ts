import { createRouter, createWebHistory } from "vue-router";
import WorkbenchPage from "@/pages/WorkbenchPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "workbench",
      component: WorkbenchPage,
    },
  ],
});

router.beforeEach((_to, _from, next) => {
  next();
});

export default router;
