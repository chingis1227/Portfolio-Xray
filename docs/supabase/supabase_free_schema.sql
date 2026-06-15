-- Portfolio MRI / Portfolio X-Ray optional Supabase Free app-data schema.
--
-- Apply this file manually in the Supabase SQL Editor. It creates the
-- lightweight persistence layer used by the frontend when Supabase is enabled.
-- It intentionally stores compact app records only: profiles, portfolios,
-- holdings, compact review summaries, compact stage summaries, and verdicts.
--
-- Do not use this database as an analytics engine or generated-artifact store.
-- The application must not upload runs/, Main portfolio/, cache/, pdf files/,
-- generated candidate folders, full portfolio_xray.json, full stress_report.json,
-- price history, parquet, CSV exports, PDFs, or other generated evidence here.

create extension if not exists pgcrypto;

create or replace function public.pmri_set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email text,
  display_name text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.portfolios (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  description text,
  base_currency text not null default 'USD',
  risk_profile text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint portfolios_name_not_blank check (length(btrim(name)) > 0),
  constraint portfolios_base_currency_not_blank check (length(btrim(base_currency)) > 0)
);

create table if not exists public.portfolio_holdings (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  ticker text not null,
  name text,
  asset_class text,
  weight numeric,
  quantity numeric,
  market_value numeric,
  currency text,
  metadata jsonb not null default '{}'::jsonb,
  sort_order integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint portfolio_holdings_ticker_not_blank check (length(btrim(ticker)) > 0),
  constraint portfolio_holdings_weight_range check (weight is null or (weight >= 0 and weight <= 1))
);

create table if not exists public.reviews (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  portfolio_id uuid references public.portfolios(id) on delete set null,
  review_id text not null,
  title text,
  mode text,
  status text not null default 'created',
  portfolio_snapshot jsonb not null default '{}'::jsonb,
  compact_summary jsonb not null default '{}'::jsonb,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint reviews_review_id_not_blank check (length(btrim(review_id)) > 0),
  constraint reviews_user_review_id_unique unique (user_id, review_id)
);

create table if not exists public.review_stage_summaries (
  id uuid primary key default gen_random_uuid(),
  review_row_id uuid not null references public.reviews(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  review_id text not null,
  stage text not null,
  status text not null default 'saved',
  summary jsonb not null default '{}'::jsonb,
  summary_size_bytes integer,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint review_stage_summaries_review_id_not_blank check (length(btrim(review_id)) > 0),
  constraint review_stage_summaries_stage_check check (
    stage in (
      'diagnosis',
      'builder',
      'input',
      'data_load',
      'xray',
      'stress',
      'client_fit',
      'problem_classification',
      'launchpad_builder',
      'candidate',
      'comparison',
      'verdict',
      'report'
    )
  ),
  constraint review_stage_summaries_summary_size_nonnegative check (
    summary_size_bytes is null or summary_size_bytes >= 0
  ),
  constraint review_stage_summaries_unique_stage unique (review_row_id, stage)
);

create table if not exists public.verdicts (
  id uuid primary key default gen_random_uuid(),
  review_row_id uuid not null references public.reviews(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  review_id text not null,
  verdict text,
  confidence numeric,
  rationale text,
  summary jsonb not null default '{}'::jsonb,
  limitations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint verdicts_review_id_not_blank check (length(btrim(review_id)) > 0),
  constraint verdicts_confidence_range check (confidence is null or (confidence >= 0 and confidence <= 1)),
  constraint verdicts_unique_review unique (review_row_id)
);

create index if not exists profiles_email_idx on public.profiles(email);
create index if not exists portfolios_user_id_updated_at_idx on public.portfolios(user_id, updated_at desc);
create index if not exists portfolio_holdings_portfolio_id_sort_order_idx
  on public.portfolio_holdings(portfolio_id, sort_order, ticker);
create index if not exists portfolio_holdings_user_id_idx on public.portfolio_holdings(user_id);
create index if not exists reviews_user_id_updated_at_idx on public.reviews(user_id, updated_at desc);
create index if not exists reviews_portfolio_id_idx on public.reviews(portfolio_id);
create index if not exists review_stage_summaries_user_id_stage_idx
  on public.review_stage_summaries(user_id, stage, updated_at desc);
create index if not exists review_stage_summaries_review_id_idx
  on public.review_stage_summaries(review_id);
create index if not exists verdicts_user_id_updated_at_idx on public.verdicts(user_id, updated_at desc);

alter table public.review_stage_summaries
  drop constraint if exists review_stage_summaries_stage_check;

alter table public.review_stage_summaries
  add constraint review_stage_summaries_stage_check check (
    stage in (
      'diagnosis',
      'builder',
      'input',
      'data_load',
      'xray',
      'stress',
      'client_fit',
      'problem_classification',
      'launchpad_builder',
      'candidate',
      'comparison',
      'verdict',
      'report'
    )
  );

do $$
begin
  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_profiles_set_updated_at'
  ) then
    create trigger pmri_profiles_set_updated_at
      before update on public.profiles
      for each row execute function public.pmri_set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_portfolios_set_updated_at'
  ) then
    create trigger pmri_portfolios_set_updated_at
      before update on public.portfolios
      for each row execute function public.pmri_set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_portfolio_holdings_set_updated_at'
  ) then
    create trigger pmri_portfolio_holdings_set_updated_at
      before update on public.portfolio_holdings
      for each row execute function public.pmri_set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_reviews_set_updated_at'
  ) then
    create trigger pmri_reviews_set_updated_at
      before update on public.reviews
      for each row execute function public.pmri_set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_review_stage_summaries_set_updated_at'
  ) then
    create trigger pmri_review_stage_summaries_set_updated_at
      before update on public.review_stage_summaries
      for each row execute function public.pmri_set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_verdicts_set_updated_at'
  ) then
    create trigger pmri_verdicts_set_updated_at
      before update on public.verdicts
      for each row execute function public.pmri_set_updated_at();
  end if;
