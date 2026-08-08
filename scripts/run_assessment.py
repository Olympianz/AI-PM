"""入营测评：读题库交互答题，写基线画像。
用法：python3 scripts/run_assessment.py --profile data/user_profile.json --bank data/content/question_bank.json --case data/content/case_questions.json
"""
import argparse, json, pathlib, sys, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_pm.capability_model import CapabilityModel
from ai_pm.assessment import (score_objective, score_case, current_levels,
                              build_radar, priority_gaps)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--case", required=True)
    ap.add_argument("--model", default="data/capability_model.json")
    ap.add_argument("--out", default="data/assessments/baseline.json")
    args = ap.parse_args()
    model = CapabilityModel.load(args.model)
    bank = json.loads(pathlib.Path(args.bank).read_text(encoding="utf-8"))
    cases = json.loads(pathlib.Path(args.case).read_text(encoding="utf-8"))
    answers = {}
    for q in bank:
        print(f"{q['id']} [{q['capability_id']}] {q['question']}")
        for i, opt in enumerate(q["options"], 1):
            print(f"  {i}. {opt}")
        choice = input("答案编号（回车跳过）：").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(q["options"]):
            answers[q["id"]] = q["options"][int(choice) - 1][0]
    case_scores = {}
    for c in cases:
        print(f"\n案例题 {c['id']}：{c['question']}")
        answer = input("你的回答（多行用 \\n 分隔，回车结束）：").strip()
        case_scores[c["id"]] = score_case(answer, c["rubric"])
    obj_scores = score_objective(answers, bank)
    levels = current_levels(model, obj_scores, case_scores)
    radar = build_radar(model, levels)
    gaps = priority_gaps(model, levels)
    result = {"date": datetime.date.today().isoformat(), "type": "baseline",
              "objective_scores": obj_scores, "case_scores": case_scores,
              "levels": levels, "radar": radar, "gaps": gaps}
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n基线已写入", args.out, "；优先补强：")
    for g in gaps:
        print(f"  - {g['name']}（当前 L{g['current_level']} → 目标 L{g['target_level']}）")


if __name__ == "__main__":
    main()
