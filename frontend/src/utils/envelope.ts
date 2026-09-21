import type { ApiEnvelope } from "@/types/api";

export class ApiError extends Error {
  code: number | string;

  constructor(code: number | string, message: string) {
    super(message);
    this.code = code;
    this.name = "ApiError";
  }
}

export function unwrapEnvelope<T>(envelope: ApiEnvelope<T>): T {
  if (envelope.code !== 200 || envelope.data === null) {
    throw new ApiError(envelope.code, envelope.message);
  }
  return envelope.data;
}

export function okEnvelope<T>(data: T, message = "ok"): ApiEnvelope<T> {
  return { code: 200, message, data };
}

export function failEnvelope<T>(
  code: number,
  message: string,
): ApiEnvelope<T> {
  return { code, message, data: null };
}
