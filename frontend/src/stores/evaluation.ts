import { defineStore } from "pinia";
import { ref } from "vue";
import { getEvaluationCase, listEvaluationCases } from "@/services/evaluation";
import type {
  EvaluationCaseDetailResponse,
  EvaluationCaseSummary,
  EvaluationProtoSceneId,
} from "@/types/api";

const TIMEOUT_CASE_ID = "eval-meeting-timeout";

export const useEvaluationStore = defineStore("evaluation", () => {
  const items = ref<EvaluationCaseSummary[]>([]);
  const total = ref(0);
  const selected = ref<EvaluationCaseDetailResponse | null>(null);
  const protoScene = ref<EvaluationProtoSceneId>("cases");
  const loading = ref(false);

  async function loadList(): Promise<void> {
    const data = await listEvaluationCases();
    items.value = data.items;
    total.value = data.total;
  }

  async function selectCase(caseId: string): Promise<void> {
    selected.value = await getEvaluationCase(caseId);
    if (protoScene.value !== "cases-empty") {
      protoScene.value = caseId === TIMEOUT_CASE_ID ? "case-timeout" : "cases";
    }
  }

  async function applyScene(scene: EvaluationProtoSceneId): Promise<void> {
    protoScene.value = scene;
    if (scene === "cases-empty") {
      selected.value = null;
      return;
    }
    const caseId = scene === "case-timeout" ? TIMEOUT_CASE_ID : items.value[0]?.case_id;
    if (caseId) {
      selected.value = await getEvaluationCase(caseId);
    }
  }

  async function bootstrap(scene: EvaluationProtoSceneId): Promise<void> {
    loading.value = true;
    try {
      await loadList();
      await applyScene(scene);
    } finally {
      loading.value = false;
    }
  }

  return {
    items,
    total,
    selected,
    protoScene,
    loading,
    loadList,
    selectCase,
    applyScene,
    bootstrap,
  };
});
