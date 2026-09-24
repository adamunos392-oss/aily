<script setup lang="ts">
import { computed } from "vue";
import type { ConversationSceneTag } from "@/utils/copy";
import type { ConversationSummary } from "@/types/api";
import {
  formatSidebarTime,
  sidebarDayGroup,
  sidebarDayGroupLabel,
  type SidebarDayGroup,
} from "@/utils/formatTime";

const props = defineProps<{
  conversations: ConversationSummary[];
  activeId: string | null;
  tags: Record<string, ConversationSceneTag | null>;
}>();

const emit = defineEmits<{
  create: [];
  open: [conversationId: string];
}>();

const GROUP_ORDER: SidebarDayGroup[] = ["today", "yesterday", "earlier"];

const grouped = computed(() =>
  GROUP_ORDER.map((group) => ({
    group,
    label: sidebarDayGroupLabel(group),
    items: props.conversations.filter((item) => sidebarDayGroup(item.updated_at) === group),
  })).filter((item) => item.items.length > 0),
);

function isActive(id: string): boolean {
  return id === props.activeId;
}
</script>

<template>
  <aside class="aside">
    <button class="nav-item active" type="button">对话</button>
    <button class="btn-primary btn-new-chat" type="button" @click="emit('create')">
      <span class="plus">+</span>
      新建对话
    </button>
    <input class="sidebar-search" disabled value="" placeholder="搜索对话..." />
    <template v-for="block in grouped" :key="block.group">
      <div class="section-label">{{ block.label }}</div>
      <button
        v-for="item in block.items"
        :key="item.conversation_id"
        class="conv"
        :class="{ active: isActive(item.conversation_id) }"
        type="button"
        @click="emit('open', item.conversation_id)"
      >
        <span class="conv-ico" :data-tag="tags[item.conversation_id] ?? 'none'"></span>
        <span class="conv-body">
          <span class="conv-title">{{ item.preview || item.title }}</span>
          <span class="conv-meta">
            <span v-if="tags[item.conversation_id]" class="tag" :class="`tag-scene-${tags[item.conversation_id]}`">
              {{ tags[item.conversation_id] }}
            </span>
            <small>{{ formatSidebarTime(item.updated_at) }}</small>
          </span>
        </span>
      </button>
    </template>
  </aside>
</template>
