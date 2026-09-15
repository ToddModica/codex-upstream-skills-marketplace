# -*- coding: utf-8 -*-
"""
中国专利公布公告网站点：http://epub.cnipa.gov.cn/ —— **首页「公布公告查询」**（#indexForm / #searchStr）及 **高级查询**（/Advanced，分类号、名称与发明人字段）。

须安装 **Playwright**。浏览器启动见 ``tools/browser.py``（系统 Chrome → Edge → 自带 Chromium；有系统浏览器时不必 ``playwright install chromium``）。若只需内存中解析、不落盘 HTML，优先用同目录 **`cnipa_epub_search.py`**；
本文件侧重 **写出结果页 HTML** 与可插拔的 ``fetch_epub_result_html`` API。

-------------------------------------------------------------------------------
一、整体流程（单次检索）
-------------------------------------------------------------------------------
1. 启动浏览器（默认无头；系统 Chrome → Edge → 自带 Chromium；可用环境变量改为有界面）。
2. 新建浏览器上下文：设定 **桌面 Chrome UA**、**zh-CN**、固定 **视口**（见 ``_new_context``），使请求形态接近普通用户浏览器。
3. ``page.goto`` 站点首页（``wait_until`` 与超时见 ``cnipa_epub_wait.yaml``，默认 ``commit`` / 30s）。
4. **等待首页可检索**：首页经前端/WAF 后才出现 ``#searchStr``。框已在则立刻继续，否则短轮询（默认 20s）。失败阶段 ``gate``，**不是** 0 条命中。
5. ``page.fill`` 写入 ``#searchStr``，对 ``#indexForm`` **submit**，等结果标题就绪（默认 40s）；**0 条**是标题「无查询结果」，与提交超时分开。
6. 结果页：标题为 **「专利查询结果展示」或「无查询结果」**，且 ``#result`` 内有条目或零结果文案。国知局改版时须同步 ``EPUB_TITLE_*`` 与 ``_RESULT_PAGE_READY_JS``。
7. ``page.content()`` 取全页 HTML；若处于导航中抛错则 **重试退避**（``_safe_page_content``），避免竞态。
8. 后续解析由 **`cnipa_epub_parse.py`** 完成（本文件 ``search_epub_keyword`` 内会调用）。

-------------------------------------------------------------------------------
二、策略摘要：在解决什么、用了哪些手段
-------------------------------------------------------------------------------
- **为何用 Playwright**：站点依赖 **浏览器内 JavaScript** 渲染与风控后再开放检索框；**纯 HTTP 抓取**往往拿不到含 ``#searchStr`` 的可用首页或拿不到真实结果 DOM。
- **所谓「绕过」**：指 **技术层面** 与无头自动化、静态抓取之间的 gap——通过 **真实 Chromium 内核 + 等待 JS 完成 + 常见浏览器指纹**（UA、语言、viewport）降低「一进来就_submit」的失败率；**不**表示规避法律法规或站点服务条款，用途应限合法检索与交底书查新辅助。
- **反自动化/特征**：启动参数 ``--disable-blink-features=AutomationControlled`` 用于减弱 Chromium 的 **webdriver 自动化开关** 暴露（效果因站点升级而变，非保证）。
- **不覆盖的场景**：图形/滑块验证码、短信验证、强制登录等——若站点突然启用，本脚本**无**专门破解逻辑；可尝试 ``PLAYWRIGHT_HEADED=1`` 人工辅助或改用 **WebSearch**（见 ``prompts/prior_art_search.md``）。

-------------------------------------------------------------------------------
三、检索关键词建议
-------------------------------------------------------------------------------
- 公布站首页检索框对 **多个词** 通常按 **同时包含（AND）** 理解，**词多且专**时极易 **0 条**；**建议每次尽量使用单个词或极短短语** 做一次检索，需要宽召回时可用 **`cnipa_epub_search.py`**（按空白拆成多词、多次检索再合并），或分多次手动换关键词。
- 本脚本命令行默认仍接受一个参数字符串（可含空格）；含空格时与浏览器内一次提交一致，语义上仍是 **整句 AND**，不等同于拆词多查。

-------------------------------------------------------------------------------
等待参数
-------------------------------------------------------------------------------
  ``cnipa_epub_wait.yaml``（同目录；``EPUB_WAIT_YAML`` 可改路径）。缺文件回退
  ``cnipa_epub_wait.DEFAULTS``。``EPUB_WAF_MAX_WAIT_SEC`` 若已设置则覆盖 ``gate_poll_sec``。
  PLAYWRIGHT_HEADED        设为 1 时使用有界面 Chromium
  EPUB_RESULT_HTML         结果页 HTML 完整路径；不设则 tools/_last_result_YYYYMMDDHHmmss.html
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Error,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from cnipa_epub_parse import (
    EpubSearchHit,
    hits_to_jsonable,
    parse_search_result_html,
)
from browser import launch_chromium
from stdio_utf8 import ensure_utf8_stdio
from patent_type import (
    TYPE_ALL,
    epub_checkbox_states,
    normalize_patent_type,
)
from cnipa_epub_wait import EpubNavError, load_wait_config, progress


EPUB_BASE = "http://epub.cnipa.gov.cn/"
EPUB_ADVANCED = EPUB_BASE.rstrip("/") + "/Advanced"
# 高级查询页 checkbox（与首页 #fmgb 等不同）
EPUB_ADVANCED_CHECKBOX = {
    "fmgb": "isFmgb",
    "fmsq": "isFmsq",
    "xxsq": "isXx",
    "wgsq": "isWg",
}
# 国知局 /Dxb/IndexQuery 结果页 <title>；改版时须同步单测与 _RESULT_PAGE_READY_JS
EPUB_TITLE_RESULT = "专利查询结果展示"
EPUB_TITLE_NO_HIT = "无查询结果"
# 在浏览器内判断结果页可解析：title + #result DOM（列表或零结果文案）
_RESULT_PAGE_READY_JS = """(titles) => {
    const t = document.title.trim();
    if (t === titles.noHit) return true;
    if (t !== titles.result) return false;
    const r = document.querySelector("#result");
    if (!r) return false;
    if (r.querySelector("div.item, h1.title")) return true;
    const html = r.innerHTML;
    if (
        html.includes("无查询结果") ||
        html.includes("没有找到") ||
        html.includes("未检索到") ||
        html.includes("0条")
    ) {
        return true;
    }
    return false;
}"""
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _cfg() -> dict:
    return load_wait_config()


def _page_url(page: Page) -> str:
    try:
        return str(page.url or "")
    except Exception:
        return ""


def _nav_hint(*, advanced: bool) -> str:
    return "keep_round1" if advanced else "skip_epub"


def _goto(page: Page, url: str, *, advanced: bool) -> None:
    cfg = _cfg()
    timeout_ms = int(cfg["goto_timeout_ms"])
    wait_until = str(cfg["goto_wait_until"])
    progress(f"stage=goto wait_until={wait_until} timeout_ms={timeout_ms} url={url}")
    try:
        page.goto(url, wait_until=wait_until, timeout=timeout_ms)
    except (PlaywrightTimeoutError, Error) as exc:
        raise EpubNavError(
            "goto",
            hint=_nav_hint(advanced=advanced),
            message="打开公布站页面超时或失败",
            timeout_s=timeout_ms / 1000.0,
            url=url,
        ) from exc


def _wait_selector(
    page: Page,
    selector: str,
    *,
    advanced: bool,
    max_wait_sec: float | None = None,
) -> None:
    cfg = _cfg()
    limit = float(max_wait_sec) if max_wait_sec is not None else float(cfg["gate_poll_sec"])
    step = float(cfg["gate_poll_step_sec"])
    progress(f"stage=gate selector={selector} timeout_s={limit:g}")
    deadline = time.monotonic() + limit
    while True:
        try:
            if page.query_selector(selector):
                return
        except Error:
            pass
        if time.monotonic() >= deadline:
            raise EpubNavError(
                "gate",
                hint=_nav_hint(advanced=advanced),
                message=f"页面已打开但未出现 {selector}",
                timeout_s=limit,
                url=_page_url(page),
            )
        remaining = deadline - time.monotonic()
        page.wait_for_timeout(int(min(step, max(remaining, 0.05)) * 1000))


def _headed() -> bool:
    return os.environ.get("PLAYWRIGHT_HEADED", "").strip() in ("1", "true", "yes")


def default_result_html_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return Path(__file__).resolve().parent / f"_last_result_{ts}.html"


def wait_for_epub_home_ready(page: Page, *, max_wait_sec: float | None = None) -> None:
    if page.query_selector("#searchStr"):
        return
    _goto(page, EPUB_BASE, advanced=False)
    _wait_selector(page, "#searchStr", advanced=False, max_wait_sec=max_wait_sec)


def open_epub_advanced_search(page: Page) -> None:
    """Open CNIPA's fielded search after the browser session passed the home gate."""
    _goto(page, EPUB_ADVANCED, advanced=True)
    _wait_selector(page, "#advForm #e72", advanced=True)


