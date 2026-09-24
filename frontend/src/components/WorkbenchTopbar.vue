<script setup lang="ts">
import DemoControl from "@/components/DemoControl.vue";
import type { IdentityResponse } from "@/types/api";
import { withBase } from "@/utils/baseUrl";
import { DEMO_SCENE_OPTIONS } from "@/utils/copy";
import { isMockEnabled } from "@/utils/mockFlag";

defineProps<{
  identity: IdentityResponse | null;
  sceneId: string;
}>();

const emit = defineEmits<{
  scene: [id: string];
}>();
</script>

<template>
  <header class="topbar">
    <div class="brand">
      <span class="brand-mark">A</span>
      <span class="brand-name">Aily</span>
      <span class="brand-sub">企业智能助手</span>
    </div>
    <div class="topbar-right">
      <span class="env-badge">Demo Environment · Mock Data</span>
      <DemoControl
        :scene-id="sceneId"
        :options="DEMO_SCENE_OPTIONS"
        :scene-disabled="!isMockEnabled()"
        :link-href="withBase('demo/evaluation')"
        link-label="打开 Demo 验证（非产品功能）"
        @change="emit('scene', $event)"
      />
      <div class="identity">
        <div class="avatar">{{ identity?.display_name?.slice(0, 1) ?? "林" }}</div>
        <div>
          <div>{{ identity?.display_name ?? "林小北" }}</div>
          <div class="brand-sub">{{ identity?.department ?? "产品部" }}</div>
        </div>
        <span class="identity-caret" aria-hidden="true"></span>
      </div>
    </div>
  </header>
</template>
