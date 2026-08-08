"""JD 解析：分节、关键字匹配能力项、导入能力模型。"""
from typing import Dict, List, Tuple
import json

from ai_pm.capability_model import CapabilityItem, CapabilityModel


SECTION_HEADERS = {"【工作职责】": "responsibilities",
                   "【核心要求】": "requirements",
                   "【加分项】": "plus"}
GATE_KEYWORDS = ["学历", "本科", "硕士", "年以上"]


def _domain_desc(domain: str) -> str:
    names = {"A": "AI 技术理解", "B": "产品设计与体验", "C": "数据与科学方法",
             "D": "战略与规划", "E": "工程协作与工具", "F": "软技能"}
    return names.get(domain, domain)


KEYWORD_MAP: Dict[str, Tuple[str, str, str]] = {
    "KV Cache": ("A", "性能与上下文工程", "理解 KV Cache、Context Engineering、Harness Engineering 等性能与上下文概念"),
    "Context Engineering": ("A", "性能与上下文工程", "理解 KV Cache、Context Engineering、Harness Engineering 等性能与上下文概念"),
    "Harness Engineering": ("A", "性能与上下文工程", "理解 KV Cache、Context Engineering、Harness Engineering 等性能与上下文概念"),
    "Agent Loop": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "Tool Use": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "Reasoning": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "Planning": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "Skills": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "MCP": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "Memory": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "Subagent": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "Multi-Agent": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "Agent 类产品": ("A", "Agent 机制与架构", "理解 Agent Loop、Tool Use、Reasoning、Planning、Skills、MCP、Memory、Subagent、Multi-Agent"),
    "LLM API": ("A", "LLM 能力边界与 API", "理解模型能力边界、LLM API 及其局限"),
    "模型能力边界": ("A", "LLM 能力边界与 API", "理解模型能力边界、LLM API 及其局限"),
    "Prompt Engineering": ("A", "Prompt Engineering 实践", "有 Prompt Engineering 第一手实践"),
    "问卷": ("C", "用户研究方法", "能设计问卷、访谈等系统性收集数据的方法"),
    "访谈": ("C", "用户研究方法", "能设计问卷、访谈等系统性收集数据的方法"),
    "A/B": ("C", "A/B 与灰度测试", "能设计并分析 A/B 测试与灰度测试"),
    "灰度": ("C", "A/B 与灰度测试", "能设计并分析 A/B 测试与灰度测试"),
    "统计": ("C", "统计分析", "使用统计学工具严谨分析数据"),
    "指标": ("C", "指标体系设计", "能定义与衡量产品价值的指标体系"),
    "行为数据": ("C", "数据驱动决策", "把用户体感、产品直觉与行为数据结合判断"),
    "数据分析": ("C", "数据驱动决策", "把用户体感、产品直觉与行为数据结合判断"),
    "体感": ("C", "数据驱动决策", "把用户体感、产品直觉与行为数据结合判断"),
    "用户任务": ("B", "场景识别与需求拆解", "从真实用户需求和使用场景出发定位产品问题"),
    "使用场景": ("B", "场景识别与需求拆解", "从真实用户需求和使用场景出发定位产品问题"),
    "用户需求": ("B", "场景识别与需求拆解", "从真实用户需求和使用场景出发定位产品问题"),
    "留存": ("B", "AI/对话/Agent 交互设计与体验", "降低使用门槛，提升使用深度、留存、粘性与转化"),
    "使用门槛": ("B", "AI/对话/Agent 交互设计与体验", "降低使用门槛，提升使用深度、留存、粘性与转化"),
    "产品体验": ("B", "AI/对话/Agent 交互设计与体验", "降低使用门槛，提升使用深度、留存、粘性与转化"),
    "异常分支": ("B", "边界条件与失败场景感知", "对异常分支、边界条件与失败场景有敏锐嗅觉"),
    "边界条件": ("B", "边界条件与失败场景感知", "对异常分支、边界条件与失败场景有敏锐嗅觉"),
    "失败场景": ("B", "边界条件与失败场景感知", "对异常分支、边界条件与失败场景有敏锐嗅觉"),
    "品味": ("B", "产品品味与细节", "有好的产品品味，注重日常交互细节"),
    "路线图": ("D", "产品路线图与优先级", "制定并执行产品路线图，合理规划优先级"),
    "优先级": ("D", "产品路线图与优先级", "制定并执行产品路线图，合理规划优先级"),
    "开放平台": ("D", "平台/开放/开发者产品", "有开放平台、开发者与生态产品意识"),
    "权衡": ("D", "技术与用户价值权衡", "在技术能力与用户价值之间寻找最佳路径"),
    "用户价值": ("D", "技术与用户价值权衡", "在技术能力与用户价值之间寻找最佳路径"),
    "vibe coding": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "写代码": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "AI coding": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "AI Coding": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "Workflow": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "Claude Code": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "Codex": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "Cursor": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "GitHub Copilot": ("E", "vibe coding / AI coding", "能使用 vibe coding 与 AI 工具写代码提升效率"),
    "原型": ("E", "AI 辅助原型与 UI/UX 设计", "具备 UI/UX 设计素养，能在 AI 辅助下完成原型与 UI 设计"),
    "UI": ("E", "AI 辅助原型与 UI/UX 设计", "具备 UI/UX 设计素养，能在 AI 辅助下完成原型与 UI 设计"),
    "研究员": ("E", "与研究员/工程师协作", "能与模型训练团队研究员、工程师深度协作"),
    "模型训练团队": ("E", "与研究员/工程师协作", "能与模型训练团队研究员、工程师深度协作"),
    "开源社区": ("E", "开源社区与开发者社群", "维护开源社区与开发者社群关系，能用英文书面沟通"),
    "社群": ("E", "开源社区与开发者社群", "维护开源社区与开发者社群关系，能用英文书面沟通"),
    "项目管理": ("F", "项目管理与交付", "推进需求从调研、方案、评审、开发到上线的完整交付"),
    "交付": ("F", "项目管理与交付", "推进需求从调研、方案、评审、开发到上线的完整交付"),
    "落地": ("F", "项目管理与交付", "推进需求从调研、方案、评审、开发到上线的完整交付"),
    "从业经验": ("F", "项目管理与交付", "推进需求从调研、方案、评审、开发到上线的完整交付"),
    "自驱": ("F", "自驱与独立推进", "自驱力强，能独立推进复杂项目的规划、排期与迭代"),
    "沟通": ("F", "沟通与协作", "沟通力强，能与多团队协作"),
    "英文": ("F", "英文书面沟通", "能用英文与开源社区、用户社群书面沟通"),
}