def _safe_page_content(page: Page, *, max_attempts: int = 10) -> str:
    last_err: Exception | None = None
    for i in range(max_attempts):
        try:
            return page.content()
        except Error as e:
            msg = str(e).lower()
            last_err = e
            if "navigating" not in msg and "changing" not in msg:
                raise
            try:
                page.wait_for_load_state("load", timeout=20_000)
            except Exception:
                pass
            page.wait_for_timeout(400 + 200 * i)
    if last_err:
        raise last_err
    raise RuntimeError("_safe_page_content: 未返回内容")


def _wait_result_page_ready(page: Page, *, advanced: bool = False) -> None:
    """等结果页 title 与 #result 列表/零结果 DOM 就绪（不等完整 load）。"""
    timeout_ms = int(_cfg()["submit_timeout_ms"])
    progress(f"stage=submit timeout_ms={timeout_ms}")
    try:
        page.wait_for_function(
            _RESULT_PAGE_READY_JS,
            arg={"result": EPUB_TITLE_RESULT, "noHit": EPUB_TITLE_NO_HIT},
            timeout=timeout_ms,
        )
    except PlaywrightTimeoutError as exc:
        raise EpubNavError(
            "submit",
            hint=_nav_hint(advanced=advanced),
            message="提交后未出现结果页（有结果或明确0条）",
            timeout_s=timeout_ms / 1000.0,
            url=_page_url(page),
        ) from exc


