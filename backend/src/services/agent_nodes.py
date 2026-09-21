"""Agent 节点 Service：Plugin 经本层调用 Mock Adapter。"""

from src.core.config import AppSettings, settings
from src.models.agent.types import (
    AssistantMessage,
    Citation,
    ConversationRuntimeState,
    EntrySource,
    IntentResult,
    KnowledgeTableRow,
    MeetingRoomItem,
    MemoryState,
    QueryContext,
    RagAdapterResult,
    ReportDraft,
    ResultValidationOutcome,
    RewriteResult,
    RiskPermissionResult,
    RouteDecision,
    SkillAdapterResult,
    SlotAdapterResult,
    ToolCall,
    ToolResult,
)
from src.repositories.mock.intent_adapter import IntentAdapter
from src.repositories.mock.rag_adapter import RagAdapter
from src.repositories.mock.rewrite_adapter import RewriteAdapter
from src.repositories.mock.router_adapter import RouterAdapter
from src.repositories.mock.skill_adapter import SkillAdapter
from src.repositories.mock.slot_adapter import SlotAdapter
from src.repositories.mock.tool_adapter import ToolAdapter


class RewriteService:
    def __init__(self, adapter: RewriteAdapter | None = None) -> None:
        self._adapter = adapter if adapter is not None else RewriteAdapter()

    async def rewrite(self, query: QueryContext) -> RewriteResult:
        return await self._adapter.rewrite(query)


class IntentService:
    def __init__(self, adapter: IntentAdapter | None = None) -> None:
        self._adapter = adapter if adapter is not None else IntentAdapter()

    async def classify(self, query: QueryContext, rewritten_query: str) -> IntentResult:
        return await self._adapter.classify(query, rewritten_query)


class SlotService:
    def __init__(self, adapter: SlotAdapter | None = None) -> None:
        self._adapter = adapter if adapter is not None else SlotAdapter()

    async def fill(
        self,
        query: QueryContext,
        intent: IntentResult,
        rewritten_query: str,
        conversation_state: ConversationRuntimeState,
    ) -> SlotAdapterResult:
        return await self._adapter.fill(query, intent, rewritten_query, conversation_state)


class MemoryService:
    async def load(self) -> MemoryState:
        return MemoryState()


class RiskPermissionService:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def check(self, intent: IntentResult) -> RiskPermissionResult:
        identity = f"{self._settings.mock_user_display_name}｜{self._settings.mock_user_department}"
        return RiskPermissionResult(
            allowed=True,
            operation_type=intent.operation_type,
            summary=f"写入操作 · 当前身份{identity}",
        )


class RouterService:
    def __init__(self, adapter: RouterAdapter | None = None) -> None:
        self._adapter = adapter if adapter is not None else RouterAdapter()

    async def decide(
        self, intent: IntentResult, rewritten_query: str, entry_source: EntrySource
    ) -> RouteDecision:
        return await self._adapter.decide(intent, rewritten_query, entry_source)


class RagService:
    def __init__(self, adapter: RagAdapter | None = None) -> None:
        self._adapter = adapter if adapter is not None else RagAdapter()

    async def retrieve(self, query: QueryContext, rewritten_query: str) -> RagAdapterResult:
        return await self._adapter.retrieve(query, rewritten_query)


class ToolService:
    def __init__(self, adapter: ToolAdapter | None = None) -> None:
        self._adapter = adapter if adapter is not None else ToolAdapter()

    async def execute(self, call: ToolCall, query: QueryContext) -> ToolResult:
        return await self._adapter.execute(call, query)


class SkillService:
    def __init__(
        self,
        adapter: SkillAdapter | None = None,
        tool_service: ToolService | None = None,
    ) -> None:
        self._adapter = adapter if adapter is not None else SkillAdapter()
        self._tools = tool_service if tool_service is not None else ToolService()

    async def plan(
        self,
        query: QueryContext,
        intent: IntentResult,
        slot_result: SlotAdapterResult,
        conversation_state: ConversationRuntimeState,
    ) -> SkillAdapterResult:
        return await self._adapter.plan(query, intent, slot_result, conversation_state)

    async def run_tools(self, calls: list[ToolCall], query: QueryContext) -> list[ToolResult]:
        results: list[ToolResult] = []
        for call in calls:
            results.append(await self._tools.execute(call, query))
        return results

    def compose_weekly_report(
        self,
        query: QueryContext,
        tool_results: list[ToolResult],
        memory: MemoryState | None,
    ) -> ReportDraft:
        return self._adapter.compose_weekly_report(
            query,
            tool_results,
            memory if memory is not None else MemoryState(),
        )


