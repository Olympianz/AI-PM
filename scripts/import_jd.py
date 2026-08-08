"""导入 JD：解析原文并合并进能力模型。用法：
python3 scripts/import_jd.py --jd data/jds/deepseek-ai-pm.json --model data/capability_model.json --apply
"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_pm.capability_model import CapabilityModel
from ai_pm.jd_parser import import_jd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jd", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    model = CapabilityModel.load(args.model) if pathlib.Path(args.model).exists() else CapabilityModel()
    result = import_jd(args.jd, model)
    diff_path = pathlib.Path(args.jd).with_name("import-diff-" + pathlib.Path(args.jd).stem + ".json")
    diff_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("matched:", len(result["matched"]), "unmapped:", len(result["unmapped"]),
          "gates:", len(result["gates"]), "diff:", diff_path)
    if result["unmapped"]:
        print("待人工确认的行：")
        for line in result["unmapped"]:
            print("  -", line)
    if args.apply:
        model.save(args.model)
        print("已写入", args.model)


if __name__ == "__main__":
    main()
