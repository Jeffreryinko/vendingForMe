-- 매일 업무 플래너 — Supabase 구성 (기존 vendingforme 프로젝트에 "추가"만 합니다. 기존 표·작업은 건드리지 않음)
-- 공개(public): planner_items / planner_push_subs / planner_shares  — 모두 행 보안(RLS): 각자 자기 것만
-- 비공개(planner_private): 비밀값·구글 토큰·보낸 알림 기록 — API 로는 접근 불가

create schema if not exists planner_private;
revoke all on schema planner_private from public, anon, authenticated;
create sequence if not exists planner_private.rev_seq;

-- 1) 모든 기록(할 일·시간 블록·하루 기록·설정)은 한 표에, 한 줄 = 한 항목
create table if not exists public.planner_items (
  user_id    uuid    not null default auth.uid() references auth.users(id) on delete cascade,
  id         text    not null check (char_length(id) between 1 and 64),
  kind       text    not null check (char_length(kind) between 1 and 16),
  data       jsonb   not null default '{}'::jsonb check (pg_column_size(data) < 60000),
  updated_at bigint  not null,              -- 기기에서 고친 시각(ms). 더 최신 것이 이김
  deleted    boolean not null default false,
  rev        bigint  not null,              -- 서버가 매기는 순번. 기기는 "이 번호 이후"만 받아감
  primary key (user_id, id)
);
create index if not exists planner_items_rev on public.planner_items (user_id, rev);
create index if not exists planner_items_block_date on public.planner_items (user_id, (data->>'date')) where kind = 'block' and not deleted;
alter table public.planner_items enable row level security;
drop policy if exists planner_items_own on public.planner_items;
create policy planner_items_own on public.planner_items for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
revoke all on public.planner_items from anon;
grant select, insert, update, delete on public.planner_items to authenticated;

create or replace function planner_private.items_touch() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if tg_op = 'UPDATE' and new.updated_at < old.updated_at then return null; end if;  -- 더 오래된 수정은 버림
  new.rev := nextval('planner_private.rev_seq');
  return new;
end $$;
drop trigger if exists planner_items_touch on public.planner_items;
create trigger planner_items_touch before insert or update on public.planner_items
  for each row execute function planner_private.items_touch();

-- 2) 알림 받을 기기
create table if not exists public.planner_push_subs (
  endpoint   text primary key check (char_length(endpoint) < 2000),
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  p256dh     text not null,
  auth       text not null,
  ua         text,
  created_at timestamptz not null default now()
);
create index if not exists planner_push_subs_user on public.planner_push_subs (user_id);
alter table public.planner_push_subs enable row level security;
drop policy if exists planner_push_subs_own on public.planner_push_subs;
create policy planner_push_subs_own on public.planner_push_subs for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
revoke all on public.planner_push_subs from anon;
grant select, insert, update, delete on public.planner_push_subs to authenticated;

