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
  modify: [];
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
  return `${confirmation.attendees.join("、")}（共${confirmation.attendees.length}人）`;
}
</script>

<template>
  <div v-if="turn" class="bubble-ai result-card">
    <template v-if="turn.assistant_message.message_type === 'knowledge_table'">
      <p class="result-lead">{{ introText || "根据企业知识库，找到以下相关资料：" }}</p>
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
        <div class="cite-title">引用来源</div>
        <div class="cite-grid">
          <div v-for="cite in turn.citations" :key="cite.knowledge_entry_id" class="cite-card">
            <strong>{{ cite.document_title }}</strong>
            <p>{{ cite.section }}</p>
            <button class="cite-link" type="button" @click="emit('openSource')">打开文档</button>
          </div>
        </div>
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
      <p class="result-lead">
        {{ turn.assistant_message.text || "我已识别到你想创建会议。请确认以下信息，如需修改可以直接告诉我。" }}
      </p>
      <div v-if="staleEvent" class="confirm-card stale">
        <strong>原确认已作废</strong>
        <p>时间：{{ String(staleEvent.payload.meeting_time ?? "14:00") }}（旧）</p>
      </div>
      <div v-if="turn.assistant_message.confirmation" class="confirm-card">
        <div class="confirm-head">
          <strong>{{ staleEvent ? "请重新确认" : "请确认会议信息" }}</strong>
          <span class="tag tag-warn">待确认</span>
        </div>
        <dl class="confirm-fields">
          <div>
            <dt>会议主题</dt>
            <dd>{{ turn.assistant_message.confirmation.topic }}</dd>
          </div>
          <div>
            <dt>时间</dt>
            <dd>{{ turn.assistant_message.confirmation.meeting_time }}</dd>
          </div>
          <div>
            <dt>参会人</dt>
            <dd>{{ attendeeLine(turn.assistant_message.confirmation) }}</dd>
          </div>
          <div>
            <dt>时长</dt>
            <dd>{{ turn.assistant_message.confirmation.duration_minutes }} 分钟</dd>
          </div>
          <div>
            <dt>会议类型</dt>
            <dd>{{ formatMeetingType(turn.assistant_message.confirmation.meeting_type) }}</dd>
          </div>
        </dl>
        <div class="confirm-actions">
          <button class="btn-ok" type="button" @click="emit('approve')">
            {{ staleEvent ? "同意新时间" : "确认创建" }}
          </button>
          <button class="btn-ghost" type="button" @click="emit('modify')">修改</button>
          <button v-if="!staleEvent" class="btn-ghost" type="button" @click="emit('cancel')">取消</button>
        </div>
      </div>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'meeting_success'">
      <div class="result-card-success">
        <div class="result-kicker">
          <span class="tag tag-ok">核验成功</span>
          会议已创建成功
        </div>
        <p>
          已为你创建「{{ turn.assistant_message.confirmation?.topic ?? "项目复盘会" }}」，并已邀请
          {{
            turn.assistant_message.confirmation
              ? attendeeLine(turn.assistant_message.confirmation)
              : "张明（产品部）、林小北"
          }}。
        </p>
        <p>会议已创建。</p>
        <dl class="confirm-fields">
          <div>
            <dt>时间</dt>
            <dd>{{ turn.assistant_message.confirmation?.meeting_time ?? "明天下午 15:00" }}</dd>
          </div>
          <div>
            <dt>参会人</dt>
            <dd>
              {{
                turn.assistant_message.confirmation
                  ? attendeeLine(turn.assistant_message.confirmation)
                  : "张明（产品部）、林小北"
              }}
            </dd>
          </div>
          <div>
            <dt>主题</dt>
            <dd>{{ turn.assistant_message.confirmation?.topic ?? "项目复盘会" }}</dd>
          </div>
        </dl>
      </div>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'meeting_unknown'">
      <div class="result-card-unknown">
        <div class="result-kicker">
          <span class="tag tag-fail">未知</span>
          创建结果未知
        </div>
        <div class="banner-unknown">创建结果未知，需要核验。未确认会议已创建。</div>
        <p>{{ turn.assistant_message.text }}</p>
      </div>
    </template>

    <template v-else-if="turn.assistant_message.message_type === 'report_draft'">
      <p class="result-lead">{{ turn.assistant_message.text }}</p>
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
        <p class="result-lead">{{ turn.assistant_message.text }}</p>
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