def apply_epub_type_filter(page: Page, patent_type: str = TYPE_ALL) -> None:
    """按类型勾选首页 #fmgb/#fmsq/#xxsq/#wgsq（与截图四类一致）。"""
    states = epub_checkbox_states(patent_type)
    for cid, want in states.items():
        box = page.query_selector(f"#{cid}")
        if not box:
            continue
        try:
            if want:
                box.check(force=True)
            else:
                box.uncheck(force=True)
        except Error:
            page.evaluate(
                """({id, checked}) => {
                    const el = document.getElementById(id);
                    if (!el) return;
                    el.checked = checked;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }""",
                {"id": cid, "checked": want},
            )


def apply_epub_advanced_type_filter(page: Page, patent_type: str = TYPE_ALL) -> None:
    """高级查询页勾选 #isFmgb / #isFmsq / #isXx / #isWg。"""
    states = epub_checkbox_states(patent_type)
    for home_id, want in states.items():
        cid = EPUB_ADVANCED_CHECKBOX.get(home_id)
        if not cid:
            continue
        box = page.query_selector(f"#{cid}")
        if not box:
            continue
        try:
            if want:
                box.check(force=True)
            else:
                box.uncheck(force=True)
        except Error:
            page.evaluate(
                """({id, checked}) => {
                    const el = document.getElementById(id);
                    if (!el) return;
                    el.checked = checked;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }""",
                {"id": cid, "checked": want},
            )


def wait_for_epub_advanced_ready(page: Page, *, max_wait_sec: float | None = None) -> None:
    """打开 /Advanced，等到分类号框 #e51。框已在则不重新 goto。"""
    if page.query_selector("#e51"):
        return
    _goto(page, EPUB_ADVANCED, advanced=True)
    _wait_selector(page, "#e51", advanced=True, max_wait_sec=max_wait_sec)


