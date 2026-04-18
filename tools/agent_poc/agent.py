"""Browser-use agent for extracting job listings from career pages."""

import json
import logging
import posixpath
import time
from typing import Any
from urllib.parse import urlparse

from browser_use.agent.service import Agent
from browser_use.agent.views import ActionResult, AgentHistoryList
from browser_use.browser.profile import BrowserProfile
from browser_use.browser.session import BrowserSession
from browser_use.controller import Controller
from browser_use.llm.litellm.chat import ChatLiteLLM

from tools.agent_poc.config import DEFAULT_MAX_STEPS, DEFAULT_MODEL, GOAL_PROMPT
from tools.agent_poc.models import ExtractionResult

logger = logging.getLogger(__name__)


def _derive_path_prefix(sample_job_url: str) -> str:
    """Derive the job-link path prefix from a sample job URL.

    Takes the parent directory of the sample URL's path. For example:
    - "/jobs/7540236-senior-eng" -> "/jobs"
    - "/apply/17760976583210110395Pmz" -> "/apply"
    - "/careers/requirements/271/" -> "/careers/requirements"
    """
    path = urlparse(sample_job_url).path.rstrip("/")
    return posixpath.dirname(path) or "/"


def _build_controller(job_board_url: str, sample_job_url: str) -> Controller:
    """Build a Controller with a custom extract_job_links tool.

    Args:
        job_board_url: The career page URL (the listing page).
        sample_job_url: An example URL of an individual job posting, used
            to derive the path prefix that identifies valid job links.
    """
    controller: Controller = Controller()

    parsed = urlparse(job_board_url)
    origin_str = f"{parsed.scheme}://{parsed.netloc}"
    path_prefix = _derive_path_prefix(sample_job_url)

    @controller.registry.action(
        "Extract all job listing links from the current page. Call this "
        "once you have navigated to the job listings page, applied any "
        "filters, and scrolled to reveal all listings. The tool already "
        "knows how to identify valid job links. No arguments needed."
    )
    async def extract_job_links(
        browser_session: BrowserSession,
    ) -> ActionResult:
        page = await browser_session.get_current_page()
        if page is None:
            return ActionResult(error="No active page found")

        js_code = r"""([basePath, careerOrigin]) => {
            const anchors = Array.from(document.querySelectorAll('a'));
            const urls = new Set();
            for (const a of anchors) {
                const href = a.href || '';
                if (!href) continue;

                let linkUrl;
                try { linkUrl = new URL(href); }
                catch (e) { continue; }

                if (linkUrl.origin !== careerOrigin) continue;

                const linkPath = linkUrl.pathname.replace(/\/$/, '');
                if (linkPath === basePath) continue;
                if (!linkPath.startsWith(basePath + '/')) continue;

                urls.add(a.href);
            }
            return Array.from(urls);
        }"""

        urls = await page.evaluate(js_code, [path_prefix, origin_str])
        if isinstance(urls, str):
            urls = json.loads(urls)

        result = json.dumps({"jobs": urls or []})
        return ActionResult(
            is_done=True,
            extracted_content=result,
        )

    return controller


async def extract_jobs(
    company_name: str,
    job_board_url: str,
    sample_job_url: str,
    *,
    model: str = DEFAULT_MODEL,
    headless: bool = True,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> dict[str, Any]:
    """Extract job listings from a career page using browser-use agent.

    Args:
        company_name: Name of the company.
        job_board_url: URL of the career page (the job listing page).
        sample_job_url: Example URL of an individual job posting, used
            to determine which links on the job board are valid jobs.
        model: OpenAI model identifier.
        headless: Run browser in headless mode.
        max_steps: Maximum agent steps before stopping.

    Returns:
        Dict with company info, extraction result, and metadata.
    """
    llm = ChatLiteLLM(model=f"openai/{model}", temperature=1)
    controller = _build_controller(job_board_url, sample_job_url)
    browser_profile = BrowserProfile(headless=headless)
    browser_session = BrowserSession(browser_profile=browser_profile)

    task = f"Go to {job_board_url}\n\n{GOAL_PROMPT}"

    agent: Agent = Agent(
        task=task,
        llm=llm,
        browser_session=browser_session,
        controller=controller,
        use_vision=False,
        max_actions_per_step=3,
        max_failures=3,
    )

    start_time = time.time()
    history: AgentHistoryList | None = None

    try:
        history = await agent.run(max_steps=max_steps)
        elapsed = time.time() - start_time

        result = _parse_result(history)
        return _build_output(
            company_name=company_name,
            company_url=job_board_url,
            model=model,
            result=result,
            history=history,
            elapsed=elapsed,
            error=None,
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.exception("Agent extraction failed for %s", company_name)
        return _build_output(
            company_name=company_name,
            company_url=job_board_url,
            model=model,
            result=None,
            history=history,
            elapsed=elapsed,
            error=str(e),
        )
    finally:
        await browser_session.stop()


def _parse_result(history: AgentHistoryList) -> ExtractionResult | None:
    """Parse structured extraction result from agent history."""
    raw = history.final_result()
    if not raw:
        return None

    # Try direct parse
    try:
        return ExtractionResult.model_validate_json(raw)
    except Exception:
        pass

    # Try parsing as JSON, handling double-encoded values
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        data = json.loads(text)
        # Handle double-encoded jobs field
        if isinstance(data.get("jobs"), str):
            data["jobs"] = json.loads(data["jobs"])
        return ExtractionResult.model_validate(data)
    except Exception:
        logger.warning("Could not parse agent output: %s", raw[:200])
        return None


def _build_output(
    *,
    company_name: str,
    company_url: str,
    model: str,
    result: ExtractionResult | None,
    history: AgentHistoryList | None,
    elapsed: float,
    error: str | None,
) -> dict[str, Any]:
    """Build the final output dict with extraction results and metadata."""
    jobs_data = result.model_dump()["jobs"] if result else []

    return {
        "company": company_name,
        "url": company_url,
        "jobs": jobs_data,
        "metadata": {
            "model": model,
            "total_jobs_found": len(jobs_data),
            "extraction_time_seconds": round(elapsed, 2),
            "agent_steps": history.number_of_steps() if history else 0,
            "agent_completed": history.is_done() if history else False,
            "agent_had_errors": history.has_errors() if history else True,
            "error": error,
        },
    }
