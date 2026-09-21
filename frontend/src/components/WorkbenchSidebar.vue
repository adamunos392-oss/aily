<script setup lang="ts">
import type { ConversationSummary } from "@/types/api";
import { formatSidebarTime } from "@/utils/formatTime";

defineProps<{
  conversations: ConversationSummary[];
  activeId: string | null;
}>();

const emit = defineEmits<{
  create: [];
  open: [conversationId: string];
}>();

function isActive(id: string, activeId: string | null): boolean {
  return id === activeId;
}
</script>

<template>
  <aside class="aside">
    <button class="nav-item active" type="button">对话</button>
    <button class="btn-primary" type="button" @click="emit('create')">新建对话</button>
    <div class="section-label">最近对话</div>
    <button
      v-for="item in conversations"
      :key="item.conversation_id"
      class="conv"
      :class="{ active: isActive(item.conversation_id, activeId) }"
      type="button"
      @click="emit('open', item.conversation_id)"
    >
      {{ item.preview || item.title }}
      <small>{{ formatSidebarTime(item.updated_at) }}</small>
    </button>
  </aside>
</template>
