from openai import AsyncOpenAI
import os
import json


class RoadmapAgent:
    """
    Generates a 3-tier personalised career learning plan (0–3 / 3–6 / 6–12 months)
    based on the skill gaps identified by the Judge.
    """

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(self, cv_text: str, job_text: str, gaps: str, fit_score: float) -> dict:
        prompt = f"""
You are a career development specialist. A candidate has been assessed against a target role.

Match Score: {fit_score:.1f}%
Judge's Gap Summary: {gaps}

Candidate CV (excerpt):
{cv_text[:2000]}

Target Job Description (excerpt):
{job_text[:2000]}

STEP 1 — Before writing the roadmap, read the Job Description carefully and extract the 3–5 most important skills, tools, or qualifications that the JD requires but the CV does NOT demonstrate. Write them as a mental list — these are your anchors.

STEP 2 — Build a 3-tier roadmap where EVERY action names at least one of those specific missing skills/tools/qualifications by name. Do NOT write generic actions like "take a course", "network", or "find a mentor" without naming what specific skill to learn or which specific community to join.

Return ONLY valid JSON with exactly this structure:
{{
  "short_term": {{
    "label": "0–3 Months",
    "focus": "One sentence naming the most critical missing skill to close first.",
    "actions": ["Specific action referencing a named skill/tool 1", "Specific action 2", "Specific action 3"]
  }},
  "medium_term": {{
    "label": "3–6 Months",
    "focus": "One sentence describing building hands-on evidence for the gaps.",
    "actions": ["Specific action referencing a named skill/tool 1", "Specific action 2", "Specific action 3"]
  }},
  "long_term": {{
    "label": "6–12 Months",
    "focus": "One sentence about positioning for the target role with the new skills.",
    "actions": ["Specific action referencing a named skill/tool 1", "Specific action 2", "Specific action 3"]
  }}
}}

Hard rules:
- Every action MUST name a specific skill, tool, certification, or platform from the JD (e.g. "Complete the Google Data Analytics Certificate on Coursera to build SQL and data visualisation skills required by this role").
- NEVER write: "take a relevant course", "network with professionals", "seek a mentor", "build your portfolio" — unless those generic phrases are followed by the SPECIFIC skill or domain name.
- Do NOT mention FAISS, embeddings, cosine similarity, or any AI/system internals.
- Write directly to the candidate in encouraging, professional language.
"""

        if not self.api_key:
            return self._fallback()

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a career development specialist. Respond ONLY with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=600
            )
            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)
            return {
                "short_term":  parsed.get("short_term",  {}),
                "medium_term": parsed.get("medium_term", {}),
                "long_term":   parsed.get("long_term",   {}),
            }
        except Exception:
            return self._fallback()

    def _fallback(self) -> dict:
        return {
            "short_term": {
                "label":   "0–3 Months",
                "focus":   "Close the most critical skill gaps with targeted online learning.",
                "actions": [
                    "Identify the top 3 skills required by this role and enrol in a free course for each.",
                    "Set a daily 30-minute study block and track progress in a simple journal.",
                    "Build one small personal project that directly uses a missing skill."
                ]
            },
            "medium_term": {
                "label":   "3–6 Months",
                "focus":   "Build demonstrable, portfolio-ready experience.",
                "actions": [
                    "Complete a recognised certification in the primary skill gap area.",
                    "Contribute to an open-source or volunteer project in the target domain.",
                    "Update your CV and LinkedIn to highlight newly acquired skills and projects."
                ]
            },
            "long_term": {
                "label":   "6–12 Months",
                "focus":   "Target the role and apply with confidence.",
                "actions": [
                    "Apply to at least 5 entry-level or lateral positions in this domain.",
                    "Connect with a mentor or join a professional community in the field.",
                    "Set a stretch goal: aim for a role one seniority level above your starting target."
                ]
            }
        }