def split_sections(text: str) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {"mission": [], "responsibilities": [],
                                 "requirements": [], "plus": []}
    current = "mission"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        header = SECTION_HEADERS.get(line)
        if header:
            current = header
            continue
        out[current].append(line)
    return out


def match_capabilities(line: str) -> List[Tuple[str, str, str]]:
    hits: List[Tuple[str, str, str]] = []
    seen = set()
    for keyword, definition in KEYWORD_MAP.items():
        if keyword in line and keyword not in seen:
            hits.append(definition)
            seen.add(keyword)
    return hits


def _is_gate(line: str) -> bool:
    return any(k in line for k in GATE_KEYWORDS)


def import_jd(jd_path: str, model: CapabilityModel,
              weights: Dict[str, float] = None) -> dict:
    with open(jd_path, encoding="utf-8") as f:
        jd = json.load(f)
    with open(jd["raw_text_file"], encoding="utf-8") as f:
        sections = split_sections(f.read())
    weights = weights or {"mission": 0.5, "responsibilities": 1.0,
                          "requirements": 1.0, "plus": 0.5}
    matched: Dict[str, int] = {}
    unmapped: List[str] = []
    gates: List[str] = []
    for section, lines in sections.items():
        for line in lines:
            if _is_gate(line):
                gates.append(line)
                continue
            hits = match_capabilities(line)
            if not hits:
                if section in ("responsibilities", "requirements", "plus"):
                    unmapped.append(line)
                continue
            for domain, name, description in hits:
                item = model.find_by_name(name)
                if item is None:
                    item_id = _next_item_id(model, domain)
                    item = CapabilityItem(id=item_id, domain=domain, name=name,
                                          description=description, weight=0.0)
                    model.add_item(item)
                item.weight += weights.get(section, 0.5)
                if jd["id"] not in item.sources:
                    item.sources.append(jd["id"])
                matched[item.id] = matched.get(item.id, 0) + 1
    model.recompute_weights()
    return {"matched": matched, "unmapped": unmapped,
            "gates": gates, "items_added": [it.id for it in model.items]}


def _next_item_id(model: CapabilityModel, domain: str) -> str:
    n = 1
    while model.find(domain + str(n)) is not None:
        n += 1
    return domain + str(n)
