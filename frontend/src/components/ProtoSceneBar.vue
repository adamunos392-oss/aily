<script setup lang="ts">
import { DEMO_SCENE_OPTIONS } from "@/utils/copy";
import type { DemoSceneId } from "@/types/api";

defineProps<{
  sceneId: DemoSceneId;
}>();

const emit = defineEmits<{
  change: [id: DemoSceneId];
}>();
</script>

<template>
  <div class="proto-bar">
    <span>原型场景切换（非产品功能）</span>
    <select
      aria-label="选择原型场景"
      :value="sceneId"
      @change="emit('change', ($event.target as HTMLSelectElement).value as DemoSceneId)"
    >
      <option v-for="item in DEMO_SCENE_OPTIONS" :key="item.id" :value="item.id">
        {{ item.label }}
      </option>
    </select>
    <a href="/demo/evaluation">打开 Demo 验证（非产品功能）</a>
  </div>
</template>
