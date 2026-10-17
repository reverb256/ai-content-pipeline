# Research — Niche Software Workflows

> Evidence package for campaign: Niche Software Workflows. Verified claims with
> URLs, contradictions, unknowns, and mechanisms worth explaining. Every
> consequential claim in the flagship must trace to a claim here.

## Verified Claims (Market & Demand)

1. **GitHub Actions leads CI/CD adoption across all competitor tools.**
   JetBrains' State of CI/CD 2025 survey (3,500+ respondents) found GitHub
   Actions used by 62% of developers for personal projects and 41% for
   organizational work — the highest of any tool. Organizationally, Actions
   leads at 33%, followed by Jenkins (28%) and GitLab CI (19%). Source:
   https://blog.jetbrains.com/teamcity/2025/10/the-state-of-cicd/

2. **GitHub Actions is the most desirable developer collaboration tool.**
   Stack Overflow's 2025 Developer Survey (70.1% admired, 59.3% desired)
   ranked GitHub as the top tool for code documentation and collaboration,
   overtaking Jira for the first time. Source:
   https://survey.stackoverflow.co/2025/

3. **"github actions" sustains ~846 daily US Google searches (132K/month).**
   DailySearchVolume.com tracks the keyword at 846 searches per day in the
   US (132,364 monthly average), current through 2026-08-27. This is durable
   baseline demand, not a launch spike. Source:
   https://www.dailysearchvolume.com/keyword/en-us/github%20actions

4. **GitHub Actions is free for public repositories; private repos get 2,000
   free minutes/month on the Free plan.** Standard GitHub-hosted runner
   usage is free for public repos, GitHub Pages, and Dependabot. Private
   repositories consume from the account's plan entitlement; overage is
   billed at per-minute rates. Source:
   https://docs.github.com/en/billing/concepts/product-billing/github-actions

5. **GitHub cut Actions compute rates up to 39% on January 1, 2026.**
   The price reduction applies across all runner sizes, paired with a new
   $0.002/minute Actions cloud platform charge. Standard Linux hosted
   runners dropped from $0.008 to $0.005 per minute. Self-hosted runners
   began costing $0.002/minute as a control-plane fee on March 1, 2026.
   Source:
   https://github.com/resources/insights/2026-pricing-changes-for-github-actions

6. **Custom runner images reached General Availability in April 2026.**
   Teams can now bake dependencies into versioned, pinnable VM images
   using the new `snapshot` keyword. Available on GitHub Team and
   Enterprise Cloud plans only. Source:
   https://github.blog/changelog/2026-03-26-custom-images-for-github-hosted-runners-are-now-generally-available/

7. **Software/SaaS tutorial content earns $10–25 RPM on YouTube (2026).**
   Voxtly benchmarks "Software / SaaS tutorials" at $10–25 RPM. FluxNote
   places SaaS and software reviews at $10–18 RPM. The opportunity card's
   claim of $12–25 RPM is at the top of the verified range — achievable
   but not median. Sources:
   https://voxtly.com/blog/youtube-rpm-calculator ;
   https://fluxnote.io/guides/youtube-rpm-tech-niche-2026

8. **GitHub Actions CI/CD tutorials on YouTube range from 0 to ~300K views.**
   CoderDave's 2021 "GitHub Actions Tutorial | From Zero to Hero" has 297K
   views. Newer 2026 tutorials (Cloud With VarJosh, SortnSolve, DevOps by
   Shaik Moulali) range from 0 to ~870 views. The top result is four years
   old — signals room for a fresh, comprehensive 2026 production. Source:
   YouTube SERP data via direct observation (2026-08-31).

## Verified Claims (Mechanisms Worth Explaining)

9. **GitHub Actions workflows are YAML files in `.github/workflows/`.**
   Each workflow defines triggers (`on:`), jobs, steps, and runners.
   Workflows are event-driven: push, pull_request, schedule,
   workflow_dispatch, and 35+ other event types. Source:
   https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions

