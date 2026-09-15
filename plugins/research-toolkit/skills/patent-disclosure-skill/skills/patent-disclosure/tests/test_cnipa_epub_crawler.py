# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PKG = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PKG / "tools" / "crawl"))
sys.path.insert(0, str(PKG / "tools"))

from cnipa_epub_crawler import (
    EPUB_TITLE_NO_HIT,
    EPUB_TITLE_RESULT,
    _RESULT_PAGE_READY_JS,
    apply_epub_type_filter,
    search_epub_keywords,
    submit_index_search,
    wait_for_epub_home_ready,
    _goto,
    _wait_selector,
)
from cnipa_epub_wait import DEFAULTS, EpubNavError
from patent_type import (
    epub_checkbox_states,
    google_patents_websearch_query,
    infer_patent_type_from_pub,
    normalize_patent_type,
    resolve_reader_patent_type,
)


class PatentTypeTests(unittest.TestCase):
    def test_normalize_aliases(self) -> None:
        self.assertEqual(normalize_patent_type("实用新型"), "utility_model")
        self.assertEqual(normalize_patent_type("外观设计"), "design")
        self.assertEqual(normalize_patent_type("发明"), "invention")
        self.assertEqual(normalize_patent_type(None, default="all"), "all")

    def test_infer_from_pub_kind_code(self) -> None:
        self.assertEqual(infer_patent_type_from_pub("CN119961390A"), "invention")
        self.assertEqual(infer_patent_type_from_pub("CN107785522B"), "invention")
        self.assertEqual(infer_patent_type_from_pub("CN209861402U"), "utility_model")
        self.assertEqual(infer_patent_type_from_pub("CN309939145S"), "design")
        self.assertEqual(infer_patent_type_from_pub("cn 209861402 u"), "utility_model")
        self.assertIsNone(infer_patent_type_from_pub("US6301113B1"))
        self.assertIsNone(infer_patent_type_from_pub(""))

    def test_resolve_priority_user_over_pub(self) -> None:
        r = resolve_reader_patent_type(pub="CN209861402U", user_declared="外观设计")
        self.assertEqual(r["patent_type"], "design")
        self.assertEqual(r["source"], "user_declared")
        r2 = resolve_reader_patent_type(pub="CN209861402U")
        self.assertEqual(r2["patent_type"], "utility_model")
        self.assertEqual(r2["source"], "pub_kind_code")
        r3 = resolve_reader_patent_type(
            pub="UNKNOWN", biblio_text="本实用新型涉及一种卡扣"
        )
        self.assertEqual(r3["patent_type"], "utility_model")
        self.assertEqual(r3["source"], "biblio_text")

    def test_epub_checkbox_presets(self) -> None:
        um = epub_checkbox_states("utility_model")
        self.assertTrue(um["xxsq"])
        self.assertFalse(um["fmgb"])
        inv = epub_checkbox_states("invention")
        self.assertTrue(inv["fmgb"] and inv["fmsq"])
        self.assertFalse(inv["wgsq"])

    def test_google_patents_query_hints(self) -> None:
        q = google_patents_websearch_query("灯具", "design")
        self.assertIn("type:DESIGN", q)
        q2 = google_patents_websearch_query("卡扣", "utility_model")
        self.assertIn("实用新型", q2)


class ApplyTypeFilterTests(unittest.TestCase):
    def test_checks_utility_model_only(self) -> None:
        page = MagicMock()
        boxes = {cid: MagicMock() for cid in ("fmgb", "fmsq", "xxsq", "wgsq")}

        def _qs(sel: str):
            cid = sel.lstrip("#")
            return boxes.get(cid)

        page.query_selector.side_effect = _qs
        apply_epub_type_filter(page, "utility_model")
        boxes["xxsq"].check.assert_called()
        boxes["fmgb"].uncheck.assert_called()
        boxes["wgsq"].uncheck.assert_called()


