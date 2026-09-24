<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

const props = defineProps<{
  sceneId: string;
  options: Array<{ id: string; label: string }>;
  sceneDisabled?: boolean;
  linkHref: string;
  linkLabel: string;
}>();

const emit = defineEmits<{
  change: [id: string];
}>();

const open = ref(false);
const root = ref<HTMLElement | null>(null);

function toggle(): void {
  open.value = !open.value;
}

function onSceneChange(event: Event): void {
  emit("change", (event.target as HTMLSelectElement).value);
}

function onPointerDown(event: MouseEvent): void {
  if (!root.value?.contains(event.target as Node)) {
    open.value = false;
  }
}

onMounted(() => {
  document.addEventListener("mousedown", onPointerDown);
});

onUnmounted(() => {
  document.removeEventListener("mousedown", onPointerDown);
});
</script>

<template>
  <div ref="root" class="demo-control">
    <button class="demo-control-btn" type="button" @click="toggle">Demo</button>
    <div v-if="open" class="demo-control-pop">
      <div class="demo-control-label">场景切换（非产品功能）</div>
      <select
        aria-label="选择原型场景"
        :value="props.sceneId"
        :disabled="props.sceneDisabled"
        @change="onSceneChange"
      >
        <option v-for="item in props.options" :key="item.id" :value="item.id">
          {{ item.label }}
        </option>
      </select>
      <a :href="props.linkHref">{{ props.linkLabel }}</a>
    </div>
  </div>
</template>
