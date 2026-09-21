import api from "@/services/api";
import { mockGetIdentity } from "@/mocks";
import type { ApiEnvelope, IdentityResponse } from "@/types/api";
import { unwrapEnvelope } from "@/utils/envelope";
import { isMockEnabled } from "@/utils/mockFlag";

export async function getIdentity(): Promise<IdentityResponse> {
  if (isMockEnabled()) {
    return unwrapEnvelope(mockGetIdentity());
  }
  const { data } = await api.get<ApiEnvelope<IdentityResponse>>("/identity");
  return unwrapEnvelope(data);
}