-- 3) 공유 링크 (주소를 아는 사람만 읽기)
create table if not exists public.planner_shares (
  id         text primary key check (char_length(id) between 20 and 64),
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  payload    jsonb not null check (pg_column_size(payload) < 200000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists planner_shares_user on public.planner_shares (user_id);
alter table public.planner_shares enable row level security;
drop policy if exists planner_shares_own on public.planner_shares;
create policy planner_shares_own on public.planner_shares for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
revoke all on public.planner_shares from anon;
grant select, insert, update, delete on public.planner_shares to authenticated;

create or replace function public.planner_share_get(p_id text) returns jsonb
language sql stable security definer set search_path = '' as $$
  select payload from public.planner_shares where id = p_id
$$;
revoke all on function public.planner_share_get(text) from public;
grant execute on function public.planner_share_get(text) to anon, authenticated;

-- 4) 비공개 표
create table if not exists planner_private.secrets (name text primary key, value text not null);
create table if not exists planner_private.google_tokens (
  user_id uuid primary key references auth.users(id) on delete cascade,
  refresh_token text not null, updated_at timestamptz not null default now());
create table if not exists planner_private.sent (
  user_id uuid not null, key text not null, at timestamptz not null default now(), primary key (user_id, key));
alter table planner_private.secrets enable row level security;
alter table planner_private.google_tokens enable row level security;
alter table planner_private.sent enable row level security;
insert into planner_private.secrets (name, value)
  values ('tick_key', replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', ''))
  on conflict do nothing;

-- 5) 알림 보내기: DB가 "지금 보낼 알림"을 고르고, 있을 때만 엣지 함수를 부름
create or replace function planner_private.dispatch(p_jobs jsonb) returns void
language plpgsql security definer set search_path = '' as $$
declare v_key text;
begin
  select value into v_key from planner_private.secrets where name = 'tick_key';
  perform net.http_post(
    url := 'https://mirbslsgmwfahwitpgsl.supabase.co/functions/v1/planner',
    body := jsonb_build_object('op', 'push', 'jobs', p_jobs),
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-tick-key', v_key),
    timeout_milliseconds := 20000);
end $$;
revoke all on function planner_private.dispatch(jsonb) from public, anon, authenticated;

create or replace function planner_private.tick() returns integer
language plpgsql security definer set search_path = '' as $$
declare v_jobs jsonb;
begin
  -- 알림용 열쇠쌍이 아직 없으면 엣지 함수에게 만들어 달라고 부탁 (함수가 배포되면 한 번만 실행됨)
  if not exists (select 1 from planner_private.secrets where name = 'vapid_public') then
    perform net.http_post(
      url := 'https://mirbslsgmwfahwitpgsl.supabase.co/functions/v1/planner',
      body := jsonb_build_object('op', 'init'),
      headers := jsonb_build_object('Content-Type', 'application/json', 'x-tick-key', (select value from planner_private.secrets where name = 'tick_key')),
      timeout_milliseconds := 20000);
    return 0;
  end if;
  with u as (
    select distinct user_id from public.planner_push_subs
  ), cfg as (
    select u.user_id, coalesce(i.data, '{}'::jsonb) as s
    from u left join public.planner_items i on i.user_id = u.user_id and i.id = 'settings' and not i.deleted
  ), ctx as (
    select user_id, s,
      now() at time zone (case when exists (select 1 from pg_catalog.pg_timezone_names z where z.name = s->>'tz')
                               then s->>'tz' else 'Asia/Seoul' end) as ln
    from cfg
  ), c as (
    select user_id, s, to_char(ln, 'YYYY-MM-DD') as d,
      (extract(hour from ln) * 60 + extract(minute from ln))::int as nm,
      extract(isodow from ln)::int as dow,
      case when (s->>'remindMin') ~ '^\d{1,3}$' then (s->>'remindMin')::int else 5 end as rm,
      coalesce(s->'remindAtStart', 'true'::jsonb) <> 'false'::jsonb as ras,
      coalesce(s->'weekdaysOnly', 'true'::jsonb) <> 'false'::jsonb as wd,
      case when (s->>'morningTime') ~ '^\d\d:\d\d$'
           then substr(s->>'morningTime', 1, 2)::int * 60 + substr(s->>'morningTime', 4, 2)::int
           when s ? 'morningTime' then null else 530 end as mm
    from ctx
  ), b as (
    select c.user_id, i.id, c.nm, c.rm, c.ras, c.d,
      coalesce(nullif(i.data->>'title', ''), '시간 블록') as title,
      (i.data->>'start') as st, coalesce(i.data->>'end', '') as en,
      substr(i.data->>'start', 1, 2)::int * 60 + substr(i.data->>'start', 4, 2)::int as sm
    from c join public.planner_items i
      on i.user_id = c.user_id and i.kind = 'block' and not i.deleted and i.data->>'date' = c.d
    where (i.data->>'start') ~ '^\d\d:\d\d$' and coalesce(i.data->'done', 'false'::jsonb) <> 'true'::jsonb
  ), ev as (
    select user_id, 'b:' || id || ':p:' || d || ':' || st as key,
      rm || '분 뒤 · ' || title as title, st || ' – ' || en as body, 'b-' || id as tag
    from b where rm > 0 and nm >= sm - rm and nm < least(sm, sm - rm + 3)
    union all
    select user_id, 'b:' || id || ':s:' || d || ':' || st,
      '지금 시작 · ' || title, st || ' – ' || en, 'b-' || id
    from b where ras and nm >= sm and nm < sm + 3
    union all
    select c.user_id, 'm:' || c.d, '오늘의 핵심 3가지를 골라 보세요',
      concat_ws(' · ',
        '시간 블록 ' || (select count(*) from public.planner_items i where i.user_id = c.user_id and i.kind = 'block' and not i.deleted and i.data->>'date' = c.d) || '개',
        (select '119 긴급 ' || count(*) || '건' from public.planner_items i where i.user_id = c.user_id and i.kind = 'task' and not i.deleted
            and i.data->>'cat' = '1' and coalesce(i.data->>'st', 'open') = 'open' having count(*) > 0),
        (select '마감 ' || count(*) || '건' from public.planner_items i where i.user_id = c.user_id and i.kind = 'task' and not i.deleted
            and coalesce(i.data->>'st', 'open') = 'open' and (i.data->>'due') ~ '^\d{4}-\d\d-\d\d$' and i.data->>'due' <= c.d having count(*) > 0),
        (select '기다리는 일 ' || count(*) || '건' from public.planner_items i where i.user_id = c.user_id and i.kind = 'task' and not i.deleted
            and i.data->>'st' = 'wait' having count(*) > 0)),
      'morning'
    from c where c.mm is not null and c.nm >= c.mm and c.nm < c.mm + 3 and not (c.wd and c.dow in (6, 7))
  ), claimed as (
    insert into planner_private.sent (user_id, key) select user_id, key from ev
    on conflict do nothing returning user_id, key
  )
  select jsonb_agg(jsonb_build_object('endpoint', p.endpoint, 'p256dh', p.p256dh, 'auth', p.auth,
                                      'title', ev.title, 'body', ev.body, 'tag', ev.tag))
  into v_jobs
  from claimed k join ev on ev.user_id = k.user_id and ev.key = k.key
  join public.planner_push_subs p on p.user_id = k.user_id;

  if v_jobs is null then return 0; end if;
  perform planner_private.dispatch(v_jobs);
  return jsonb_array_length(v_jobs);
end $$;
revoke all on function planner_private.tick() from public, anon, authenticated;

-- 6) 앱·엣지 함수가 부르는 창구 (모두 본인 확인 또는 열쇠 확인)
create or replace function public.planner_vapid_public() returns text
language sql stable security definer set search_path = '' as $$
  select value from planner_private.secrets where name = 'vapid_public'