end;
$$;

create or replace function public.pmri_handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (user_id, email, display_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'display_name', new.raw_user_meta_data ->> 'name')
  )
  on conflict (user_id) do update
    set email = excluded.email,
        display_name = coalesce(public.profiles.display_name, excluded.display_name);

  return new;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_trigger
    where tgname = 'pmri_on_auth_user_created'
  ) then
    create trigger pmri_on_auth_user_created
      after insert on auth.users
      for each row execute function public.pmri_handle_new_user();
  end if;
end;
$$;

alter table public.profiles enable row level security;
alter table public.portfolios enable row level security;
alter table public.portfolio_holdings enable row level security;
alter table public.reviews enable row level security;
alter table public.review_stage_summaries enable row level security;
alter table public.verdicts enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'profiles' and policyname = 'pmri_profiles_select_own'
  ) then
    create policy pmri_profiles_select_own
      on public.profiles for select
      using (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'profiles' and policyname = 'pmri_profiles_insert_own'
  ) then
    create policy pmri_profiles_insert_own
      on public.profiles for insert
      with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'profiles' and policyname = 'pmri_profiles_update_own'
  ) then
    create policy pmri_profiles_update_own
      on public.profiles for update
      using (user_id = auth.uid())
      with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'profiles' and policyname = 'pmri_profiles_delete_own'
  ) then
    create policy pmri_profiles_delete_own
      on public.profiles for delete
      using (user_id = auth.uid());
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolios' and policyname = 'pmri_portfolios_select_own'
  ) then
    create policy pmri_portfolios_select_own
      on public.portfolios for select
      using (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolios' and policyname = 'pmri_portfolios_insert_own'
  ) then
    create policy pmri_portfolios_insert_own
      on public.portfolios for insert
      with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolios' and policyname = 'pmri_portfolios_update_own'
  ) then
    create policy pmri_portfolios_update_own
      on public.portfolios for update
      using (user_id = auth.uid())
      with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolios' and policyname = 'pmri_portfolios_delete_own'
  ) then
    create policy pmri_portfolios_delete_own
      on public.portfolios for delete
      using (user_id = auth.uid());
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolio_holdings' and policyname = 'pmri_portfolio_holdings_select_own'
  ) then
    create policy pmri_portfolio_holdings_select_own
      on public.portfolio_holdings for select
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_holdings.portfolio_id
            and p.user_id = auth.uid()
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolio_holdings' and policyname = 'pmri_portfolio_holdings_insert_own'
  ) then
    create policy pmri_portfolio_holdings_insert_own
      on public.portfolio_holdings for insert
      with check (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_holdings.portfolio_id
            and p.user_id = auth.uid()
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolio_holdings' and policyname = 'pmri_portfolio_holdings_update_own'
  ) then
    create policy pmri_portfolio_holdings_update_own
      on public.portfolio_holdings for update
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_holdings.portfolio_id
            and p.user_id = auth.uid()
        )
      )
      with check (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_holdings.portfolio_id
            and p.user_id = auth.uid()
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'portfolio_holdings' and policyname = 'pmri_portfolio_holdings_delete_own'
  ) then
    create policy pmri_portfolio_holdings_delete_own
      on public.portfolio_holdings for delete
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.portfolios p
          where p.id = portfolio_holdings.portfolio_id
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
    where schemaname = 'public' and tablename = 'reviews' and policyname = 'pmri_reviews_select_own'
  ) then
    create policy pmri_reviews_select_own
      on public.reviews for select
      using (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'reviews' and policyname = 'pmri_reviews_insert_own'
  ) then
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
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'reviews' and policyname = 'pmri_reviews_update_own'
  ) then
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
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'reviews' and policyname = 'pmri_reviews_delete_own'
  ) then
    create policy pmri_reviews_delete_own
      on public.reviews for delete
      using (user_id = auth.uid());
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'review_stage_summaries' and policyname = 'pmri_review_stage_summaries_select_own'
  ) then
    create policy pmri_review_stage_summaries_select_own
      on public.review_stage_summaries for select
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = review_stage_summaries.review_row_id
            and r.user_id = auth.uid()
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'review_stage_summaries' and policyname = 'pmri_review_stage_summaries_insert_own'
  ) then
    create policy pmri_review_stage_summaries_insert_own
      on public.review_stage_summaries for insert
      with check (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = review_stage_summaries.review_row_id
            and r.user_id = auth.uid()
            and r.review_id = review_stage_summaries.review_id
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'review_stage_summaries' and policyname = 'pmri_review_stage_summaries_update_own'
  ) then
    create policy pmri_review_stage_summaries_update_own
      on public.review_stage_summaries for update
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = review_stage_summaries.review_row_id
            and r.user_id = auth.uid()
        )
      )
      with check (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = review_stage_summaries.review_row_id
            and r.user_id = auth.uid()
            and r.review_id = review_stage_summaries.review_id
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'review_stage_summaries' and policyname = 'pmri_review_stage_summaries_delete_own'
  ) then
    create policy pmri_review_stage_summaries_delete_own
      on public.review_stage_summaries for delete
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = review_stage_summaries.review_row_id
            and r.user_id = auth.uid()
        )
      );
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'verdicts' and policyname = 'pmri_verdicts_select_own'
  ) then
    create policy pmri_verdicts_select_own
      on public.verdicts for select
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = verdicts.review_row_id
            and r.user_id = auth.uid()
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'verdicts' and policyname = 'pmri_verdicts_insert_own'
  ) then
    create policy pmri_verdicts_insert_own
      on public.verdicts for insert
      with check (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = verdicts.review_row_id
            and r.user_id = auth.uid()
            and r.review_id = verdicts.review_id
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'verdicts' and policyname = 'pmri_verdicts_update_own'
  ) then
    create policy pmri_verdicts_update_own
      on public.verdicts for update
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = verdicts.review_row_id
            and r.user_id = auth.uid()
        )
      )
      with check (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = verdicts.review_row_id
            and r.user_id = auth.uid()
            and r.review_id = verdicts.review_id
        )
      );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'verdicts' and policyname = 'pmri_verdicts_delete_own'
  ) then
    create policy pmri_verdicts_delete_own
      on public.verdicts for delete
      using (
        user_id = auth.uid()
        and exists (
          select 1 from public.reviews r
          where r.id = verdicts.review_row_id
            and r.user_id = auth.uid()
        )
      );
  end if;
end;
$$;

comment on table public.profiles is
  'Portfolio MRI optional app-data profile rows. One row per Supabase Auth user.';
comment on table public.portfolios is
  'User-owned saved portfolios. Stores lightweight metadata only.';
comment on table public.portfolio_holdings is
  'Child rows for saved portfolio holdings. Deleted automatically when the parent portfolio is deleted.';
comment on table public.reviews is
  'Compact review records keyed by user_id and review_id. Does not store generated evidence artifacts.';
comment on table public.review_stage_summaries is
  'Compact per-stage summaries for staged progress, diagnosis, builder, candidate, comparison, verdict, and report. Full outputs are not stored here.';
comment on table public.verdicts is
  'Compact verdict summary for a review. Deleted automatically when the parent review is deleted.';

-- Portfolio MRI account workspace schema extension.
--
-- Included in the base schema for new Supabase projects.
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
