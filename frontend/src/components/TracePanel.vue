<script setup lang="ts">
import { ref } from "vue";
import type { Citation, TraceEvent } from "@/types/api";
import { formatTraceTime } from "@/utils/formatTime";
import { traceKindTag, traceStatusLabel } from "@/utils/copy";

defineProps<{
  tab: "process" | "source";
  events: TraceEvent[];
  citations: Citation[];
}>();

const emit = defineEmits<{
  tab: [value: "process" | "source"];
}>();

const TAIL_OP_TAG = /\u3000(?:只读|写入)$/;
const expanded = ref<Record<string, boolean>>({});

function summaryText(event: TraceEvent): string {
  return event.summary.replace(TAIL_OP_TAG, "").replace(/<br\s*\/?>/g, " · ");
}

function clauseNo(section: string): string {
  const matched = section.match(/第\s*[\d.]+\s*条/);
  return matched ? matched[0] : section;
}

function sourceLine(cite: Citation, index: number): string {
  return `${index + 1}. ${cite.document_title}${clauseNo(cite.section)}：${cite.excerpt}`;
}

function toggle(eventId: string): void {
  expanded.value = { ...expanded.value, [eventId]: !expanded.value[eventId] };
}

function payloadEntries(payload: Record<string, unknown>): Array<{ key: string; value: string }> {
  return Object.entries(payload).map(([key, value]) => ({
    key,
    value: typeof value === "string" ? value : JSON.stringify(value),
  }));
}

function tagClass(tag: string): string {
  return `tag-kind-${tag.toLowerCase()}`;
}
</script>

<template>
  <aside class="trace">
    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'process' }" type="button" @click="emit('tab', 'process')">
        Agent 运行过程
      </button>
      <button class="tab" :class="{ active: tab === 'source' }" type="button" @click="emit('tab', 'source')">
        相关来源
      </button>
    </div>
    <div class="trace-body">
      <template v-if="tab === 'source'">
        <div v-if="!citations.length" class="empty-hint">本轮无知识来源</div>
        <div v-else class="cite-list">
          <p v-for="(cite, index) in citations" :key="cite.knowledge_entry_id">
            {{ sourceLine(cite, index) }}
          </p>
        </div>
      </template>
      <template v-else>
        <div v-if="!events.length" class="empty-hint">本轮尚无过程</div>
        <button
          v-for="event in events"
          :key="event.event_id"
          class="event"
          type="button"
          @click="toggle(event.event_id)"
        >
          <span class="dot" :class="tagClass(traceKindTag(event) ?? 'read')"></span>
          <div class="event-main">
            <h4>
              {{ event.title_zh }}
              <span v-if="traceKindTag(event)" class="tag" :class="tagClass(traceKindTag(event)!)">
                {{ traceKindTag(event) }}
              </span>
            </h4>
            <p>
              <span class="event-status">{{ traceStatusLabel(event) }}</span>
              · {{ summaryText(event) }}
            </p>
            <dl v-if="expanded[event.event_id] && payloadEntries(event.payload).length" class="event-detail">
              <template v-for="item in payloadEntries(event.payload)" :key="item.key">
                <dt>{{ item.key }}</dt>
                <dd>{{ item.value }}</dd>
              </template>
            </dl>
          </div>
          <span class="event-time">{{ formatTraceTime(event.occurred_at) }}</span>
        </button>
      </template>
    </div>
  </aside>
</template>
