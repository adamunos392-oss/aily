const TIMEZONE = "Asia/Shanghai";

function partsInShanghai(iso: string): { hour: string; minute: string; second: string } {
  const date = new Date(iso);
  const formatter = new Intl.DateTimeFormat("zh-CN", {
    timeZone: TIMEZONE,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  const parts = formatter.formatToParts(date);
  const pick = (type: string) => parts.find((item) => item.type === type)?.value ?? "00";
  return { hour: pick("hour"), minute: pick("minute"), second: pick("second") };
}

export function formatSidebarTime(iso: string): string {
  const { hour, minute } = partsInShanghai(iso);
  return `今天 ${hour}:${minute}`;
}

export function formatTraceTime(iso: string): string {
  const { hour, minute, second } = partsInShanghai(iso);
  return `${hour}:${minute}:${second}`;
}

export function formatLimitCny(limit: number): string {
  return `≤ ${limit.toLocaleString("zh-CN")}`;
}

export function formatMeetingType(type: "online" | "offline"): string {
  return type === "online" ? "线上会议" : "线下会议";
}

export function formatRoomWindow(fromIso: string, toIso: string): string {
  const from = partsInShanghai(fromIso);
  const to = partsInShanghai(toIso);
  return `明天下午 ${from.hour}:${from.minute}–${to.hour}:${to.minute} 空闲`;
}
