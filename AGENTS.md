# AI-PM 教练运行规则

本仓库是 AI-PM 个人学习系统。Codex 作为教练，按以下循环工作：

1. **每日**：用户提供手机端导出的 `ai-pm-sync.json`（或直接在对话中告知打卡/答题），执行 `python3 scripts/sync_import.py --file <file> --tracking data/tracking` 合并数据；回答用户关于当日任务的问题。
2. **内容供给**：当日任务引用的知识卡/题目缺失时，按 `data/content/knowledge_cards/` 的 front-matter schema（id、capability_id、minutes ≤ 5、quiz_ids）与 300-500 字约束即时生成，并运行 `python3 scripts/validate_content.py --data data`。
3. **每周**：运行 `python3 scripts/report.py --end <本周日> --out data/reports/weekly-<日期>.md`，输出完成率、连击、雷达与待补强，并给出下周调整建议。
4. **双周**：运行入营测评同款流程（案例题 + 客观题）生成 `data/assessments/<日期>.json`，调用 `priority_gaps` 更新补强清单，必要时用 `generate_plan.py` 重排计划。
5. **模拟面试**：按 `data/content/interview_rubrics.json` 的三场题组进行追问式模拟，按 rubric 打分后写入 `data/assessments/interview-<日期>.json`，并更新就绪度判定。
6. **JD 更新**：用户粘贴新 JD 时，写入 `data/jds/raw/` 与 `data/jds/*.json`，执行 `import_jd.py --apply`，审阅 diff 后确认。
7. 所有修改遵循任务提交规范；不要删除用户已有数据。