class ResultValidationService:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def validate(
        self,
        *,
        route: RouteDecision,
        rag: RagAdapterResult | None,
        skill: SkillAdapterResult | None,
        tool_results: list[ToolResult],
    ) -> ResultValidationOutcome:
        if any(item.status == "timeout" for item in tool_results):
            return ResultValidationOutcome(
                status="unknown",
                result_status="unknown",
                assistant_message=AssistantMessage(
                    message_type="meeting_unknown",
                    text="已确认的会议信息仍保留，但系统未在约定等待内得到确定成功。",
                ),
            )
        if route.route_type == "RAG":
            return self._validate_rag(rag)
        if route.route_type == "READ_TOOL":
            rooms = self._rooms_from_tools(tool_results)
            text = (
                "明天下午 15:00 以后可用的会议室："
                if rooms
                else "该时段没有可用会议室。"
            )
            return ResultValidationOutcome(
                status="replied",
                result_status="success",
                assistant_message=AssistantMessage(
                    message_type="room_list",
                    text=text,
                    rooms=rooms,
                ),
            )
        if skill is not None:
            return self._validate_skill(skill, tool_results)
        return ResultValidationOutcome(
            status="refused",
            result_status="refused",
            assistant_message=AssistantMessage(
                message_type="refusal",
                text="以上内容基于公司内部知识。如有特殊情况请咨询行政部门。",
            ),
        )

    def _validate_rag(self, rag: RagAdapterResult | None) -> ResultValidationOutcome:
        refuse = ResultValidationOutcome(
            status="refused",
            result_status="refused",
            citation_valid=False,
            citations=[],
            assistant_message=AssistantMessage(
                message_type="refusal",
                text="以上内容基于公司内部知识。如有特殊情况请咨询行政部门。",
            ),
        )
        if rag is None or rag.hit_count == 0:
            return refuse
        min_score = self._settings.rag_min_score
        scores = rag.scores or [min_score] * rag.hit_count
        if any(score < min_score for score in scores):
            return refuse
        rows = [
            KnowledgeTableRow(level="P1-P3", city_type="一线城市", limit_cny=800),
            KnowledgeTableRow(level="P1-P3", city_type="其他城市", limit_cny=600),
            KnowledgeTableRow(level="P4 及以上", city_type="一线城市", limit_cny=1200),
        ]
        answer_ids = {"know-travel-p1-tier1", "know-travel-reimburse"}
        selected = [item for item in rag.hits if item.knowledge_entry_id in answer_ids]
        if len(selected) < 2:
            selected = list(rag.hits)
        mapped: list[Citation] = []
        for item in selected:
            if item.knowledge_entry_id == "know-travel-p1-tier1":
                mapped.append(
                    item.model_copy(update={"excerpt": "一线城市 P1-P3 住宿标准不超过 800 元/晚。"})
                )
            elif item.knowledge_entry_id == "know-travel-reimburse":
                mapped.append(
                    item.model_copy(update={"excerpt": "差旅住宿以职级与城市类型对照表执行。"})
                )
            else:
                mapped.append(item)
        return ResultValidationOutcome(
            status="replied",
            result_status="success",
            citation_valid=True,
            citations=mapped,
            assistant_message=AssistantMessage(
                message_type="knowledge_table",
                text=(
                    "根据企业差旅管理制度，为您查询到住宿标准：\n\n"
                    "以上标准适用于公司正式员工的商务差旅，实际报销以发票和公司差旅制度为准。"
                ),
                table_rows=rows,
            ),
        )

    def _validate_skill(
        self, skill: SkillAdapterResult, tool_results: list[ToolResult]
    ) -> ResultValidationOutcome:
        if any(item.status == "timeout" for item in tool_results):
            return ResultValidationOutcome(
                status="unknown",
                result_status="unknown",
                assistant_message=AssistantMessage(
                    message_type="meeting_unknown",
                    text="已确认的会议信息仍保留，但系统未在约定等待内得到确定成功。",
                ),
            )
        if skill.confirmation is not None:
            return ResultValidationOutcome(
                status=skill.status,
                result_status="pending",
                assistant_message=AssistantMessage(
                    message_type="confirmation",
                    text=skill.text,
                    confirmation=skill.confirmation,
                ),
            )
        if skill.report_draft is not None:
            return ResultValidationOutcome(
                status="replied",
                result_status="success",
                assistant_message=AssistantMessage(
                    message_type="report_draft",
                    text=skill.text or "已命中技能：生成工作周报。按固定步骤生成本周周报，事实来自本轮工作消息。",
                    report_draft=skill.report_draft,
                ),
            )
        if skill.message_type == "disambiguation":
            return ResultValidationOutcome(
                status="clarifying",
                result_status="pending",
                assistant_message=AssistantMessage(
                    message_type="disambiguation",
                    text=skill.text,
                    choices=skill.choices,
                ),
            )
        if skill.message_type == "clarification":
            return ResultValidationOutcome(
                status="clarifying",
                result_status="pending",
                assistant_message=AssistantMessage(
                    message_type="clarification",
                    text=skill.text,
                ),
            )
        created = any(
            item.tool_id == "meeting_create" and item.status == "success" for item in tool_results
        )
        if created:
            return ResultValidationOutcome(
                status="replied",
                result_status="success",
                assistant_message=AssistantMessage(
                    message_type="meeting_success",
                    text="会议已创建。",
                ),
            )
        return ResultValidationOutcome(
            status=skill.status,
            result_status="success",
            assistant_message=AssistantMessage(
                message_type=skill.message_type,
                text=skill.text,
                choices=skill.choices,
                confirmation=skill.confirmation,
                report_draft=skill.report_draft,
            ),
        )

    def _rooms_from_tools(self, tool_results: list[ToolResult]) -> list[MeetingRoomItem]:
        rooms: list[MeetingRoomItem] = []
        for item in tool_results:
            payload = item.payload or {}
            raw_rooms = payload.get("rooms")
            if not isinstance(raw_rooms, list):
                continue
            for row in raw_rooms:
                if isinstance(row, dict):
                    rooms.append(MeetingRoomItem.model_validate(row))
        return rooms