class SubmitIndexSearchTests(unittest.TestCase):
    def test_uses_committed_navigation_and_result_ready_wait(self) -> None:
        page = MagicMock()
        submit_index_search(page, "数据标注")
        page.expect_navigation.assert_called_once_with(timeout=40_000, wait_until="commit")
        page.wait_for_function.assert_called_once()
        self.assertEqual(page.wait_for_function.call_args.kwargs.get("timeout"), 40_000)
        page.wait_for_load_state.assert_not_called()
        page.wait_for_timeout.assert_not_called()

    def test_wait_checks_result_dom_not_title_only(self) -> None:
        page = MagicMock()
        submit_index_search(page, "数据标注")
        js = page.wait_for_function.call_args.args[0]
        self.assertIs(js, _RESULT_PAGE_READY_JS)
        self.assertIn("#result", js)
        self.assertIn("div.item", js)
        self.assertIn("h1.title", js)

    def test_applies_type_before_fill(self) -> None:
        page = MagicMock()
        boxes = {cid: MagicMock() for cid in ("fmgb", "fmsq", "xxsq", "wgsq")}
        page.query_selector.side_effect = lambda sel: boxes.get(sel.lstrip("#")) if sel.startswith("#f") or sel.startswith("#x") or sel.startswith("#w") or sel == "#indexForm" else (boxes.get(sel.lstrip("#")) if sel.startswith("#") else MagicMock())
        # simpler: always return MagicMock for form/search
        def qs(sel: str):
            if sel in ("#fmgb", "#fmsq", "#xxsq", "#wgsq"):
                return boxes[sel[1:]]
            return MagicMock()

        page.query_selector.side_effect = qs
        submit_index_search(page, "卡扣", patent_type="utility_model")
        page.fill.assert_called_with("#searchStr", "卡扣")
        boxes["xxsq"].check.assert_called()


class TitleConstantsTests(unittest.TestCase):
    def test_titles(self) -> None:
        self.assertEqual(EPUB_TITLE_RESULT, "专利查询结果展示")
        self.assertEqual(EPUB_TITLE_NO_HIT, "无查询结果")


class FailFastWaitTests(unittest.TestCase):
    def test_goto_uses_commit_and_30s(self) -> None:
        page = MagicMock()
        _goto(page, "http://epub.cnipa.gov.cn/", advanced=False)
        kwargs = page.goto.call_args.kwargs
        self.assertEqual(kwargs["wait_until"], "commit")
        self.assertEqual(kwargs["timeout"], 30_000)

    def test_goto_timeout_classified(self) -> None:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        page = MagicMock()
        page.goto.side_effect = PlaywrightTimeoutError("nav")
        with self.assertRaises(EpubNavError) as ctx:
            _goto(page, "http://epub.cnipa.gov.cn/Advanced", advanced=True)
        self.assertEqual(ctx.exception.stage, "goto")
        self.assertEqual(ctx.exception.hint, "keep_round1")

    def test_home_ready_skips_goto_when_box_present(self) -> None:
        page = MagicMock()
        page.query_selector.return_value = object()
        wait_for_epub_home_ready(page)
        page.goto.assert_not_called()
        page.wait_for_timeout.assert_not_called()

    def test_gate_checks_before_sleep(self) -> None:
        page = MagicMock()
        page.query_selector.return_value = object()
        _wait_selector(page, "#searchStr", advanced=False)
        page.wait_for_timeout.assert_not_called()

    def test_gate_timeout_classified(self) -> None:
        page = MagicMock()
        page.query_selector.return_value = None
        page.url = "http://epub.cnipa.gov.cn/"
        with self.assertRaises(EpubNavError) as ctx:
            _wait_selector(page, "#searchStr", advanced=False, max_wait_sec=0.05)
        self.assertEqual(ctx.exception.stage, "gate")
        self.assertEqual(ctx.exception.hint, "skip_epub")


class StopOnFirstFailureTests(unittest.TestCase):
    def test_later_hops_not_run(self) -> None:
        pw = MagicMock()
        pw.__enter__.return_value = pw
        pw.__exit__.return_value = None
        browser = MagicMock()
        ctx = MagicMock()
        page = MagicMock()
        ctx.new_page.return_value = page

        def _submit(_page, keyword, patent_type="all"):
            if keyword == "词2":
                raise EpubNavError("submit", hint="skip_epub", message="导航超时")

        cfg = dict(DEFAULTS)
        cfg["stop_on_first_nav_failure"] = True
        with patch("cnipa_epub_crawler.sync_playwright", return_value=pw):
            with patch("cnipa_epub_crawler._launch_browser", return_value=browser):
                with patch("cnipa_epub_crawler._new_context", return_value=ctx):
                    with patch("cnipa_epub_crawler.wait_for_epub_home_ready"):
                        with patch(
                            "cnipa_epub_crawler.submit_index_search",
                            side_effect=_submit,
                        ) as submit:
                            with patch(
                                "cnipa_epub_crawler._safe_page_content",
                                return_value="<html></html>",
                            ):
                                with patch(
                                    "cnipa_epub_crawler.parse_search_result_html",
                                    return_value=[],
                                ):
                                    with patch(
                                        "cnipa_epub_crawler.load_wait_config",
                                        return_value=cfg,
                                    ):
                                        rows = search_epub_keywords(
                                            ["词1", "词2", "词3"]
                                        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(submit.call_count, 2)


if __name__ == "__main__":
    unittest.main()
