<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useEvaluationStore } from "@/stores/evaluation";
import {
  EVALUATION_SCENE_OPTIONS,
  evaluationBadCaseLabel,
  evaluationRouteLabel,
} from "@/utils/copy";
import type { EvaluationCaseSummary, EvaluationProtoSceneId } from "@/types/api";

const store = useEvaluationStore();
const route = useRoute();
const router = useRouter();

function sceneFromHash(hash: string): EvaluationProtoSceneId {
  const id = hash.replace(/^#/, "");
  if (id === "cases-empty" || id === "case-timeout" || id === "cases") return id;
  return "cases";
}

const selectedId = computed(() => store.selected?.case.case_id ?? null);
const isEmpty = computed(() => store.protoScene === "cases-empty");
const comparison = computed(() => store.selected?.route_comparison ?? null);
const replayEvents = computed(() => store.selected?.case.trace_events ?? []);

function setHash(scene: EvaluationProtoSceneId): void {
  if (route.hash === `#${scene}`) return;
  void router.replace({ hash: `#${scene}` });
}

function onSceneChange(event: Event): void {
  const scene = (event.target as HTMLSelectElement).value as EvaluationProtoSceneId;
  setHash(scene);
  void store.applyScene(scene);
}

function onRowActivate(item: EvaluationCaseSummary): void {
  void store.selectCase(item.case_id);
  setHash(item.case_id === "eval-meeting-timeout" ? "case-timeout" : "cases");
}

function onRowKeydown(event: KeyboardEvent, item: EvaluationCaseSummary): void {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    onRowActivate(item);
  }
}

onMounted(() => {
  document.title = "Demo Validation · 非产品功能";
  void store.bootstrap(sceneFromHash(route.hash));
});

watch(
  () => route.hash,
  (hash) => {
    const scene = sceneFromHash(hash);
    if (scene !== store.protoScene) {
      void store.applyScene(scene);
    }
  },
);
</script>

<template>
  <div>
    <div class="proto-bar">
      <span>原型场景切换（非产品功能）</span>
      <select aria-label="选择原型场景" :value="store.protoScene" @change="onSceneChange">
        <option v-for="item in EVALUATION_SCENE_OPTIONS" :key="item.id" :value="item.id">
          {{ item.label }}
        </option>
      </select>
      <a href="/">返回员工工作台</a>
    </div>
    <div class="demo-banner">Demo Validation / 非产品功能 · 不是员工工作台，不出现在员工导航</div>
    <div class="demo-page">
      <div v-if="isEmpty" class="empty-hint">暂无预置案例。不得伪造通过率。</div>
      <template v-else>
        <h2 class="demo-title">案例验证台</h2>
        <p class="brand-sub demo-lead">仅供面试演示核对路由。员工产品不包含本页。</p>
        <table class="data-table">
          <thead>
            <tr>
              <th>案例</th>
              <th>预期路由</th>
              <th>实际路由</th>
              <th>结果</th>
              <th>分类</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in store.items"
              :key="item.case_id"
              :class="{ selected: item.case_id === selectedId }"
              tabindex="0"
              @click="onRowActivate(item)"
              @keydown="onRowKeydown($event, item)"
            >
              <td>{{ item.name }}</td>
              <td>{{ evaluationRouteLabel(item.expected_route) }}</td>
              <td>{{ evaluationRouteLabel(item.actual_route) }}</td>
              <td>
                <span class="tag" :class="item.passed ? 'tag-ok' : 'tag-fail'">
                  {{ item.passed ? "通过" : "不通过" }}
                </span>
              </td>
              <td>{{ evaluationBadCaseLabel(item.bad_case_category) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="comparison" class="room-grid demo-compare">
          <div class="bubble-ai demo-card">
            <strong>路由对照</strong>
            <p>
              预期：{{ evaluationRouteLabel(comparison.expected_route) }}<br />
              实际：{{ evaluationRouteLabel(comparison.actual_route) }}
            </p>
          </div>
          <div class="bubble-ai demo-card">
            <strong>事件流回放</strong>
            <p v-for="item in replayEvents" :key="item.event_id">· {{ item.title_zh }}</p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
