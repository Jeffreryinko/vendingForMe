-- 자판기 알림(웹 푸시) — 2026-11-14 수파베이스(mirbslsgmwfahwitpgsl)에 적용한 것의 기록
-- 플래너 알림의 열쇠(VAPID)·엣지 함수(planner, op=push)를 그대로 같이 씀.
--
-- 흐름: 로봇이 data/sisa/push.json(브리핑·큰 소식) 갱신 → 수파베이스가 15분마다 읽어 감
--       → 처음 보는 id면 그 주제를 켠 기기들에 보냄. 복습 알림은 매일 21:30(KST).
-- 로그인 없이 구독(엔드포인트 = 기기 하나). 표는 아무도 직접 못 읽고 아래 창구로만.
-- 주의: 이 도구로는 delete 문을 못 돌려서, 끄기 = 주제를 비우는 것으로 처리함(보낼 때 빈 주제는 제외).

create schema if not exists vfm_push;
create table if not exists public.vfm_push_subs (
  endpoint text primary key, p256dh text not null, auth text not null,
  topics text[] not null default '{brief,big,review}', ua text,
  created_at timestamptz not null default now(), test_at timestamptz);
alter table public.vfm_push_subs enable row level security;
revoke all on public.vfm_push_subs from anon, authenticated;
create table if not exists vfm_push.state (k text primary key, v text);           -- req = 마지막으로 보낸 http_get 번호
create table if not exists vfm_push.sent (id text primary key, at timestamptz not null default now());   -- 이미 보낸 소식 id
alter table vfm_push.state enable row level security;
alter table vfm_push.sent enable row level security;

-- 창구: 구독/주제 바꾸기 (주제 brief·big·review 만, 빈 배열 = 끔)
create or replace function public.vfm_push_sub(p_endpoint text, p_p256dh text, p_auth text, p_topics text[], p_ua text default null)
returns text language plpgsql security definer set search_path = '' as $$
declare t text[];
begin
  if p_endpoint is null or p_endpoint !~ '^https://' or length(p_endpoint) > 1000
     or length(coalesce(p_p256dh,'')) not between 20 and 200 or length(coalesce(p_auth,'')) not between 8 and 100 then
    raise exception 'bad subscription';
  end if;
  select coalesce(array_agg(distinct x), '{}') into t from unnest(coalesce(p_topics, '{}'::text[])) x where x in ('brief','big','review');
  if (select count(*) from public.vfm_push_subs) > 50000 then raise exception 'full'; end if;
  insert into public.vfm_push_subs (endpoint, p256dh, auth, topics, ua)
    values (p_endpoint, p_p256dh, p_auth, t, left(p_ua, 200))
  on conflict (endpoint) do update set p256dh = excluded.p256dh, auth = excluded.auth, topics = excluded.topics, ua = excluded.ua;
  return case when cardinality(t) = 0 then 'off' else 'ok' end;
end $$;
create or replace function public.vfm_push_unsub(p_endpoint text) returns void
language sql security definer set search_path = '' as $$ update public.vfm_push_subs set topics = '{}' where endpoint = p_endpoint $$;
-- 시험 알림: 그 기기 하나에만, 1분에 한 번
create or replace function public.vfm_push_test(p_endpoint text) returns integer
language plpgsql security definer set search_path = '' as $$
declare v_jobs jsonb;
begin
  update public.vfm_push_subs set test_at = now()
   where endpoint = p_endpoint and (test_at is null or test_at < now() - interval '1 minute');
  if not found then return 0; end if;
  select jsonb_agg(jsonb_build_object('endpoint', endpoint, 'p256dh', p256dh, 'auth', auth,
           'title', '알림이 켜졌어요', 'body', '아침·저녁 브리핑이 나오면 이렇게 알려 드릴게요.', 'tag', 'vfm-test', 'url', 'sisa/'))
    into v_jobs from public.vfm_push_subs where endpoint = p_endpoint;
  perform planner_private.dispatch(v_jobs);
  return 1;
end $$;
grant execute on function public.vfm_push_sub(text,text,text,text[],text), public.vfm_push_unsub(text), public.vfm_push_test(text) to anon, authenticated;

-- 주제 하나로 모두에게 (400개씩)
create or replace function vfm_push.send(p_topic text, p_title text, p_body text, p_url text, p_tag text) returns integer
language plpgsql security definer set search_path = '' as $$
declare v_jobs jsonb; n int := 0;
begin
  for v_jobs in
    select jsonb_agg(jsonb_build_object('endpoint', endpoint, 'p256dh', p256dh, 'auth', auth,
             'title', p_title, 'body', p_body, 'tag', p_tag, 'url', p_url))
    from (select (row_number() over (order by endpoint) - 1) / 400 as g, endpoint, p256dh, auth
          from public.vfm_push_subs where p_topic = any(topics)) q group by g
  loop
    perform planner_private.dispatch(v_jobs);
    n := n + jsonb_array_length(v_jobs);
  end loop;
  return n;
end $$;
create or replace function vfm_push.claim(p_id text) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  insert into vfm_push.sent (id) values (p_id) on conflict do nothing;
  return found;
end $$;
-- 15분마다: 지난번에 받아 둔 push.json 읽기 → 새 소식이면 보냄 → 다음 것 받아 두기
create or replace function vfm_push.poll() returns text
language plpgsql security definer set search_path = '' as $$
declare v_id bigint; v_body text; d jsonb; it jsonb; h int; r text := '';
begin
  select v::bigint into v_id from vfm_push.state where k = 'req';
  if v_id is not null then
    select content into v_body from net._http_response where id = v_id and status_code = 200;
    if v_body is not null then
      d := v_body::jsonb;
      h := extract(hour from now() at time zone 'Asia/Seoul');
      it := d->'brief';
      if it ? 'id' and vfm_push.claim(it->>'id') then
        r := r || 'brief:' || vfm_push.send('brief', it->>'title', it->>'body', it->>'url', 'vfm-brief') || ' ';
      end if;
      for it in select value from jsonb_array_elements(coalesce(d->'big', '[]'::jsonb)) loop
        if vfm_push.claim(it->>'id') and h between 7 and 22 then   -- 밤(23~6시)엔 큰 소식도 조용히
          r := r || 'big:' || vfm_push.send('big', it->>'title', it->>'body', it->>'url', 'vfm-big') || ' ';
        end if;
      end loop;
    end if;
  end if;
  v_id := net.http_get(url := 'https://jeffreryinko.github.io/vendingForMe/data/sisa/push.json?t=' || extract(epoch from now())::bigint,
                       timeout_milliseconds := 15000);
  insert into vfm_push.state (k, v) values ('req', v_id::text) on conflict (k) do update set v = excluded.v;
  return r;
end $$;

select cron.schedule('vfm-push-poll', '*/15 * * * *', 'select vfm_push.poll()');
select cron.schedule('vfm-push-review', '30 12 * * *',
  $$select vfm_push.send('review', '📚 오늘의 복습 3분', '어제 배운 것 몇 문제만 풀고 연속 기록을 이어가요.', 'sisa/learn/', 'vfm-review')$$);