$$;
revoke all on function public.planner_vapid_public() from public;
grant execute on function public.planner_vapid_public() to anon, authenticated;

create or replace function public.planner_push_test() returns integer
language plpgsql security definer set search_path = '' as $$
declare v_jobs jsonb;
begin
  if auth.uid() is null then raise exception 'login required'; end if;
  select jsonb_agg(jsonb_build_object('endpoint', endpoint, 'p256dh', p256dh, 'auth', auth,
           'title', '알림 테스트', 'body', '이 기기에서 알림이 잘 옵니다.', 'tag', 'test'))
    into v_jobs from public.planner_push_subs where user_id = auth.uid();
  if v_jobs is null then return 0; end if;
  perform planner_private.dispatch(v_jobs);
  return jsonb_array_length(v_jobs);
end $$;
revoke all on function public.planner_push_test() from public, anon;
grant execute on function public.planner_push_test() to authenticated;

create or replace function public.planner_google_set(p_token text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'login required'; end if;
  if p_token is null or char_length(p_token) not between 10 and 2000 then raise exception 'bad token'; end if;
  insert into planner_private.google_tokens (user_id, refresh_token) values (auth.uid(), p_token)
  on conflict (user_id) do update set refresh_token = excluded.refresh_token, updated_at = now();
end $$;
create or replace function public.planner_google_get() returns text
language sql stable security definer set search_path = '' as $$
  select refresh_token from planner_private.google_tokens where user_id = auth.uid()
$$;
create or replace function public.planner_google_clear() returns void
language sql security definer set search_path = '' as $$
  delete from planner_private.google_tokens where user_id = auth.uid()
$$;
revoke all on function public.planner_google_set(text), public.planner_google_get(), public.planner_google_clear() from public, anon;
grant execute on function public.planner_google_set(text), public.planner_google_get(), public.planner_google_clear() to authenticated;

create or replace function planner_private.check_key(p_key text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if p_key is null or not exists (select 1 from planner_private.secrets where name = 'tick_key' and value = p_key)
  then raise exception 'forbidden'; end if;
end $$;

create or replace function public.planner_fn_ctx(p_key text) returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  perform planner_private.check_key(p_key);
  return jsonb_build_object(
    'pub',  (select value from planner_private.secrets where name = 'vapid_public'),
    'priv', (select value from planner_private.secrets where name = 'vapid_private'));
end $$;
create or replace function public.planner_fn_set_vapid(p_key text, p_pub text, p_priv text) returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  perform planner_private.check_key(p_key);
  if not exists (select 1 from planner_private.secrets where name = 'vapid_public') then
    insert into planner_private.secrets (name, value) values ('vapid_public', p_pub), ('vapid_private', p_priv)
    on conflict do nothing;
  end if;
  return public.planner_fn_ctx(p_key);
end $$;
create or replace function public.planner_fn_prune(p_key text, p_endpoints text[]) returns integer
language plpgsql security definer set search_path = '' as $$
declare n integer;
begin
  perform planner_private.check_key(p_key);
  delete from public.planner_push_subs where endpoint = any(p_endpoints);
  get diagnostics n = row_count;
  return n;
end $$;
revoke all on function public.planner_fn_ctx(text), public.planner_fn_set_vapid(text, text, text), public.planner_fn_prune(text, text[]) from public;
grant execute on function public.planner_fn_ctx(text), public.planner_fn_set_vapid(text, text, text), public.planner_fn_prune(text, text[]) to anon, authenticated;

-- 7) 예약 작업: 1분마다 알림 확인, 하루 한 번 청소
select cron.unschedule(jobname) from cron.job where jobname in ('planner-tick', 'planner-tidy');
select cron.schedule('planner-tick', '* * * * *', 'select planner_private.tick()');
select cron.schedule('planner-tidy', '13 18 * * *', $$
  delete from planner_private.sent where at < now() - interval '3 days';
  delete from cron.job_run_details where jobid in (select jobid from cron.job where jobname = 'planner-tick') and end_time < now() - interval '1 day';
$$);
