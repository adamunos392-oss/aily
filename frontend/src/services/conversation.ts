import api from "@/services/api";
import {
  mockApplyScene,
  mockCreateConversation,
  mockGetConversation,
  mockListConversations,
} from "@/mocks";
import type {
  ApiEnvelope,
  ConversationCreateRequest,
  ConversationDetailResponse,
  ConversationListResponse,
  DemoSceneId,
} from "@/types/api";
import type { SceneApplyResult } from "@/mocks/engine";
import { unwrapEnvelope } from "@/utils/envelope";
import { isMockEnabled } from "@/utils/mockFlag";

export async function listConversations(limit = 20): Promise<ConversationListResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockListConversations(limit));
  }
  const { data } = await api.get<ApiEnvelope<ConversationListResponse>>("/conversations", {
    params: { limit },
  });
  return unwrapEnvelope(data);
}

export async function createConversation(
  body: ConversationCreateRequest = { title: null },
): Promise<ConversationDetailResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockCreateConversation(body));
  }
  const { data } = await api.post<ApiEnvelope<ConversationDetailResponse>>("/conversations", body);
  return unwrapEnvelope(data);
}

export async function getConversation(conversationId: string): Promise<ConversationDetailResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockGetConversation(conversationId));
  }
  const { data } = await api.get<ApiEnvelope<ConversationDetailResponse>>(
    `/conversations/${conversationId}`,
  );
  return unwrapEnvelope(data);
}

export async function applyDemoScene(sceneId: DemoSceneId): Promise<SceneApplyResult> {
  if (!isMockEnabled()) {
    throw new Error("原型场景切换仅在 VITE_USE_MOCK=true 时可用");
  }
  return unwrapEnvelope(mockApplyScene(sceneId));
}
