"""内容校验入口。用法：python3 scripts/validate_content.py --data data"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_pm.validate_content import validate_content


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    args = ap.parse_args()
    errors = validate_content(args.data)
    if errors:
        print("校验失败：")
        for e in errors:
            print("  -", e)
        raise SystemExit(1)
    print("内容校验通过")


if __name__ == "__main__":
    main()
