import api from "@/services/api";
import { mockApproveConfirmation, mockCancelConfirmation } from "@/mocks";
import type {
  ApiEnvelope,
  ConfirmationApproveRequest,
  ConfirmationCancelRequest,
  TurnResponse,
} from "@/types/api";
import { unwrapEnvelope } from "@/utils/envelope";
import { isMockEnabled } from "@/utils/mockFlag";

export async function approveConfirmation(
  conversationId: string,
  confirmationId: string,
  body: ConfirmationApproveRequest,
): Promise<TurnResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockApproveConfirmation(conversationId, confirmationId, body));
  }
  const { data } = await api.post<ApiEnvelope<TurnResponse>>(
    `/conversations/${conversationId}/confirmations/${confirmationId}/approve`,
    body,
  );
  return unwrapEnvelope(data);
}

export async function cancelConfirmation(
  conversationId: string,
  confirmationId: string,
  body: ConfirmationCancelRequest,
): Promise<TurnResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockCancelConfirmation(conversationId, confirmationId, body));
  }
  const { data } = await api.post<ApiEnvelope<TurnResponse>>(
    `/conversations/${conversationId}/confirmations/${confirmationId}/cancel`,
    body,
  );
  return unwrapEnvelope(data);
}
