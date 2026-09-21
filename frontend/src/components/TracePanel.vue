<script setup lang="ts">
import type { Citation, TraceEvent } from "@/types/api";
import { formatTraceTime } from "@/utils/formatTime";

defineProps<{
  tab: "process" | "source";
  events: TraceEvent[];
  citations: Citation[];
}>();

const emit = defineEmits<{
  tab: [value: "process" | "source"];
}>();

const TAIL_OP_TAG = /\u3000(?:只读|写入)$/;

function operationTag(event: TraceEvent): "READ" | "WRITE" | null {
  if (event.summary.endsWith("\u3000只读")) return "READ";
  if (event.summary.endsWith("\u3000写入")) return "WRITE";
  return null;
}

function summaryLines(event: TraceEvent): string[] {
  return event.summary.replace(TAIL_OP_TAG, "").split("<br/>");
}

function clauseNo(section: string): string {
  const matched = section.match(/第\s*[\d.]+\s*条/);
  return matched ? matched[0] : section;
}

function sourceLine(cite: Citation, index: number): string {
  return `${index + 1}. ${cite.document_title}${clauseNo(cite.section)}：${cite.excerpt}`;
}
</script>

<template>
  <aside class="trace">
    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'process' }" type="button" @click="emit('tab', 'process')">
        过程
      </button>
      <button class="tab" :class="{ active: tab === 'source' }" type="button" @click="emit('tab', 'source')">
        相关来源
      </button>
    </div>
    <div class="trace-body">
      <template v-if="tab === 'source'">
        <div v-if="!citations.length" class="empty-hint">本轮无知识来源</div>
        <p v-for="(cite, index) in citations" :key="cite.knowledge_entry_id">
          {{ sourceLine(cite, index) }}
        </p>
      </template>
      <template v-else>
        <div v-if="!events.length" class="empty-hint">本轮尚无过程</div>
        <div v-for="event in events" :key="event.event_id" class="event">
          <span class="dot"></span>
          <div>
            <h4>{{ event.title_zh }}</h4>
            <p>
              <template v-for="(line, lineIndex) in summaryLines(event)" :key="lineIndex">
                <span>{{ line }}</span>
                <br v-if="lineIndex === 0 && summaryLines(event).length > 1" />
              </template>
              <span v-if="operationTag(event) === 'READ'" class="tag tag-read">只读</span>
              <span v-if="operationTag(event) === 'WRITE'" class="tag tag-write">写入</span>
            </p>
          </div>
          <span>{{ formatTraceTime(event.occurred_at) }}</span>
        </div>
      </template>
    </div>
  </aside>
</template>
