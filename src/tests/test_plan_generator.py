import json
from ai_pm.capability_model import CapabilityModel, CapabilityItem
from ai_pm.plan_generator import day_tasks, generate_plan


def make_gaps():
    return [{"item_id": "A2", "name": "Agent 机制"}, {"item_id": "C3", "name": "A/B 测试"},
            {"item_id": "B1", "name": "场景拆解"}, {"item_id": "E1", "name": "vibe coding"},
            {"item_id": "F1", "name": "项目管理"}]


def test_day_tasks_daily_split():
    tasks = day_tasks("2026-08-10", 1, 0, ["A2", "C3"], 150)
    assert [t["type"] for t in tasks] == ["input", "practice", "case"]
    assert sum(t["duration_min"] for t in tasks) == 150
    assert tasks[0]["duration_min"] == 60
    assert tasks[1]["duration_min"] == 60


def test_generate_plan_56_days_monday_start():
    model = CapabilityModel(domains={"A": "AI 技术理解"})
    model.add_item(CapabilityItem(id="A2", domain="A", name="Agent 机制", target_level=4, weight=1.0))
    plan = generate_plan(model, make_gaps(), "2026-08-10")
    assert plan["start_date"] == "2026-08-10"
    assert len(plan["days"]) == 56 * 3  # 56 天 × 每天 3 个任务
    assert len(plan["weeks"]) == 8
    first = plan["days"][0]
    assert first["date"] == "2026-08-10"
    assert first["week"] == 1
    sprint1 = plan["weeks"][0]["focus_ids"]
    assert sprint1 == ["A2", "C3"]
    total = sum(d["duration_min"] for d in plan["days"])
    assert total == 56 * 150


def test_plan_json_serializable():
    model = CapabilityModel()
    plan = generate_plan(model, make_gaps(), "2026-08-10")
    json.dumps(plan)  # 不应抛异常
