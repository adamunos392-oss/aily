<script setup lang="ts">
import { computed, onMounted } from "vue";
import AssistantBubble from "@/components/AssistantBubble.vue";
import TracePanel from "@/components/TracePanel.vue";
import WorkbenchSidebar from "@/components/WorkbenchSidebar.vue";
import WorkbenchTopbar from "@/components/WorkbenchTopbar.vue";
import { useWorkbenchStore } from "@/stores/workbench";
import { SHORTCUTS, conversationSceneTag, type ConversationSceneTag } from "@/utils/copy";
import { formatSidebarTime } from "@/utils/formatTime";
import { isMockEnabled } from "@/utils/mockFlag";
import type { DemoSceneId } from "@/types/api";

const store = useWorkbenchStore();

const userInitial = computed(() => store.identity?.display_name?.slice(0, 1) ?? "林");

const activeConversationId = computed(() => {
  const currentId = store.current?.conversation_id ?? null;
  if (!currentId) return null;
  const match = store.conversations.find((item) => item.conversation_id === currentId);
  if (match) return currentId;
  const highlighted = store.conversations.find((item) => store.isConversationActive(item.conversation_id));
  return highlighted?.conversation_id ?? null;
});

const currentEvents = computed(() => store.currentTurn?.trace_events ?? []);
const currentCitations = computed(() => store.currentTurn?.citations ?? []);
const emptyConversation = computed(
  () => !store.sending && (!store.current || store.displayTurns.length === 0),
);

const lastUserContent = computed(() => {
  const users = store.displayTurns.filter((item) => item.role === "user");
  return users[users.length - 1]?.content ?? "";
});

const conversationTags = computed<Record<string, ConversationSceneTag | null>>(() => {
  const activeId = activeConversationId.value;
  const routeType =
    activeId && store.currentTurn?.conversation_id === activeId
      ? store.currentTurn.route_decision.route_type
      : null;
  const tags: Record<string, ConversationSceneTag | null> = {};
  for (const item of store.conversations) {
    tags[item.conversation_id] = conversationSceneTag(
      item.preview,
      item.title,
      item.conversation_id === activeId ? routeType : null,
    );
  }
  return tags;
});

function keepReport(draftId: string, content: string): void {
  void store.keepReportEdit(draftId, content);
}

onMounted(() => {
  void store.bootstrap();
});

function onSceneChange(id: string): void {
  if (!isMockEnabled()) return;
  void store.loadScene(id as DemoSceneId);
}

function onSend(): void {
  void store.sendMessage(store.composerText, "manual", null);
}
</script>

<template>
  <div class="workbench">
    <WorkbenchTopbar :identity="store.identity" :scene-id="store.sceneId" @scene="onSceneChange" />
    <div class="shell">
      <WorkbenchSidebar
        :conversations="store.conversations"
        :active-id="activeConversationId"
        :tags="conversationTags"
        @create="store.createNewConversation()"
        @open="store.openConversation($event)"
      />
      <section class="main">
        <div class="shortcuts">
          <button
            v-for="item in SHORTCUTS"
            :key="item.id"
            class="shortcut"
            type="button"
            :disabled="store.sending"
            @click="store.sendMessage(item.query, item.entrySource, item.id === 'task' ? 'person:zhangming-product' : null)"
          >
            <strong>{{ item.title }}</strong>
            <span>{{ item.subtitle }}</span>
          </button>
        </div>
        <div class="messages">
          <div v-if="emptyConversation" class="empty-hint empty-main">新对话。从上方功能进入，或直接输入问题。</div>
          <template v-else>
            <template v-for="item in store.displayTurns" :key="`${item.role}-${item.turnId}`">
              <div v-if="item.role === 'user'" class="msg-row msg-user">
                <div class="msg-stack">
                  <div class="bubble-user">{{ item.content }}</div>
                  <time class="msg-time">{{ formatSidebarTime(item.createdAt) }}</time>
                </div>
                <div class="avatar avatar-user">{{ userInitial }}</div>
              </div>
              <div v-else-if="store.turnMap[item.turnId]" class="msg-row msg-ai">
                <div class="avatar avatar-ai">A</div>
                <AssistantBubble
                  :turn="store.turnMap[item.turnId]"
                  @choose="store.choosePerson($event)"
                  @approve="store.approveCurrent()"
                  @cancel="store.cancelCurrent()"
                  @modify="store.changeCurrentMeetingTime()"
                  @open-source="store.traceTab = 'source'"
                  @keep-report="keepReport"
                />
              </div>
              <div v-else class="msg-row msg-ai">
                <div class="avatar avatar-ai">A</div>
                <div class="bubble-ai">{{ item.content }}</div>
              </div>
            </template>
            <template v-if="store.sending">
              <div
                v-if="store.loadingUserMessage && store.loadingUserMessage !== lastUserContent"
                class="msg-row msg-user"
              >
                <div class="msg-stack">
                  <div class="bubble-user">{{ store.loadingUserMessage }}</div>
                </div>
                <div class="avatar avatar-user">{{ userInitial }}</div>
              </div>
              <div class="msg-row msg-ai">
                <div class="avatar avatar-ai">A</div>
                <div class="bubble-ai loading">正在处理本轮提问…</div>
              </div>
            </template>
          </template>
        </div>
        <div class="composer">
          <textarea
            v-model="store.composerText"
            placeholder="请输入，或选择上方功能"
            :disabled="store.sending"
            @keydown.enter.exact.prevent="onSend"
          />
          <button class="btn-send" type="button" :disabled="store.sending" @click="onSend">发送</button>
        </div>
      </section>
      <TracePanel
        :tab="store.traceTab"
        :events="currentEvents"
        :citations="currentCitations"
        @tab="store.traceTab = $event"
      />
    </div>
  </div>
</template>
