<script setup lang="ts">
import { computed, onMounted } from "vue";
import AssistantBubble from "@/components/AssistantBubble.vue";
import ProtoSceneBar from "@/components/ProtoSceneBar.vue";
import TracePanel from "@/components/TracePanel.vue";
import WorkbenchSidebar from "@/components/WorkbenchSidebar.vue";
import WorkbenchTopbar from "@/components/WorkbenchTopbar.vue";
import { useWorkbenchStore } from "@/stores/workbench";
import { SHORTCUTS } from "@/utils/copy";
import type { DemoSceneId } from "@/types/api";

const store = useWorkbenchStore();

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

function keepReport(draftId: string, content: string): void {
  void store.keepReportEdit(draftId, content);
}

onMounted(() => {
  void store.bootstrap();
});

function onSceneChange(id: DemoSceneId): void {
  void store.loadScene(id);
}

function onSend(): void {
  void store.sendMessage(store.composerText, "manual", null);
}
</script>

<template>
  <div>
    <ProtoSceneBar :scene-id="store.sceneId" @change="onSceneChange" />
    <WorkbenchTopbar :identity="store.identity" />
    <div class="shell">
      <WorkbenchSidebar
        :conversations="store.conversations"
        :active-id="activeConversationId"
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
          <div v-if="emptyConversation" class="empty-hint">新对话。从上方功能进入，或直接输入问题。</div>
          <template v-else>
            <template v-for="item in store.displayTurns" :key="`${item.role}-${item.turnId}`">
              <div v-if="item.role === 'user'" class="bubble-user">{{ item.content }}</div>
              <AssistantBubble
                v-else
                :turn="store.turnMap[item.turnId]"
                @choose="store.choosePerson($event)"
                @approve="store.approveCurrent()"
                @cancel="store.cancelCurrent()"
                @open-source="store.traceTab = 'source'"
                @keep-report="keepReport"
              />
            </template>
            <template v-if="store.sending">
              <div
                v-if="store.loadingUserMessage && store.loadingUserMessage !== lastUserContent"
                class="bubble-user"
              >
                {{ store.loadingUserMessage }}
              </div>
              <div class="bubble-ai loading">正在处理本轮提问…</div>
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
