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
    stage in ('diagnosis', 'builder', 'candidate', 'comparison', 'verdict', 'report')
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
  'Compact per-stage summaries for diagnosis, builder, candidate, comparison, verdict, and report. Full outputs are not stored here.';
comment on table public.verdicts is
  'Compact verdict summary for a review. Deleted automatically when the parent review is deleted.';
