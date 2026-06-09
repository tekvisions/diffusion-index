# The Diffusion Index — build continuation (2026-06-08)

**Gap proven + data layer DONE.** AI image/video generation — `diffusion.kymatalabs.com`.
Scaffolded from `~/rag-index`; `build_data.py` adapted (domain knobs swapped) + precision-tightened.

## DONE
- `build_data.py` — QUERIES/`_GEN_TOPICS`/`_GEN_PHRASES`/`_DENY`/`_ANTI`/categorize all adapted.
  `_ANTI` matches name+desc (catches awesome-*/`*-skill`/`*-mcp`). Run: `GITHUB_TOKEN=$(gh auth token) ~/agent-os/.venv/bin/python build_data.py`.
- `data.json` — **268 tools, 8 categories** (Image Models 92, Video Gen 66, ComfyUI 38,
  Editing 23, Frameworks 22, WebUIs 14, Training 12, Collections 1). Precision-tightened
  304→268 (removed LLM runtimes/skills/MCP/prompt-tools/surveys/TTS). Categorization verified
  (diffusers→Frameworks, InvokeAI→Apps). Trustworthy directory — do NOT re-loosen.
- SEO (sitemap/rss/robots/llms.txt) generated. `.github/workflows/update.yml` present.

## REMAINING (in order) — see ~/agent-os/docs/HANDOFF-2026-06-08-AUTOPILOT.md MISSION 2 checklist
1. **Distinct design** (NEW identity — "darkroom / spectral": deep charcoal #0d0d0f, film-grain
   texture, a vivid spectral gradient accent evoking generative imagery, a strong display font;
   image-forward cards). Rewrite `style.css` + `index.html` + `app.js` + `favicon.svg` — they're
   still the RAG template (light vector-field). DON'T reuse a prior fleet identity (warm-almanac/
   dark-scoreboard/light-blueprint/riso-zine/light-vector-field/industrial-forge/dark-launchpad).
   Update all "RAG"→"Diffusion" copy in index.html + the hero/meta.
2. `gen_details.py` + `gen_og.py` (run with `~/agent-os/.venv/bin/python` for Pillow). Update any
   "RAG" strings in them. `favicon.svg` distinct.
3. `deploy.py` first deploy (Vercel REST — CLI hangs in CC). Env: `VERCEL_TOKEN`,
   `VERCEL_TEAM_ID=team_L6hpqgg8pEHznOzrnU66JuoW`, `VERCEL_PROJECT=diffusion-index`. Then resolve
   the REAL public alias (`targets.production.alias`; global `diffusion-index.vercel.app` may be
   taken → `-three`/`-gamma`). If alias ≠ SITE_URL, fix SITE_URL in build_data.py + rebuild.
4. Assign subdomain `diffusion.kymatalabs.com` (Vercel domains API, POST
   `v10/projects/diffusion-index/domains?teamId=<team>` body `{"name":"diffusion.kymatalabs.com"}`
   → verified ~5s) → recanonicalize SITE_URL → rebuild → redeploy. Verify live `?z=<epoch>` +
   Playwright (cards render, 0 console errors, screenshot).
5. `git init` + repo `tekvisions/diffusion-index` + `gh secret set VERCEL_TOKEN` + trigger cron
   once (verify green). Footer: Sitemap · RSS · llms.txt · `↗ The Living Indexes`
   (indexes.kymatalabs.com) · `Built by tekvisions →` (https://www.kymatalabs.com/live).
6. **Integrate** (⚠️ kymatalabs flagship gotchas — see handoff): add to the hub
   (`~/living-indexes/build_data.py` INDEXES + index.html footer; bump "Ten"→"Eleven"),
   homepage (`~/kymatalabs` branch **master**, commit as `tekvisions <techtalevisions@gmail.com>`
   or Vercel BLOCKS it → `src/data/portfolio.ts` flagshipTrackers), and `/live`
   (`src/app/live/page.tsx` hardcoded products + "Eleven/Twelve" copy). Pro README + lock repo.
7. Telegram one-liner + Hive fact (`POST /admin/hive`).

Identity reminder: this is index #11 — give it a face the fleet doesn't have yet.
