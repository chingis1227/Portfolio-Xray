-- Portfolio MRI account workspace schema extension.
--
-- Apply this file once in the Supabase SQL Editor after supabase_free_schema.sql.
-- It is additive and idempotent: it only adds compact workspace/profile/version fields,
-- archive markers, and review-to-version links. It does not store generated artifacts.

create extension if not exists pgcrypto;

alter table public.profiles
  add column if not exists client_fit_profile jsonb not null default '{}'::jsonb,
  add column if not exists onboarding_completed_at timestamptz,
  add column if not exists client_fit_updated_at timestamptz;

alter table public.portfolios
  add column if not exists archived_at timestamptz;

create table if not exists public.portfolio_versions (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  version_number integer not null,
  base_currency text not null default 'USD',
  holdings_snapshot jsonb not null default '[]'::jsonb,
  input_fingerprint text,
  source_kind text not null default 'manual',
  source_review_id text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint portfolio_versions_version_number_positive check (version_number > 0),
  constraint portfolio_versions_base_currency_not_blank check (length(btrim(base_currency)) > 0),
  constraint portfolio_versions_source_kind_not_blank check (length(btrim(source_kind)) > 0),
  constraint portfolio_versions_user_portfolio_version_unique unique (user_id, portfolio_id, version_number),
  constraint portfolio_versions_user_fingerprint_unique unique (user_id, portfolio_id, input_fingerprint)
);

alter table public.reviews
  add column if not exists portfolio_version_id uuid references public.portfolio_versions(id) on delete set null,
  add column if not exists archived_at timestamptz;

create table if not exists public.workspace_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  active_portfolio_id uuid references public.portfolios(id) on delete set null,
  active_portfolio_version_id uuid references public.portfolio_versions(id) on delete set null,
  active_review_row_id uuid references public.reviews(id) on delete set null,
  last_opened_review_row_id uuid references public.reviews(id) on delete set null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists profiles_onboarding_completed_at_idx
  on public.profiles(onboarding_completed_at desc)
  where onboarding_completed_at is not null;
create index if not exists portfolios_user_id_archived_at_updated_at_idx
  on public.portfolios(user_id, archived_at, updated_at desc);
create index if not exists portfolio_versions_portfolio_id_version_number_idx
  on public.portfolio_versions(portfolio_id, version_number desc);
create index if not exists portfolio_versions_user_id_created_at_idx
  on public.portfolio_versions(user_id, created_at desc);
create index if not exists portfolio_versions_input_fingerprint_idx
  on public.portfolio_versions(user_id, portfolio_id, input_fingerprint)
  where input_fingerprint is not null;
create index if not exists reviews_portfolio_version_id_idx
  on public.reviews(portfolio_version_id);
create index if not exists reviews_user_id_archived_at_updated_at_idx
  on public.reviews(user_id, archived_at, updated_at desc);
create index if not exists workspace_state_active_portfolio_id_idx
  on public.workspace_state(active_portfolio_id);
create index if not exists workspace_state_active_review_row_id_idx
  on public.workspace_state(active_review_row_id);

do $$
begin
  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_portfolio_versions_set_updated_at'
  ) then
    create trigger pmri_portfolio_versions_set_updated_at
      before update on public.portfolio_versions
      for each row execute function public.pmri_set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_workspace_state_set_updated_at'
  ) then
    create trigger pmri_workspace_state_set_updated_at
      before update on public.workspace_state
      for each row execute function public.pmri_set_updated_at();
  end if;
end;
$$;

