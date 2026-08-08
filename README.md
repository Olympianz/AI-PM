# AI-PM

帮助有经验且具备 AI 基础知识的产品经理，在 2 个月内查漏补缺，达到大厂资深 AI 产品经理录用标准。

- 首个用户：作者本人（个人案例先行，成功后产品化）
- 核心思路：录用标准 → 能力模型 → 诊断 → 个性化路径 → 闭环验证 → 面试就绪度
- 设计规格：[docs/superpowers/specs/2026-08-08-ai-pm-design.md](docs/superpowers/specs/2026-08-08-ai-pm-design.md)
- 实现计划：[docs/superpowers/plans/2026-08-08-ai-pm.md](docs/superpowers/plans/2026-08-08-ai-pm.md)

## 部署与使用

1. 生成站点：`python3 scripts/build_site.py --data data --out site`
2. 本地预览：`python3 -m http.server 8765 --directory site`
3. 手机访问（通勤）：将 `site/` 部署到 GitHub Pages 或 Vercel（静态托管），手机浏览器打开 HTTPS 地址，可添加到主屏作为 PWA 使用。
4. 离线：首次打开后 service worker 会缓存页面，弱网/离线仍可阅读当日知识卡。
5. 同步：手机端答题与打卡保存在浏览器 localStorage；点击「导出同步文件」生成 `ai-pm-sync.json`，用 `python3 scripts/sync_import.py --file <文件> --tracking data/tracking` 合并到本地跟踪。
6. 每日打卡：`python3 scripts/checkin.py --date <日期> --minutes <分钟> --task <任务id>`
7. 周报：`python3 scripts/report.py --end <本周日> --out data/reports/weekly-<日期>.md`
8. 新 JD：写入 `data/jds/raw/` 与 `data/jds/*.json` 后执行 `python3 scripts/import_jd.py --jd <文件> --model data/capability_model.json --apply`
