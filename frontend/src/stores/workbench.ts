import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { applyDemoScene, createConversation, getConversation, listConversations } from "@/services/conversation";
import { approveConfirmation, cancelConfirmation } from "@/services/confirmation";
import { getIdentity } from "@/services/identity";
import { saveReportDraft } from "@/services/report";
import { createTurn, getTurn, updateSlots } from "@/services/turn";
import { nextDemoMeetingTime } from "@/utils/copy";
import type {
  ConversationDetailResponse,
  ConversationSummary,
  DemoSceneId,
  EntrySource,
  IdentityResponse,
  TurnResponse,
} from "@/types/api";
import { TIMEOUT_CONVERSATION_ID } from "@/mocks/dto";

export const useWorkbenchStore = defineStore("workbench", () => {
  const identity = ref<IdentityResponse | null>(null);
  const conversations = ref<ConversationSummary[]>([]);
  const current = ref<ConversationDetailResponse | null>(null);
  const turnMap = ref<Record<string, TurnResponse>>({});
  const composerText = ref("");
  const sending = ref(false);
  const loadingUserMessage = ref("");
  const traceTab = ref<"process" | "source">("process");
  const sceneId = ref<DemoSceneId>("qa-success");

  const currentTurn = computed<TurnResponse | null>(() => {
    if (sending.value) {
      const processing = Object.values(turnMap.value).find((item) => item.status === "processing");
      if (processing) return processing;
    }
    const turns = current.value?.turns ?? [];
    for (let i = turns.length - 1; i >= 0; i -= 1) {
      const item = turns[i];
      if (item.role === "assistant" && turnMap.value[item.turn_id]) {
        return turnMap.value[item.turn_id];
      }
    }
    return null;
  });

  const displayTurns = computed(() => {
    const ordered: Array<{
      turnId: string;
      role: "user" | "assistant";
      content: string;
      createdAt: string;
    }> = [];
    const seenAssistant = new Set<string>();
    for (const item of current.value?.turns ?? []) {
      if (item.role === "user") {
        ordered.push({
          turnId: item.turn_id,
          role: "user",
          content: item.content,
          createdAt: item.created_at,
        });
      } else if (!seenAssistant.has(item.turn_id)) {
        seenAssistant.add(item.turn_id);
        ordered.push({
          turnId: item.turn_id,
          role: "assistant",
          content: item.content,
          createdAt: item.created_at,
        });
      }
    }
    return ordered;
  });

  async function refreshList(): Promise<void> {
    const data = await listConversations();
    conversations.value = data.items;
  }

  async function hydrateTurns(detail: ConversationDetailResponse): Promise<void> {
    const ids = [...new Set(detail.turns.map((item) => item.turn_id))];
    const next: Record<string, TurnResponse> = {};
    await Promise.all(
      ids.map(async (turnId) => {
        try {
          next[turnId] = await getTurn(detail.conversation_id, turnId);
        } catch {
          return;
        }
      }),
    );
    turnMap.value = next;
  }

  async function openConversation(conversationId: string): Promise<void> {
    const detail = await getConversation(conversationId);
    current.value = detail;
    sending.value = false;
    loadingUserMessage.value = "";
    await hydrateTurns(detail);
    await refreshList();
  }

  async function bootstrap(): Promise<void> {
    identity.value = await getIdentity();
    await refreshList();
    const first = conversations.value[0];
    if (first) {
      sceneId.value = "qa-success";
      await openConversation(first.conversation_id);
    }
  }

  async function createNewConversation(): Promise<void> {
    const created = await createConversation({ title: null });
    sceneId.value = "empty";
    composerText.value = "";
    sending.value = false;
    loadingUserMessage.value = "";
    current.value = created;
    turnMap.value = {};
    traceTab.value = "process";
    await refreshList();
  }

  async function applyTurn(turn: TurnResponse): Promise<void> {
    turnMap.value = { ...turnMap.value, [turn.turn_id]: turn };
    await openConversation(turn.conversation_id);
  }

  async function sendMessage(
    content: string,
    entrySource: EntrySource = "manual",
    choiceId: string | null = null,
  ): Promise<void> {
    const text = content.trim();
    if (!text || sending.value) return;
    if (!current.value) {
      await createNewConversation();
    }
    const conversationId = current.value?.conversation_id;
    if (!conversationId) return;
    composerText.value = "";
    sending.value = true;
    loadingUserMessage.value = text;
    try {
      const turn = await createTurn(conversationId, {
        content: text,
        entry_source: entrySource,
        choice_id: choiceId,
        client_turn_key: null,
      });
      sending.value = false;
      loadingUserMessage.value = "";
      await applyTurn(turn);
    } catch (error) {
      sending.value = false;
      throw error;
    }
  }

  async function choosePerson(choiceId: string): Promise<void> {
    const lastUser = [...(current.value?.turns ?? [])].reverse().find((item) => item.role === "user");
    const content = lastUser?.content ?? "帮我明天下午三点跟张明开一个项目复盘会。";
    await sendMessage(content, "manual", choiceId);
  }

  async function approveCurrent(): Promise<void> {
    const turn = currentTurn.value;
    const confirmation = turn?.assistant_message.confirmation;
    if (!turn || !confirmation || !current.value) return;
    const next = await approveConfirmation(current.value.conversation_id, confirmation.confirmation_id, {
      turn_id: turn.turn_id,
    });
    await applyTurn(next);
  }

  async function cancelCurrent(): Promise<void> {
    const turn = currentTurn.value;
    const confirmation = turn?.assistant_message.confirmation;
    if (!turn || !confirmation || !current.value) return;
    const next = await cancelConfirmation(current.value.conversation_id, confirmation.confirmation_id, {
      turn_id: turn.turn_id,
      reason: null,
    });
    await applyTurn(next);
  }

  async function keepReportEdit(draftId: string, content: string): Promise<void> {
    const turn = currentTurn.value;
    if (!turn || !current.value) return;
    await saveReportDraft(current.value.conversation_id, turn.turn_id, draftId, content);
    const refreshed = await getTurn(current.value.conversation_id, turn.turn_id);
    turnMap.value = { ...turnMap.value, [turn.turn_id]: refreshed };
  }

  async function changeCurrentMeetingTime(): Promise<void> {
    const turn = currentTurn.value;
    const confirmation = turn?.assistant_message.confirmation;
    if (!turn || !confirmation || !current.value) return;
    const next = await updateSlots(current.value.conversation_id, turn.turn_id, {
      updates: { meeting_time: nextDemoMeetingTime(confirmation.meeting_time) },
    });
    await applyTurn(next);
  }

  async function loadScene(id: DemoSceneId): Promise<void> {
    const result = await applyDemoScene(id);
    sceneId.value = result.sceneId;
    composerText.value = result.composerText;
    sending.value = result.loading;
    loadingUserMessage.value = result.loading ? result.turn?.user_message ?? "" : "";
    current.value = result.conversation;
    turnMap.value = result.turn ? { [result.turn.turn_id]: result.turn } : {};
    traceTab.value = "process";
    await refreshList();
  }

  function isConversationActive(conversationId: string): boolean {
    if (current.value?.conversation_id === conversationId) return true;
    if (current.value?.conversation_id === TIMEOUT_CONVERSATION_ID && conversationId === "conv-002") {
      return true;
    }
    if (current.value?.conversation_id === "conv-rooms-empty" && conversationId === "conv-004") {
      return true;
    }
    return false;
  }

  return {
    identity,
    conversations,
    current,
    turnMap,
    composerText,
    sending,
    loadingUserMessage,
    traceTab,
    sceneId,
    currentTurn,
    displayTurns,
    bootstrap,
    refreshList,
    openConversation,
    createNewConversation,
    sendMessage,
    choosePerson,
    approveCurrent,
    cancelCurrent,
    keepReportEdit,
    changeCurrentMeetingTime,
    loadScene,
    isConversationActive,
  };
});