alter table public.portfolio_versions enable row level security;
alter table public.workspace_state enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolio_versions' and policyname = 'pmri_portfolio_versions_select_own'
  ) then
    create policy pmri_portfolio_versions_select_own
      on public.portfolio_versions for select
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_versions.portfolio_id
            and p.user_id = auth.uid()
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolio_versions' and policyname = 'pmri_portfolio_versions_insert_own'
  ) then
    create policy pmri_portfolio_versions_insert_own
      on public.portfolio_versions for insert
      with check (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_versions.portfolio_id
            and p.user_id = auth.uid()
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolio_versions' and policyname = 'pmri_portfolio_versions_update_own'
  ) then
    create policy pmri_portfolio_versions_update_own
      on public.portfolio_versions for update
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_versions.portfolio_id
            and p.user_id = auth.uid()
        )
      )
      with check (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_versions.portfolio_id
            and p.user_id = auth.uid()
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolio_versions' and policyname = 'pmri_portfolio_versions_delete_own'
  ) then
    create policy pmri_portfolio_versions_delete_own
      on public.portfolio_versions for delete
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_versions.portfolio_id
            and p.user_id = auth.uid()
        )
      );
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'workspace_state' and policyname = 'pmri_workspace_state_select_own'
  ) then
    create policy pmri_workspace_state_select_own
      on public.workspace_state for select
      using (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'workspace_state' and policyname = 'pmri_workspace_state_insert_own'
  ) then
    create policy pmri_workspace_state_insert_own
      on public.workspace_state for insert
      with check (
        user_id = auth.uid()
        and (
          active_portfolio_id is null
          or exists (
            select 1 from public.portfolios p
            where p.id = workspace_state.active_portfolio_id
              and p.user_id = auth.uid()
          )
        )
        and (
          active_portfolio_version_id is null
          or exists (
            select 1 from public.portfolio_versions pv
            where pv.id = workspace_state.active_portfolio_version_id
              and pv.user_id = auth.uid()
          )
        )
        and (
          active_review_row_id is null
          or exists (
            select 1 from public.reviews r
            where r.id = workspace_state.active_review_row_id
              and r.user_id = auth.uid()
          )
        )
        and (
          last_opened_review_row_id is null
          or exists (
            select 1 from public.reviews r
            where r.id = workspace_state.last_opened_review_row_id
              and r.user_id = auth.uid()
          )
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'workspace_state' and policyname = 'pmri_workspace_state_update_own'
  ) then
    create policy pmri_workspace_state_update_own
      on public.workspace_state for update
      using (user_id = auth.uid())
      with check (
        user_id = auth.uid()
        and (
          active_portfolio_id is null
          or exists (
            select 1 from public.portfolios p
            where p.id = workspace_state.active_portfolio_id
              and p.user_id = auth.uid()
          )
        )
        and (
          active_portfolio_version_id is null
          or exists (
            select 1 from public.portfolio_versions pv
            where pv.id = workspace_state.active_portfolio_version_id
              and pv.user_id = auth.uid()
          )
        )
        and (
          active_review_row_id is null
          or exists (
            select 1 from public.reviews r
            where r.id = workspace_state.active_review_row_id
              and r.user_id = auth.uid()
          )
        )
        and (
          last_opened_review_row_id is null
          or exists (
            select 1 from public.reviews r
            where r.id = workspace_state.last_opened_review_row_id
              and r.user_id = auth.uid()
          )
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'workspace_state' and policyname = 'pmri_workspace_state_delete_own'
  ) then
    create policy pmri_workspace_state_delete_own
      on public.workspace_state for delete
      using (user_id = auth.uid());
  end if;
end;
$$;

comment on column public.profiles.client_fit_profile is
  'Compact Client Fit profile fields for account workspace hydration; no raw generated artifacts.';
comment on column public.profiles.onboarding_completed_at is
  'Timestamp marking that the signed-in user completed the required onboarding journey.';
comment on column public.profiles.client_fit_updated_at is
  'Timestamp for the last compact Client Fit profile update.';
comment on column public.portfolios.archived_at is
  'Soft archive marker. Archived portfolios are hidden from default workspace lists without hard deletion.';
comment on table public.portfolio_versions is
  'Immutable compact snapshots of saved portfolio input used by draft or completed reviews.';
comment on column public.reviews.portfolio_version_id is
  'Optional link from a compact review row to the immutable portfolio version analyzed by that review.';
comment on column public.reviews.archived_at is
  'Soft archive marker. Archived reviews are hidden from default workspace history without hard deletion.';
comment on table public.workspace_state is
  'One compact workspace pointer row per user. It stores active portfolio/review ids only, not generated artifacts.';

-- Refresh review write policies so portfolio_version_id cannot point to another user's snapshot.
drop policy if exists pmri_reviews_insert_own on public.reviews;
create policy pmri_reviews_insert_own
  on public.reviews for insert
  with check (
    user_id = auth.uid()
    and (
      portfolio_id is null
      or exists (
        select 1 from public.portfolios p
        where p.id = reviews.portfolio_id
          and p.user_id = auth.uid()
      )
    )
    and (
      portfolio_version_id is null
      or exists (
        select 1 from public.portfolio_versions pv
        where pv.id = reviews.portfolio_version_id
          and pv.user_id = auth.uid()
          and (reviews.portfolio_id is null or pv.portfolio_id = reviews.portfolio_id)
      )
    )
  );

drop policy if exists pmri_reviews_update_own on public.reviews;
create policy pmri_reviews_update_own
  on public.reviews for update
  using (user_id = auth.uid())
  with check (
    user_id = auth.uid()
    and (
      portfolio_id is null
      or exists (
        select 1 from public.portfolios p
        where p.id = reviews.portfolio_id
          and p.user_id = auth.uid()
      )
    )
    and (
      portfolio_version_id is null
      or exists (
        select 1 from public.portfolio_versions pv
        where pv.id = reviews.portfolio_version_id
          and pv.user_id = auth.uid()
          and (reviews.portfolio_id is null or pv.portfolio_id = reviews.portfolio_id)
      )
    )
  );
