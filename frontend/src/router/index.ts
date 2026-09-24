import { createRouter, createWebHistory } from "vue-router";
import DemoEvaluationPage from "@/pages/DemoEvaluationPage.vue";
import WorkbenchPage from "@/pages/WorkbenchPage.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "workbench",
      component: WorkbenchPage,
    },
    {
      path: "/demo/evaluation",
      name: "demo-evaluation",
      component: DemoEvaluationPage,
      meta: { isDemoValidation: true },
    },
  ],
});

router.beforeEach((_to, _from, next) => {
  next();
});

export default router;