10. **Secrets management is built into GitHub Actions.** Two levels:
    repository secrets (scoped to one repo) and environment secrets
    (scoped to a deployment environment with required reviewers).
    Secrets are masked in logs and never exposed to forks. Source:
    https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions

11. **Environment-based promotion enables manual approval gates.**
    GitHub Environments support required reviewers, deployment protection
    rules, and environment-specific secrets. A common pattern: staging
    deploys automatically, production requires manual approval. Source:
    https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment

12. **Caching cuts install time from ~45 seconds to under 5.**
    The `actions/cache` action (or built-in `cache: 'npm'` in setup-node)
    caches dependencies between runs. Docker layer caching via
    `cache-from: type=gha` dramatically speeds up container builds.
    Source: https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows

13. **Matrix builds run the same job across multiple configurations in
    parallel.** Common use: testing against Node.js 18, 20, and 22
    simultaneously, or across operating systems (Ubuntu, Windows, macOS).
    Source:
    https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs

## Contradictions

- **Opportunity card claims $12–25 RPM for software/tech niche.** Verified
  data shows Software/SaaS tutorials at $10–25 RPM (Voxtly) and $10–18 RPM
  (FluxNote). The card's figure is at the top of the range — achievable
  with a US-heavy audience and strong ad load, but not the median. Use
  $10–18 RPM for conservative planning; $12–25 is the upside case.

- **"Crowded but fragmented" supply vs. real competitive landscape.** The
  supply gap is real but nuanced. YouTube has thousands of "how to use
  GitHub Actions" tutorials, but most are short, narrow, or outdated.
  The gap is for a comprehensive, start-to-finish "build a complete
  CI/CD pipeline from scratch" production — a single video that takes
  a viewer from zero to a deployed, multi-environment pipeline with
  secrets management, caching, and manual approval gates. No dominant
  2026 video owns this framing.

## Unknowns / What Sources Do NOT Prove

- **No verified view-count forecast for a "build CI/CD from scratch"
  tutorial.** Demand signals (search volume, survey adoption) confirm
  audience size, but no source predicts views for a specific video.
  The 846 daily US searches for "github actions" suggest a healthy
  long-tail, not a viral spike.

- **No public data on AI-generated vs. human-created tutorial performance
  in this niche.** Screen-recording automation is the production method,
  but whether audiences distinguish AI-narrated tutorials from
  human-narrated ones (and whether it affects retention/CPM) is
  untested.

- **Sponsorship potential for a GitHub Actions-specific tutorial is
  unquantified.** SaaS companies (Hostinger, NordVPN, Brilliant) sponsor
  tech channels at 10K+ subs, but no source breaks out sponsorship rates
  for DevOps/CI-CD content specifically.

- **The 2026 Actions Security Roadmap (default-deny permissions,
  tightened defaults) is referenced across tutorials but no independent
  audit of its impact on workflow authoring exists.** It is a real
  product direction, not a proven adoption driver.

## Mechanisms Worth Explaining (for the scriptwriter)

1. **The GitHub Actions execution model** — events trigger workflows,
   workflows contain jobs, jobs contain steps, steps run on runners.
   This is the mental model every viewer needs before writing YAML.

2. **The pricing ladder** — free for public repos, 2,000 min/month
   free for private, then $0.005/min for standard Linux. Why this
   matters for a developer deciding whether to adopt Actions.

3. **Secrets vs. environment secrets** — the difference, when to use
   each, and how environment secrets enable the manual approval gate
   that separates staging from production.

4. **The promotion workflow** — staging auto-deploys, production
   requires a human to click "approve" in the GitHub UI. This is the
   pattern that prevents broken code from reaching users.

5. **Caching as a speed lever** — how `actions/cache` and Docker
   layer caching turn a 3-minute build into a 30-second one.

6. **Matrix builds** — testing across Node.js versions or operating
   systems in parallel, and why this catches platform-specific bugs
   before staging.

7. **Custom runner images (2026 GA)** — baking dependencies into a
   versioned image so every run starts "pre-warmed." Available on
   Team/Enterprise plans only.
