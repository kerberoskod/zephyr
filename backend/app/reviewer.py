from anthropic import AsyncAnthropic
from app.config import settings


REVIEW_PROMPT = """You are Zephyr, an expert code reviewer. Analyze the following pull request diff and provide a thorough review.

Focus on:
1. **Bugs & Logic Errors** — Logic flaws, off-by-one, race conditions, null pointers
2. **Security Issues** — Injection, leaks, auth bypass, hardcoded secrets
3. **Code Quality** — Duplication, readability, naming, SOLID principles
4. **Performance** — N+1 queries, unnecessary allocations, blocking calls
5. **Style & Consistency** — Deviations from project conventions

For each finding, include:
- **severity**: critical | major | minor
- **category**: bug | security | quality | performance | style
- **file**: the file path
- **line**: approximate line number (from diff)
- **message**: clear explanation
- **suggestion**: how to fix it

If the code looks good, still provide a brief positive summary.

<diff>
{diff}
</diff>

Return your response as valid JSON with this structure:
{{
  "summary": "brief overview of the changes and overall quality",
  "findings": [
    {{
      "severity": "critical|major|minor",
      "category": "bug|security|quality|performance|style",
      "file": "path/to/file.ts",
      "line": 42,
      "message": "description of the issue",
      "suggestion": "how to fix it"
    }}
  ]
}}
"""


class Reviewer:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def review_diff(self, diff: str) -> dict:
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system="You are an expert code reviewer. Always respond with valid JSON only.",
            messages=[
                {
                    "role": "user",
                    "content": REVIEW_PROMPT.format(diff=diff[:100000]),
                }
            ],
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]
        if content.startswith("```json"):
            content = content[7:]

        import json

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "summary": "Review completed but response parsing failed",
                "findings": [],
                "_raw": content,
            }
