# AI-PM

帮助有经验且具备 AI 基础知识的产品经理，在 2 个月内查漏补缺，达到大厂资深 AI 产品经理录用标准。

- 首个用户：作者本人（个人案例先行，成功后产品化）
- 核心思路：录用标准 → 能力模型 → 诊断 → 个性化路径 → 闭环验证 → 面试就绪度
- 设计规格：[docs/superpowers/specs/2026-08-08-ai-pm-design.md](docs/superpowers/specs/2026-08-08-ai-pm-design.md)
- 实现计划：[docs/superpowers/plans/2026-08-08-ai-pm.md](docs/superpowers/plans/2026-08-08-ai-pm.md)

## 部署与使用

**线上地址**：https://ai-pm-learn.vercel.app （Vercel 部署，Supabase 云同步）

1. 本地生成站点：`python3 scripts/build_site.py --data data --out site`；本地预览 `python3 -m http.server 8765 --directory site`
2. 线上部署：根目录配置了 `vercel.json`（`/` 路由到 `site/`，`/api/*` 走 serverless）与 `api/sync.py`（Supabase 云同步）。`vercel deploy --prod --yes` 即可发布。
3. 云端数据：`ai_pm_checkins / ai_pm_quiz_answers / ai_pm_artifacts / ai_pm_mocks` 四张表，由 `api/sync.py` 用 service role key 读写（密钥只在服务端环境变量中）。
4. 前端同步：打开首页点击「☁ 云端同步」上传本机数据；每次加载自动从云端拉取合并（在线时）。离线场景仍可用「导出文件」+ `scripts/sync_import.py` 回传。
5. 每日打卡：`python3 scripts/checkin.py --date <日期> --minutes <分钟> --task <任务id>`
6. 周报：`python3 scripts/report.py --end <本周日> --out data/reports/weekly-<日期>.md`
7. 新 JD：写入 `data/jds/raw/` 与 `data/jds/*.json` 后执行 `python3 scripts/import_jd.py --jd <文件> --model data/capability_model.json --apply`
