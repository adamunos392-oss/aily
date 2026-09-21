import api from "@/services/api";
import { mockCreateTurn, mockGetTurn, mockUpdateSlots } from "@/mocks";
import type {
  ApiEnvelope,
  SlotUpdateRequest,
  TurnCreateRequest,
  TurnResponse,
} from "@/types/api";
import { unwrapEnvelope } from "@/utils/envelope";
import { isMockEnabled } from "@/utils/mockFlag";

export async function createTurn(
  conversationId: string,
  body: TurnCreateRequest,
): Promise<TurnResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockCreateTurn(conversationId, body));
  }
  const { data } = await api.post<ApiEnvelope<TurnResponse>>(
    `/conversations/${conversationId}/turns`,
    body,
  );
  return unwrapEnvelope(data);
}

export async function getTurn(conversationId: string, turnId: string): Promise<TurnResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockGetTurn(conversationId, turnId));
  }
  const { data } = await api.get<ApiEnvelope<TurnResponse>>(
    `/conversations/${conversationId}/turns/${turnId}`,
  );
  return unwrapEnvelope(data);
}

export async function updateSlots(
  conversationId: string,
  turnId: string,
  body: SlotUpdateRequest,
): Promise<TurnResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockUpdateSlots(conversationId, turnId, body));
  }
  const { data } = await api.patch<ApiEnvelope<TurnResponse>>(
    `/conversations/${conversationId}/turns/${turnId}/slots`,
    body,
  );
  return unwrapEnvelope(data);
}
