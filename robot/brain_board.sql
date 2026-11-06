-- 뇌 탭 '가족 점수판' 표 (Supabase → SQL Editor 에 붙여 넣고 Run, 한 번만)
-- 자판기에 구글로 로그인한 사람끼리만 서로 보임. 각자 자기 줄만 쓰고 지울 수 있음.
create table if not exists public.brain_board (
  user_id uuid primary key references auth.users(id) on delete cascade,
  name text not null default '',
  learned int not null default 0,      -- 외운 부위 (상자 3 이상)
  started int not null default 0,      -- 시작한 부위
  week int not null default 0,         -- 이번 주 복습 횟수
  streak int not null default 0,       -- 연속 일수
  ts bigint not null default 0
);
alter table public.brain_board enable row level security;
create policy "brain_board read (logged in)" on public.brain_board for select to authenticated using (true);
create policy "brain_board insert own" on public.brain_board for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "brain_board update own" on public.brain_board for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "brain_board delete own" on public.brain_board for delete to authenticated using ((select auth.uid()) = user_id);
