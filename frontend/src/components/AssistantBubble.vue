<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { ConfirmationSummary, TraceEvent, TurnResponse } from "@/types/api";
import { formatLimitCny, formatMeetingType, formatRoomWindow } from "@/utils/formatTime";

const props = defineProps<{
  turn: TurnResponse | null;
}>();

const emit = defineEmits<{
  choose: [choiceId: string];
  approve: [];
  cancel: [];
  openSource: [];
  keepReport: [draftId: string, content: string];
}>();

const reportText = ref("");

watch(
  () => props.turn?.assistant_message.report_draft?.content,
  (value) => {
    reportText.value = value ?? "";
  },
  { immediate: true },
);

const introText = computed(() => {
  const text = props.turn?.assistant_message.text ?? "";
  const [intro] = text.split("\n\n");
  return intro;
});

const restText = computed(() => {
  const text = props.turn?.assistant_message.text ?? "";
  const parts = text.split("\n\n");
  return parts.slice(1).join("\n\n");
});

const staleEvent = computed<TraceEvent | undefined>(() =>
  props.turn?.trace_events.find(
    (item) => item.node === "confirmation" && item.payload.status === "invalidated",
  ),
);

function attendeeLine(confirmation: ConfirmationSummary): string {
  return confirmation.attendees.join("、");
}
</script>

<template>
  <div v-if="turn" class="bubble-ai">
    <template v-if="turn.assistant_message.message_type === 'knowledge_table'">
      <div>{{ introText }}</div>
      <table class="table">
        <thead>
          <tr>
            <th>职级</th>
            <th>城市类型</th>
            <th>住宿标准（人民币/晚）</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in turn.assistant_message.table_rows ?? []" :key="index">
            <td>{{ row.level }}</td>
            <td>{{ row.city_type }}</td>
            <td>{{ formatLimitCny(row.limit_cny) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="restText">{{ restText }}</div>
      <div v-if="turn.citations.length" class="cite">
        引用来源<br />
        <template v-for="(cite, index) in turn.citations" :key="cite.knowledge_entry_id">
          {{ index + 1 }}. {{ cite.document_title }}{{ cite.section }}
          <button class="cite-link" type="button" @click="emit('openSource')">打开文档</button>
          <br />
        </template>
      </div>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'refusal'">
      <div class="banner-refuse">未找到可靠企业知识依据，无法回答该问题。</div>
      <p>{{ turn.assistant_message.text }}</p>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'clarification'">
      {{ turn.assistant_message.text }}
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'disambiguation'">
      {{ turn.assistant_message.text }}
      <div class="choice-row">
        <button
          v-for="choice in turn.assistant_message.choices ?? []"
          :key="choice.choice_id"
          class="choice"
          type="button"
          @click="emit('choose', choice.choice_id)"
        >
          {{ choice.label }}
        </button>
      </div>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'confirmation'">
      <div v-if="staleEvent" class="confirm-card stale">
        <strong>原确认已作废</strong>
        <p>时间：{{ String(staleEvent.payload.meeting_time ?? "14:00") }}（旧）</p>
      </div>
      <div v-if="turn.assistant_message.confirmation" class="confirm-card">
        <strong>{{ staleEvent ? "请重新确认" : "请确认创建会议" }}</strong>
        <p>
          时间：{{ turn.assistant_message.confirmation.meeting_time }}<br />
          参会人：{{ attendeeLine(turn.assistant_message.confirmation) }}<br />
          主题：{{ turn.assistant_message.confirmation.topic }}<br />
          <template v-if="!staleEvent">
            时长：{{ turn.assistant_message.confirmation.duration_minutes }} 分钟<br />
            类型：{{ formatMeetingType(turn.assistant_message.confirmation.meeting_type) }}
          </template>
        </p>
        <button class="btn-ok" type="button" @click="emit('approve')">
          {{ staleEvent ? "同意新时间" : "同意创建" }}
        </button>
        <button v-if="!staleEvent" class="btn-ghost" type="button" @click="emit('cancel')">取消</button>
      </div>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'meeting_success'">
      <span class="tag tag-ok">核验成功</span>
      <p>会议已创建。</p>
      <p>
        时间：明天下午 15:00<br />
        参会人：张明（产品部）、林小北<br />
        主题：项目复盘会
      </p>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'meeting_unknown'">
      <div class="banner-unknown">创建结果未知，需要核验。未确认会议已创建。</div>
      <p>{{ turn.assistant_message.text }}</p>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'report_draft'">
      <p>{{ turn.assistant_message.text }}</p>
      <textarea v-model="reportText" class="report" />
      <p class="brand-sub">闲聊未写入。修改后以你的编辑版为准。</p>
      <button
        class="btn-ok"
        type="button"
        :disabled="!turn.assistant_message.report_draft"
        @click="
          turn.assistant_message.report_draft &&
            emit('keepReport', turn.assistant_message.report_draft.draft_id, reportText)
        "
      >
        保留修改
      </button>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'room_list'">
      <div v-if="!(turn.assistant_message.rooms ?? []).length" class="banner-refuse">
        {{ turn.assistant_message.text }}
      </div>
      <template v-else>
        <p>{{ turn.assistant_message.text }}</p>
        <div class="room-grid">
          <div
            v-for="room in turn.assistant_message.rooms ?? []"
            :key="room.room_name"
            class="room-card"
          >
            <strong>{{ room.room_name }}</strong>
            <p>{{ formatRoomWindow(room.available_from, room.available_to) }}</p>
          </div>
        </div>
      </template>
    </template>

    <template v-else>
      {{ turn.assistant_message.text }}
    </template>
  </div>
</template>
