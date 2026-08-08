import json
from ai_pm.capability_model import CapabilityModel, CapabilityItem


def test_recompute_weights_normalizes_to_one(tmp_path):
    model = CapabilityModel(domains={"A": "AI 技术理解"})
    model.add_item(CapabilityItem(id="A1", domain="A", name="LLM 能力边界", weight=1.0))
    model.add_item(CapabilityItem(id="A2", domain="A", name="Agent 机制", weight=3.0))
    model.recompute_weights()
    assert model.find("A1").weight == 0.25
    assert model.find("A2").weight == 0.75


def test_save_load_roundtrip(tmp_path):
    path = str(tmp_path / "model.json")
    model = CapabilityModel(domains={"A": "AI 技术理解"})
    model.add_item(CapabilityItem(
        id="A1", domain="A", name="LLM 能力边界",
        behavioral_indicators=["能解释模型局限"], target_level=4, weight=1.0))
    model.save(path)
    loaded = CapabilityModel.load(path)
    item = loaded.find("A1")
    assert item.name == "LLM 能力边界"
    assert item.target_level == 4
    assert loaded.domain_weights() == {"A": 1.0}


def test_find_by_name_returns_none_when_missing():
    model = CapabilityModel()
    assert model.find_by_name("不存在") is None
