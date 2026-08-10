-- AI-PM 云同步表结构（api/sync.py 使用，主键与 upsert 的 on_conflict 保持一致）
-- 适用区域：新加坡 ap-southeast-1 或 东京 ap-northeast-1；不要使用美国区域。

create table if not exists public.ai_pm_checkins (
  date    text primary key,
  task_ids jsonb not null default '[]'::jsonb,
  minutes integer not null default 60
);

create table if not exists public.ai_pm_quiz_answers (
  date    text not null,
  quiz_id text not null,
  choice  text,
  primary key (date, quiz_id)
);

create table if not exists public.ai_pm_artifacts (
  id         text primary key,
  type       text,
  title      text,
  content    text,
  updated_at text
);

create table if not exists public.ai_pm_mocks (
  id          text primary key,
  date        text,
  section     text,
  question_id text,
  score       numeric,
  covered     numeric,
  total       numeric
);

create table if not exists public.ai_pm_topic_progress (
  topic_id text primary key,
  data     jsonb not null default '{}'::jsonb
);

create table if not exists public.ai_pm_tasks (
  date    text not null,
  task_id text not null,
  done    boolean not null default false,
  primary key (date, task_id)
);

create table if not exists public.ai_pm_read_cards (
  card_id text primary key,
  read_at text
);

create table if not exists public.ai_pm_bookmarks (
  card_id    text primary key,
  created_at text
);

create table if not exists public.ai_pm_gaps (
  id         text primary key,
  text       text not null,
  source     text not null default '',
  created_at text not null,
  status     text not null default 'open',
  topic_id   text,
  suggestion jsonb
);

create table if not exists public.ai_pm_topic_items (
  id         text primary key,
  topic_id   text not null,
  title      text not null,
  content    text not null,
  created_at text not null
);