def submit_advanced_search(
    page: Page,
    keyword: str,
    *,
    class_code: str,
    patent_type: str = TYPE_ALL,
) -> None:
    """高级查询：分类号 #e51 + 名称 #ti，类型勾选后提交。等结果标题，不死等 AdvancedQuery+load。"""
    apply_epub_advanced_type_filter(page, patent_type)
    page.fill("#e51", class_code)
    if page.query_selector("#ti"):
        page.fill("#ti", keyword or "")
    form = page.query_selector("#advForm")
    if form is None:
        raise RuntimeError("高级查询未找到 #advForm")
    btn = form.query_selector("button")
    if btn is None:
        raise RuntimeError("高级查询未找到提交按钮")
    btn.click()
    _wait_result_page_ready(page, advanced=True)


def submit_index_search(
    page: Page,
    keyword: str,
    *,
    patent_type: str = TYPE_ALL,
) -> None:
    apply_epub_type_filter(page, patent_type)
    page.fill("#searchStr", keyword)
    timeout_ms = int(_cfg()["submit_timeout_ms"])
    try:
        with page.expect_navigation(timeout=timeout_ms, wait_until="commit"):
            form = page.query_selector("#indexForm")
            if form:
                form.evaluate("el => el.submit()")
            else:
                page.evaluate(
                    """() => {
                    const f = document.getElementById('indexForm');
                    if (f) f.submit();
                }"""
                )
    except (PlaywrightTimeoutError, Error) as exc:
        raise EpubNavError(
            "submit",
            hint=_nav_hint(advanced=False),
            message="首页提交后导航超时",
            timeout_s=timeout_ms / 1000.0,
            url=_page_url(page),
        ) from exc
    _wait_result_page_ready(page, advanced=False)


def fetch_epub_result_html(
    keyword: str,
    *,
    patent_type: str = TYPE_ALL,
    playwright_factory: Callable[[], Playwright] | None = None,
) -> str:
    """只拉取检索结果页 HTML（一词一页，不翻页）。"""
    rows = search_epub_keywords(
        [keyword], patent_type=patent_type, playwright_factory=playwright_factory
    )
    return rows[0][0]


def search_epub_keywords(
    terms: list[str],
    *,
    patent_type: str = TYPE_ALL,
    class_codes: list[str] | None = None,
    playwright_factory: Callable[[], Playwright] | None = None,
) -> list[tuple[str, list[EpubSearchHit]]]:
    """一场检索共用一个浏览器；一词一页，返回与检索次数等长的 ``(html, hits)``。

    ``class_codes`` 非空时走公布站 **高级查询**（分类号 + 名称）；``terms`` 可为空（只按分类号，保底放宽）。
    导航失败默认停止后续跳（``stop_on_first_nav_failure``）；已完成的跳仍返回。
    """
    codes = [c.strip() for c in (class_codes or []) if c and str(c).strip()]
    if not terms and not codes:
        return []
    kw_list = list(terms) if terms else [""]
    cfg = _cfg()
    stop = bool(cfg["stop_on_first_nav_failure"])
    pw_gen = playwright_factory or sync_playwright
    with pw_gen() as p:
        browser = _launch_browser(p)
        context = _new_context(browser)
        try:
            page = context.new_page()
            out: list[tuple[str, list[EpubSearchHit]]] = []
            hops: list[tuple[str, str]]
            if not codes:
                hops = [("", keyword) for keyword in kw_list if keyword]
            else:
                hops = [(code, keyword) for code in codes for keyword in kw_list]
            total = len(hops)
            for i, (code, keyword) in enumerate(hops, start=1):
                label = (
                    f"stage=home term={keyword} i={i}/{total}"
                    if not code
                    else f"stage=advanced class={code} term={keyword or '-'} i={i}/{total}"
                )
                progress(label)
                try:
                    if not code:
                        wait_for_epub_home_ready(page)
                        submit_index_search(page, keyword, patent_type=patent_type)
                    else:
                        wait_for_epub_advanced_ready(page)
                        submit_advanced_search(
                            page,
                            keyword,
                            class_code=code,
                            patent_type=patent_type,
                        )
                    html = _safe_page_content(page)
                    out.append((html, parse_search_result_html(html)))
                except EpubNavError as exc:
                    remaining = total - i
                    progress(
                        f"stage={exc.stage} remaining_skipped={remaining} hint={exc.hint}"
                    )
                    if not stop:
                        print(
                            f"EPUB_NOTE: hop_failed_continue stage={exc.stage} hint={exc.hint}",
                            file=sys.stderr,
                            flush=True,
                        )
                        continue
                    print(
                        f"EPUB_NOTE: stopped_after_failure stage={exc.stage} hint={exc.hint}",
                        file=sys.stderr,
                        flush=True,
                    )
                    if out:
                        return out
                    raise
            return out
        finally:
            context.close()
            browser.close()


