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
3. 云端数据：`ai_pm_checkins / ai_pm_quiz_answers / ai_pm_artifacts / ai_pm_mocks / ai_pm_topic_progress / ai_pm_tasks / ai_pm_read_cards` 七张表，由 `api/sync.py` 用 service role key 读写（密钥只在服务端环境变量中）。
4. 前端同步：打开首页点击「☁ 云端同步」上传本机数据；每次加载自动从云端拉取合并（在线时）。离线场景仍可用「导出文件」+ `scripts/sync_import.py` 回传。
5. 每日打卡：`python3 scripts/checkin.py --date <日期> --minutes <分钟> --task <任务id>`

> **区域要求（中国大陆访问）**：Supabase 项目请创建在亚洲区域（推荐新加坡 `ap-southeast-1`，或东京 `ap-northeast-1`），不要选择美国区域。建表可直接执行 `supabase/schema.sql`。
6. 周报：`python3 scripts/report.py --end <本周日> --out data/reports/weekly-<日期>.md`
7. 新 JD：写入 `data/jds/raw/` 与 `data/jds/*.json` 后执行 `python3 scripts/import_jd.py --jd <文件> --model data/capability_model.json --apply`

## 主题学习（专题）

- 针对个人短板建专题（当前内置：用户体验设计与用户研究、A/B 测试与实验设计，可扩展 `data/content/topics.json`）。
- 每个专题包含：目标、学习模块（可勾选进度）、自测题、输出任务、推荐资源。
- AI 助手（DeepSeek，`api/ai.py` 代理，`DEEPSEEK_API_KEY` 只存在 Vercel 环境变量）：一键生成 4 周学习计划、出 5 道自测题、总结进度、自由提问。
- 专题进度随云同步（`ai_pm_topic_progress` 表）跨设备保存。
