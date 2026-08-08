"""生成 8 周学习计划。用法：python3 scripts/generate_plan.py --model data/capability_model.json --gaps data/assessments/baseline.json --start 2026-08-10 --out data/learning_plan.json"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_pm.capability_model import CapabilityModel
from ai_pm.plan_generator import generate_plan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--gaps", required=True)
    ap.add_argument("--start", default="2026-08-10")
    ap.add_argument("--out", default="data/learning_plan.json")
    args = ap.parse_args()
    model = CapabilityModel.load(args.model)
    gaps = json.loads(pathlib.Path(args.gaps).read_text(encoding="utf-8"))["gaps"]
    plan = generate_plan(model, gaps, args.start)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print("计划已写入", args.out, "，共", len(plan["days"]), "个任务")


if __name__ == "__main__":
    main()
