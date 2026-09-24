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

export function shanghaiDateKey(iso: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(iso));
}

export function todayShanghaiKey(): string {
  return shanghaiDateKey(new Date().toISOString());
}

export function yesterdayShanghaiKey(): string {
  const [year, month, day] = todayShanghaiKey().split("-").map(Number);
  const previous = new Date(Date.UTC(year, month - 1, day - 1));
  return previous.toISOString().slice(0, 10);
}

export type SidebarDayGroup = "today" | "yesterday" | "earlier";

export function sidebarDayGroup(iso: string): SidebarDayGroup {
  const key = shanghaiDateKey(iso);
  if (key === todayShanghaiKey()) return "today";
  if (key === yesterdayShanghaiKey()) return "yesterday";
  return "earlier";
}

export function sidebarDayGroupLabel(group: SidebarDayGroup): string {
  if (group === "today") return "今天";
  if (group === "yesterday") return "昨天";
  return "更早";
}

export function formatSidebarTime(iso: string): string {
  const { hour, minute } = partsInShanghai(iso);
  return `${hour}:${minute}`;
}

export function formatTraceTime(iso: string): string {
  const { hour, minute, second } = partsInShanghai(iso);
  return `${hour}:${minute}:${second}`;
}

export function formatLimitCny(limit: number): string {
  return `≤ ${limit.toLocaleString("zh-CN")}`;
}

export function formatMeetingType(type: "online" | "offline"): string {
  return type === "online" ? "线上会议（飞书会议）" : "线下会议";
}

export function formatRoomWindow(fromIso: string, toIso: string): string {
  const from = partsInShanghai(fromIso);
  const to = partsInShanghai(toIso);
  return `明天下午 ${from.hour}:${from.minute}–${to.hour}:${to.minute} 空闲`;
}
