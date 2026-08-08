"""生成周报。用法：python3 scripts/report.py --plan data/learning_plan.json --tracking data/tracking --assessments data/assessments --end 2026-08-16 --out data/reports/weekly-2026-08-16.md"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_pm.report import write_weekly_report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="data/learning_plan.json")
    ap.add_argument("--tracking", default="data/tracking")
    ap.add_argument("--assessments", default="data/assessments")
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    write_weekly_report(args.plan, args.tracking, args.assessments, args.out, args.end)
    print("周报已写入", args.out)


if __name__ == "__main__":
    main()