def search_epub_keyword(
    keyword: str,
    *,
    patent_type: str = TYPE_ALL,
    class_codes: list[str] | None = None,
    playwright_factory: Callable[[], Playwright] | None = None,
) -> tuple[str, list[EpubSearchHit]]:
    rows = search_epub_keywords(
        [keyword],
        patent_type=patent_type,
        class_codes=class_codes,
        playwright_factory=playwright_factory,
    )
    return rows[0]


def search_epub_keyword_with_page(
    page: Page,
    keyword: str,
    *,
    patent_type: str = TYPE_ALL,
) -> tuple[str, list[EpubSearchHit]]:
    wait_for_epub_home_ready(page)
    submit_index_search(page, keyword, patent_type=patent_type)
    html = _safe_page_content(page)
    return html, parse_search_result_html(html)


def _launch_browser(p: Playwright) -> Browser:
    browser, _label = launch_chromium(p, headless=not _headed())
    return browser


def _new_context(browser: Browser) -> BrowserContext:
    if sys.platform == "darwin":
        platform_token = "Macintosh; Intel Mac OS X 10_15_7"
    elif sys.platform.startswith("linux"):
        platform_token = "X11; Linux x86_64"
    else:
        platform_token = "Windows NT 10.0; Win64; x64"
    user_agent = DEFAULT_USER_AGENT.format(version=browser.version).replace(
        "Windows NT 10.0; Win64; x64", platform_token
    )
    return browser.new_context(
        user_agent=user_agent,
        locale="zh-CN",
        viewport={"width": 1280, "height": 900},
    )


def _dump_home_debug() -> None:
    """调试：仅拉取首页并保存 WAF 通过后 HTML。"""
    out = Path(__file__).resolve().parent / "_last_home.html"
    with sync_playwright() as p:
        browser = _launch_browser(p)
        context = _new_context(browser)
        page = context.new_page()
        try:
            wait_for_epub_home_ready(page)
            out.write_text(page.content(), encoding="utf-8")
            print("已保存:", out)
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    ensure_utf8_stdio()
    argv = [a for a in sys.argv[1:] if a.strip()]
    if argv and argv[0] in ("--dump-home", "-d"):
        _dump_home_debug()
        sys.exit(0)
    patent_type = TYPE_ALL
    filtered: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--type", "-t") and i + 1 < len(argv):
            patent_type = normalize_patent_type(argv[i + 1], default=TYPE_ALL)
            i += 2
            continue
        if a.startswith("--type="):
            patent_type = normalize_patent_type(a.split("=", 1)[1], default=TYPE_ALL)
            i += 1
            continue
        filtered.append(a)
        i += 1
    kw = (filtered[0] if filtered else "批处理").strip()
    try:
        out_html, hits = search_epub_keyword(kw, patent_type=patent_type)
    except EpubNavError as e:
        print("CNIPA_EPUB_ERROR:", e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("CNIPA_EPUB_ERROR:", e, file=sys.stderr)
        sys.exit(1)
    out_path = Path(
        os.environ.get("EPUB_RESULT_HTML", "").strip() or default_result_html_path()
    )
    out_path = out_path.expanduser().resolve()
    out_path.write_text(out_html, encoding="utf-8")
    print(
        "结果页长度",
        len(out_html),
        "解析条目数",
        len(hits),
        file=sys.stderr,
        flush=True,
    )
    print("结果页 HTML 已保存:", out_path, file=sys.stderr, flush=True)
    print(
        "EPUB_HITS_JSON:",
        json.dumps(hits_to_jsonable(hits), ensure_ascii=False),
        flush=True,
    )
