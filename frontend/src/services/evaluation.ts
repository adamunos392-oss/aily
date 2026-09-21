import api from "@/services/api";
import { mockGetEvaluationCase, mockListEvaluationCases } from "@/mocks";
import type {
  ApiEnvelope,
  EvaluationCaseDetailResponse,
  EvaluationCaseListResponse,
} from "@/types/api";
import { unwrapEnvelope } from "@/utils/envelope";
import { isMockEnabled } from "@/utils/mockFlag";

export async function listEvaluationCases(): Promise<EvaluationCaseListResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockListEvaluationCases());
  }
  const { data } = await api.get<ApiEnvelope<EvaluationCaseListResponse>>("/evaluation_cases");
  return unwrapEnvelope(data);
}

export async function getEvaluationCase(caseId: string): Promise<EvaluationCaseDetailResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockGetEvaluationCase(caseId));
  }
  const { data } = await api.get<ApiEnvelope<EvaluationCaseDetailResponse>>(
    `/evaluation_cases/${caseId}`,
  );
  return unwrapEnvelope(data);
}
