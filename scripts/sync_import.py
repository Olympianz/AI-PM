"""导入手机端同步文件。用法：python3 scripts/sync_import.py --file site/ai-pm-sync.json --tracking data/tracking"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_pm.sync import import_sync_file


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--tracking", default="data/tracking")
    args = ap.parse_args()
    result = import_sync_file(args.file, args.tracking)
    print("新增答题", result["quiz_answers_added"], "条；新增打卡", result["checkins_added"], "条")


if __name__ == "__main__":
    main()
