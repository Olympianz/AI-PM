"""每日打卡。用法：python3 scripts/checkin.py --date 2026-08-10 --minutes 150 --task 2026-08-10-input"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_pm.tracking import record_checkin, read_jsonl, streak


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--minutes", type=int, required=True)
    ap.add_argument("--task", action="append", default=[])
    ap.add_argument("--out", default="data/tracking/checkins.jsonl")
    args = ap.parse_args()
    record_checkin(args.out, args.date, args.task, args.minutes)
    print("已记录", args.date, args.minutes, "分钟；当前连击", streak(read_jsonl(args.out)), "天")


if __name__ == "__main__":
    main()
