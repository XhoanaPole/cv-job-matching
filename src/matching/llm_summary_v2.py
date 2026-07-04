import os
import re
import urllib.request
import json
import concurrent.futures


def _is_skill_in_cv(skill: str, cv_text: str) -> bool:
    """Case/format-insensitive check for whether `skill` is literally present in the CV text.
    Used to catch cases where the LLM flags a skill as missing despite it being
    explicitly listed (e.g. 'Power BI' vs 'PowerBI')."""
    skill_lower = skill.lower().strip()
    cv_lower = cv_text.lower()
    if skill_lower in cv_lower:
        return True
    skill_norm = re.sub(r'[\s\-_/]', '', skill_lower)
    if len(skill_norm) >= 4:
        cv_norm = re.sub(r'[\s\-_/]', '', cv_lower)
        if skill_norm in cv_norm:
            return True
    return False


def generate_single_summary(match_info):
    gap       = match_info.get('gap_analysis', {})
    breakdown = match_info.get('score_breakdown', {})
    fit_category = match_info.get('fit_category', 'moderate fit')

    final_score = breakdown.get('final_hybrid', match_info.get('similarity_score', 0) * 100)

    # Raw texts — injected by main.py into every match dict
    cv_text  = match_info.get('cv_text',  '')[:3000]   # truncate to stay within token budget
    job_text = match_info.get('job_text', '')[:2000]

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        match_info['llm_summary'] = "OpenAI API Key is missing. Please provide one to enable AI Analysis."
        return match_info

    # If we don't have the raw texts yet, fall back gracefully
    if not cv_text or not job_text:
        match_info['llm_summary'] = "Raw document text unavailable for AI skill extraction."
        return match_info

    prompt = f"""You are MatchAI, a career mentor AI.

OFFICIAL MATCH SCORE: {final_score:.1f}% — this is the authoritative hybrid score calculated by the system. Your summary MUST reference this exact number. Do NOT calculate or mention any other overall percentage.

STRICT RULES — read before anything else:
- "matched_skills" MUST contain only skills from the JOB DESCRIPTION that are also clearly present or demonstrated in the candidate's CV (either as exact matches or direct semantic synonyms).
- "missing_skills" MUST contain skills from the JOB DESCRIPTION that are required or preferred but are completely absent from the candidate's CV.
- Do NOT assume the candidate has specialized platform/tool skills (like "SQL", "Python", "Google Ads", "Facebook Ads") unless they are explicitly listed in their CV.
- Extract only NOUNS and NOUN PHRASES that are professional skills, tools, software, certifications, or qualifications (e.g., "Python", "Project Management", "Adobe Photoshop")
- NEVER extract: adjectives (long, strong, good), adverbs, verbs, or standalone generic words (experience, work, team, able, provide, manage, support, knowledge, background, ability)
- NEVER extract: standalone platform names (Facebook, Instagram, LinkedIn, Tiktok, Snapchat) unless they are part of a specific technical competency (e.g., "Facebook Ads", "LinkedIn Sales Navigator")
- NEVER extract: scheduling info (8AM-5PM, Monday-Friday, full-time, part-time, weekends, shifts)
- NEVER extract: locations (London, remote, on-site, hybrid)
- NEVER extract: years of experience (3 years, entry-level, senior)
- Format: Title Case for multi-word phrases ("Patient Care", "Data Analysis"), ALL CAPS for acronyms ("EHR", "AWS", "SQL")
- If unsure whether something is a real professional skill — leave it out
- Respond ONLY with valid JSON. No markdown, no extra text.

CV:
{cv_text}

JOB DESCRIPTION:
{job_text}

Return ONLY this JSON:
{{
  "matched_skills": ["Skill One", "Skill Two"],
  "missing_skills": ["Skill Three", "Skill Four"],
  "summary": "1-2 warm sentences addressing the candidate as you. Must state the overall match is {final_score:.1f}% ({fit_category}) and align your tone with that tier."
}}"""

    endpoint = 'https://api.openai.com/v1/chat/completions'
    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are MatchAI, a career mentor. You ALWAYS respond with valid JSON only. No markdown, no extra text."
            },
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": 600
    }).encode('utf-8')

    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw    = response.read().decode('utf-8')
            result = json.loads(raw)
            content = result['choices'][0]['message']['content'].strip()
            parsed  = json.loads(content)

            # Safeguard: if the LLM flags a skill as missing but it's literally
            # present in the CV text, move it to matched_skills instead.
            matched_skills = parsed.get('matched_skills', [])
            missing_skills = parsed.get('missing_skills', [])
            still_missing = []
            for skill in missing_skills:
                if _is_skill_in_cv(skill, cv_text):
                    matched_skills.append(skill)
                else:
                    still_missing.append(skill)
            parsed['matched_skills'] = matched_skills
            parsed['missing_skills'] = still_missing

            # Write cleaned skills back to gap_analysis so the UI gets them
            if gap is not None:
                if 'matched_skills' in parsed:
                    gap['matched_skills'] = parsed['matched_skills']
                if 'missing_skills' in parsed:
                    gap['missing_skills'] = parsed['missing_skills']
                gap['skills_source'] = 'llm'

            match_info['llm_summary'] = parsed.get('summary', '')

    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"[DEBUG] HTTP ERROR {e.code}: {e.reason} — {body[:300]}")
        match_info['llm_summary'] = "AI service temporarily unavailable."
        if gap is not None: gap['skills_source'] = 'nlp_fallback'
    except urllib.error.URLError as e:
        print(f"[DEBUG] URL ERROR: {e.reason}")
        match_info['llm_summary'] = "AI service temporarily unavailable."
        if gap is not None: gap['skills_source'] = 'nlp_fallback'
    except Exception as e:
        print(f"[DEBUG] UNEXPECTED ERROR: {type(e).__name__}: {e}")
        match_info['llm_summary'] = "AI service temporarily unavailable."
        if gap is not None: gap['skills_source'] = 'nlp_fallback'

    return match_info



def enrich_matches_with_llm(matches):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(generate_single_summary, matches))
    return matches