"""生成移动端站点。用法：python3 scripts/build_site.py --data data --out site --date 2026-08-10"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_pm.site_builder import build_site


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="site")
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    written = build_site(args.data, args.out, args.date)
    print("已生成", len(written), "个文件：", ", ".join(written[:8]), "...")


if __name__ == "__main__":
    main()
