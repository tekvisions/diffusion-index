#!/usr/bin/env python3
"""The Diffusion Index — recompute the living index of AI image & video generation tooling
from live GitHub signals, and write data.json + SEO (sitemap, rss, robots, llms.txt).

Scope = the generative-vision stack: diffusion frameworks (diffusers, SDXL, Flux), image
models, video generation (text-to-video, AnimateDiff, SVD), ComfyUI nodes, training (LoRA,
DreamBooth, ControlNet), and the WebUIs/apps that wrap them. Excludes prompt-engineering and
awesome-list repos, LLM/chat tooling, and repos that belong to sibling indexes. Gathered,
deduped, FILTERED (precision over recall), categorized, scored.

Only the GitHub *search* payload is used. Env: GITHUB_TOKEN (required for a usable rate limit).
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.github.com"
SITE_URL = "https://diffusion.kymatalabs.com"   # fixed to the real alias after first deploy
SITE_NAME = "The Diffusion Index"

QUERIES = [
    "topic:stable-diffusion stars:>150",
    "topic:diffusion-models stars:>200",
    "topic:text-to-image stars:>120",
    "topic:image-generation stars:>200",
    "topic:comfyui stars:>90",
    "topic:text-to-video stars:>80",
    "topic:video-generation stars:>120",
    "topic:image-to-image stars:>120",
    "topic:generative-art stars:>250",
    "text to image model in:name,description stars:>300",
    "text to video in:name,description stars:>150",
    "diffusion model in:name,description stars:>250",
]


def token() -> str:
    return (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()


HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "diffusion-index"}
if token():
    HEADERS["Authorization"] = f"Bearer {token()}"

_GEN_TOPICS = {"stable-diffusion", "text-to-image", "image-generation", "diffusion-models",
               "comfyui", "text-to-video", "video-generation", "image-to-image", "image-synthesis",
               "generative-art", "diffusion", "controlnet", "dreambooth", "lora", "sdxl", "flux",
               "video-diffusion", "img2img", "animatediff", "image-editing"}
_GEN_PHRASES = re.compile(
    r"\b(text[- ]to[- ]image|text[- ]to[- ]video|image[- ]to[- ]image|image generation"
    r"|video generation|diffusion model|stable diffusion|image synthesis|img2img|txt2img"
    r"|comfyui|controlnet|dreambooth|inpaint(ing)?|outpaint(ing)?|generative art|image editing"
    r"|video diffusion|latent diffusion|sdxl|flux\.?1|animatediff|image model)\b", re.I)
# LLM runtimes/chat, agent skills/MCP, prompt tools, paper-surveys, TTS/speech, and other
# sibling-index repos that match but aren't image/video GENERATION tools. Lowercased
# full_name (is_gen lowercases before the lookup); _ANTI (name+desc) catches the rest.
_DENY = {"promptslab/awesome-prompt-engineering", "evolinkai/awesome-gpt-image-2-api-and-prompts",
         "jamez-bondos/awesome-gpt4o-images", "hismax/redink", "f/awesome-chatgpt-prompts",
         "dair-ai/prompt-engineering-guide", "openai/clip", "open-webui/open-webui",
         "mudler/localai", "enricoros/big-agi", "crmne/ruby_llm", "khoj-ai/khoj",
         "light-heart-labs/dreamserver", "chatanyteam/chatany", "cuckoo-network/cuckoo",
         "opengvlab/interngpt", "aserbao/androidcamera", "samuraigpt/generative-media-skills",
         "openvinotoolkit/openvino", "runanywhereai/runanywhere-sdks"}
_ANTI = re.compile(
    r"\b(awesome|curated|prompt engineering|prompt (collection|library|gallery)|list of prompts"
    r"|tutorial|course|roadmap|cheat ?sheet|paper[- ]?(list|survey)|reading list|survey (on|of)"
    r"|interview|llm chat|chatbot builder|second brain|model context protocol|\bmcp\b|\bskill\b"
    r"|powerpoint|ppt\b|slide deck|social card|speech recognition|text[- ]to[- ]speech|\btts\b"
    r"|\basr\b|voice (clon|convers)|generative music|creative coding|\bbook\b)\b", re.I)


def gh(url: str, *, retries: int = 4):
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (403, 429):
                reset = e.headers.get("X-RateLimit-Reset")
                wait = 5 * (attempt + 1)
                if reset:
                    try:
                        wait = max(wait, min(60, int(reset) - int(time.time()) + 2))
                    except ValueError:
                        pass
                print(f"  rate-limited — sleeping {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if 500 <= e.code < 600:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(3 * (attempt + 1))
    if last:
        raise last
    raise RuntimeError(f"gh failed: {url}")


def search(q: str, per_page: int = 40) -> list[dict]:
    url = (f"{API}/search/repositories?q={urllib.parse.quote(q)}"
           f"&sort=stars&order=desc&per_page={per_page}")
    try:
        return gh(url).get("items", [])
    except Exception as e:
        print(f"  query failed [{q}]: {e}", file=sys.stderr)
        return []


def is_gen(r: dict) -> bool:
    full = (r.get("full_name") or "").lower()
    if full in _DENY:
        return False
    name = r.get("name") or ""
    desc = r.get("description") or ""
    if _ANTI.search(f"{name} {desc}"):       # name+desc → catches awesome-*/`*-skill`/`*-mcp` names
        return False
    topics = {t.lower() for t in (r.get("topics") or [])}
    if topics & _GEN_TOPICS:
        return True
    return bool(_GEN_PHRASES.search(f"{r.get('name','')} {desc}"))


def categorize(r: dict) -> str:
    topics = {t.lower() for t in (r.get("topics") or [])}
    blob = f"{(r.get('name') or '').lower()} {(r.get('description') or '').lower()} {' '.join(topics)}"
    if "comfyui" in blob or "custom-node" in blob or "custom node" in blob:
        return "ComfyUI & Nodes"
    # definitive apps/UIs FIRST (so InvokeAI/A1111 don't fall into Editing via a topic)
    if re.search(r"automatic1111|invokeai|fooocus|\bforge\b|web[- ]?ui|\bwebui\b|creative engine"
                 r"|desktop app|1-?click|\bplayground\b", blob):
        return "WebUIs & Apps"
    if re.search(r"\bdiffusers\b|\bsdxl\b|\bflux\b|latent diffusion|diffusion (library|framework|pipeline)"
                 r"|inference (engine|library|framework)", blob):
        return "Diffusion Frameworks"
    if re.search(r"text[- ]to[- ]video|video[- ]?(gener|diffus|model|synth)|animatediff|\bt2v\b|\bi2v\b"
                 r"|image[- ]to[- ]video|talking[- ]?(head|portrait)|lip[- ]?sync|portraits? to life", blob):
        return "Video Generation"
    if re.search(r"\blora\b|dreambooth|fine[- ]?tun|\btraining\b|textual inversion|train your own", blob):
        return "Training & Fine-tuning"
    if re.search(r"controlnet|inpaint|outpaint|img2img|image[- ]edit|ip-?adapter|\bediting\b"
                 r"|super[- ]?resolution|upscal", blob):
        return "Editing & Control"
    if re.search(r"awesome|curated|collection|directory", blob):
        return "Collections"
    return "Image Models"


def days_since(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds() / 86400.0
    except ValueError:
        return None


def momentum(r: dict, max_stars: int) -> int:
    stars = r.get("stargazers_count", 0) or 0
    star_norm = math.log10(stars + 1) / math.log10(max(max_stars, 10) + 1)
    pushed = days_since(r.get("pushed_at"))
    recency = 0.2 if pushed is None else max(0.0, 1.0 - max(0.0, pushed) / 180.0)
    created = days_since(r.get("created_at"))
    young = (1.0 - created / 120.0) if (created is not None and created < 120 and stars >= 20) else 0.0
    return max(1, min(100, round((0.55 * star_norm + 0.32 * recency + 0.13 * young) * 100)))


def slugify(full_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", full_name.lower()).strip("-")


def build_items() -> list[dict]:
    seen: dict[str, dict] = {}
    for q in QUERIES:
        for r in search(q):
            full = r.get("full_name")
            if full and full not in seen and is_gen(r):
                seen[full] = r
        time.sleep(0.7)
    raw = list(seen.values())
    max_stars = max((r.get("stargazers_count", 0) or 0) for r in raw) if raw else 10
    items = []
    for r in raw:
        owner = r.get("owner") or {}
        items.append({
            "name": r.get("name", ""), "full_name": r.get("full_name", ""),
            "slug": slugify(r.get("full_name", "")), "url": r.get("html_url", ""),
            "owner": owner.get("login", ""), "owner_avatar": owner.get("avatar_url", ""),
            "stars": r.get("stargazers_count", 0) or 0, "forks": r.get("forks_count", 0) or 0,
            "open_issues": r.get("open_issues_count", 0) or 0, "language": r.get("language") or "",
            "license": ((r.get("license") or {}) or {}).get("spdx_id") or "",
            "pushed_at": r.get("pushed_at"), "created_at": r.get("created_at"),
            "description": (r.get("description") or "").strip(), "topics": r.get("topics") or [],
            "category": categorize(r), "momentum": momentum(r, max_stars),
        })
    items.sort(key=lambda x: (x["momentum"], x["stars"]), reverse=True)
    for i, it in enumerate(items, 1):
        it["rank"] = i
    return items


def write_json(items: list[dict]) -> dict:
    cats: dict[str, int] = {}
    for it in items:
        cats[it["category"]] = cats.get(it["category"], 0) + 1
    data = {"generated_at": datetime.now(timezone.utc).isoformat(), "count": len(items),
            "categories": [{"name": k, "count": v} for k, v in sorted(cats.items(), key=lambda x: -x[1])],
            "items": items}
    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


def write_seo(data: dict) -> None:
    items = data["items"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [f"  <url><loc>{SITE_URL}/</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for it in items:
        urls.append(f"  <url><loc>{SITE_URL}/p/{it['slug']}/</loc><lastmod>{now}</lastmod>"
                    f"<changefreq>weekly</changefreq><priority>0.6</priority></url>")
    open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n")
    open(os.path.join(HERE, "robots.txt"), "w", encoding="utf-8").write(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    rss_items = [
        f"    <item><title>{esc(it['full_name'])} — momentum {it['momentum']}</title>"
        f"<link>{SITE_URL}/p/{it['slug']}/</link><guid isPermaLink=\"false\">{esc(it['full_name'])}</guid>"
        f"<description>{esc(it['description'][:300])}</description></item>" for it in items[:30]]
    open(os.path.join(HERE, "rss.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n  <channel>\n'
        f"    <title>{SITE_NAME}</title>\n    <link>{SITE_URL}</link>\n"
        "    <description>The living index of AI image &amp; video generation tooling — diffusion frameworks, video models, ComfyUI, training.</description>\n"
        + "\n".join(rss_items) + "\n  </channel>\n</rss>\n")

    lines = [f"# {SITE_NAME}", "",
             "> The living index of AI image & video generation tooling — diffusion frameworks,",
             "> video models, ComfyUI nodes, training & editing — ranked daily by GitHub momentum.", "",
             f"Updated: {data['generated_at']}", f"Tools indexed: {data['count']}", "",
             "## Top generation tools by momentum", ""]
    for it in items[:40]:
        lines.append(f"- [{it['full_name']}]({it['url']}) — momentum {it['momentum']}, "
                     f"⭐{it['stars']} — {it['category']} — {it['description'][:100]}")
    open(os.path.join(HERE, "llms.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def main() -> int:
    if not token():
        print("WARNING: no GITHUB_TOKEN — low rate limit, partial results", file=sys.stderr)
    items = build_items()
    if not items:
        print("ERROR: no generation tools found — refusing to write empty data.json", file=sys.stderr)
        return 1
    data = write_json(items)
    write_seo(data)
    print(f"wrote data.json: {len(items)} generation tools across {len(data['categories'])} categories")
    print("  top 5:", ", ".join(f"{it['full_name']}({it['momentum']})" for it in items[:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
