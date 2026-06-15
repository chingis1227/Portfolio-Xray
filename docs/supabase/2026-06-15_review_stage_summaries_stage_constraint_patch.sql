-- Portfolio MRI Supabase patch: align review_stage_summaries.stage with review_state_v1.
--
-- Use this in the Supabase SQL Editor when an existing database returns:
--   new row for relation "review_stage_summaries" violates check constraint
--   "review_stage_summaries_stage_check"
-- for stages such as "input", "data_load", "xray", "stress",
-- "client_fit", "problem_classification", or "launchpad_builder".
--
-- This patch stores compact stage summaries only. It does not create storage
-- buckets and does not permit raw generated artifacts.

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
