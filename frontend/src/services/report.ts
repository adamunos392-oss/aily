import api from "@/services/api";
import { mockSaveReportDraft } from "@/mocks";
import type { ApiEnvelope, ReportDraftResponse } from "@/types/api";
import { unwrapEnvelope } from "@/utils/envelope";
import { isMockEnabled } from "@/utils/mockFlag";

export async function saveReportDraft(
  conversationId: string,
  turnId: string,
  draftId: string,
  content: string,
): Promise<ReportDraftResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockSaveReportDraft(conversationId, turnId, draftId, content));
  }
  const { data } = await api.patch<ApiEnvelope<ReportDraftResponse>>(
    `/conversations/${conversationId}/turns/${turnId}/report_drafts/${draftId}`,
    { content },
  );
  return unwrapEnvelope(data);
}
