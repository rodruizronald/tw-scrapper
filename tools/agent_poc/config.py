"""Configuration for the agent PoC: test companies and agent settings."""

COMPANIES: list[dict[str, str]] = [
    {
        "name": "Growth Acceleration Partners",
        "job_board_url": "https://careers.wearegap.com/jobs",
        "sample_job_url": "https://careers.wearegap.com/jobs/7540236-senior-python-aws-software-engineer",
    },
    {
        "name": "Akurey",
        "job_board_url": "https://www.akurey.com/careers/",
        "sample_job_url": "https://www.akurey.com/careers/requirements/271/",
    },
    {
        "name": "Golabs Tech",
        "job_board_url": "https://recruitcrm.io/jobs/Golabs_Tech_jobs",
        "sample_job_url": "https://recruitcrm.io/apply/17760976583210110395Pmz",
    },
]

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_STEPS = 20

GOAL_PROMPT = """\
You are on a company career page with a job board listing open positions. \
Your task is to extract the title and URL for each job listing.

STEP 1 — FILTER (optional):
Before extracting, look for any location or region filter on the page \
(dropdown, checkbox, search box, tags, etc.). If one exists:
- Try to select "Costa Rica" or "CR"
- If that is not available, try "LATAM" or "Latin America"
- If none of these options exist, skip filtering and proceed with all listings

STEP 2 — EXTRACT:
Once the page is ready (filters applied, content loaded, scrolled to \
reveal all listings), call the extract_job_links tool. It takes no \
arguments — the tool already knows how to identify valid job links \
based on the company configuration.

IMPORTANT:
- Do NOT click into individual job pages. Stay on the listing page.
- If you need to scroll to reveal more listings, do so before extracting.
- Use the extract_job_links tool to extract — do NOT use find_elements.
"""
