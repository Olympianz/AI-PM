from ai_pm.jd_parser import split_sections, match_capabilities, import_jd, GATE_KEYWORDS
from ai_pm.capability_model import CapabilityModel


def test_split_sections_by_headers():
    text = "使命行一\n使命行二\n【工作职责】\n职责一\n【核心要求】\n要求一\n【加分项】\n加分一"
    out = split_sections(text)
    assert out["mission"] == ["使命行一", "使命行二"]
    assert out["responsibilities"] == ["职责一"]
    assert out["requirements"] == ["要求一"]
    assert out["plus"] == ["加分一"]


def test_match_capabilities_keywords():
    line = "深度使用过 Claude Code，理解 LLM API 与 Agent Loop"
    hits = match_capabilities(line)
    names = {h[1] for h in hits}
    assert "Agent 机制与架构" in names
    assert "LLM 能力边界与 API" in names
    assert "vibe coding / AI coding" in names


def test_import_jd_creates_items_and_reports_unmapped(tmp_path):
    jd = tmp_path / "jd.json"
    raw = tmp_path / "jd.txt"
    jd.write_text('{"id":"t1","company":"C","title":"T","location":"L","raw_text_file":"%s"}' % raw)
    raw.write_text("【工作职责】\n规划产品路线图\n【核心要求】\n2年以上产品经理从业经验\n【加分项】\n爱好钢琴")
    model = CapabilityModel()
    result = import_jd(str(jd), model)
    assert "D1" in result["matched"]
    assert result["gates"] == ["2年以上产品经理从业经验"]
    assert result["unmapped"] == ["爱好钢琴"]
    assert "D1" in [it.id for it in model.items]
    assert "D" in model.domains
