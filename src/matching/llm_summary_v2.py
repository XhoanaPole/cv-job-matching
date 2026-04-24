import os
import urllib.request
import json
import concurrent.futures


def generate_single_summary(match_info):
    gap       = match_info.get('gap_analysis', {})
    breakdown = match_info.get('score_breakdown', {})
    fit_category = match_info.get('fit_category', 'moderate fit')

    # --- Score display ---
    final_score   = breakdown.get('final_hybrid', match_info.get('similarity_score', 0) * 100)
    semantic_pts  = breakdown.get('semantic_points',  0)
    skills_pts    = breakdown.get('skills_points',    0)
    domain_pts    = breakdown.get('domain_points',    0)
    edu_pts       = breakdown.get('education_points', 0)
    sen_pts       = breakdown.get('seniority_points', 0)

    # --- Domain & profile labels ---
    cv_domain   = breakdown.get('cv_domain',   'unknown')
    job_domain  = breakdown.get('job_domain',  'unknown')
    dom_compat  = breakdown.get('domain_compatibility', 'unknown')
    cv_edu      = breakdown.get('cv_education',  'unknown')
    job_edu     = breakdown.get('job_education', 'not specified')
    cv_sen      = breakdown.get('cv_seniority',  'unknown')
    job_sen     = breakdown.get('job_seniority', 'unknown')

    # --- Skills lists ---
    matched  = gap.get('matched_skills', [])[:8]
    missing  = gap.get('missing_skills', [])[:8]
    matched_str = ', '.join(matched) if matched else 'None'
    missing_str = ', '.join(missing) if missing else 'None'

    prompt = f"""
You are MatchAI, a friendly but highly analytical career assistant.
Your job is to cleanly analyze matching skills and explain CV-to-job matching results in a way that feels human, supportive, and easy to understand — like a mentor.

- CRITICAL: You MUST filter the skills lists down to ONLY actual professional skills. This includes Hard Skills, Soft Skills, Tooling, and Certifications. Delete noise words like "Able", "LI", "Brand".
- Format skills in Title Case, except for acronyms which must be ALL CAPS (e.g., 'EHR', 'SEO').
- CRITICAL TONE: You are speaking DIRECTLY to the candidate. Address them as 'you' and 'your'. NEVER refer to 'the candidate'. Do NOT use exact numbers or fractions in your text—keep it conceptual.
- CRITICAL ALIGNMENT: Your written analysis MUST perfectly align with the score. Note that domain matching is extremely important. If their domain matches, praise it. If not, point it out.
- Keep response under 150 words total excluding the skills lists.

DATA TO ANALYZE:
Overall Match Score     : {final_score:.1f}% ({fit_category})
Your domain             : {cv_domain}
Job domain              : {job_domain} (Match: {dom_compat})
Your education          : {cv_edu} vs Required: {job_edu}
Your seniority          : {cv_sen} vs Required: {job_sen}
Raw Matched Skills      : {matched_str}
Raw Missing Skills      : {missing_str}

Now respond using EXACT structure:
Clean_Matched_Skills:
[comma separated list of actual professional skills (hard or soft)]
Clean_Missing_Skills:
[comma separated list of actual professional skills (hard or soft)]
Strengths:
Explain clearly why your matched skills and profile make you a strong fit for this role.
Gaps:
What you are missing conceptually. Do not use numbers. Only mention domain/education if there's a mismatch.
Advice:
Give 2–3 very practical next steps or courses for you to improve.
Overall:
Explain whether you are a strong, moderate, or weak fit conceptually based on the data.
"""

    # === DEBUG: Check API key ===
    api_key = os.environ.get("OPENAI_API_KEY", "")
    print(f"[DEBUG] OPENAI_API_KEY present: {bool(api_key)}")
    if api_key:
        print(f"[DEBUG] Key length: {len(api_key)}, starts with: {api_key[:8]}...")
    else:
        print("[DEBUG] OPENAI_API_KEY is EMPTY — no API call will be made")

    if not api_key:
        match_info['llm_summary'] = "OpenAI API Key is missing. Please provide one to enable AI Analysis."
        return match_info

    # === DEBUG: Check what endpoint we're actually hitting ===
    endpoint = 'https://api.openai.com/v1/chat/completions'
    print(f"[DEBUG] Target endpoint: {endpoint}")

    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are MatchAI. You explain CV-job matches clearly and warmly like a mentor. "
                    "You are friendly but never vague or motivational without evidence. "
                    "You always stay grounded in the provided skills."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 800
    }).encode('utf-8')

    print(f"[DEBUG] Request payload size: {len(data)} bytes")
    print(f"[DEBUG] Model requested: gpt-4o-mini")

    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    )

    try:
        print(f"[DEBUG] Sending request to {endpoint}...")
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read().decode('utf-8')
            result = json.loads(raw)

            summary = result['choices'][0]['message']['content'].strip()
            print(f"[DEBUG] Summary length: {len(summary)} chars")

            import re
            cleaned_matched_match = re.search(r'Clean_Matched_Skills:\s*([\s\S]*?)(?=Clean_Missing_Skills:)', summary)
            cleaned_missing_match = re.search(r'Clean_Missing_Skills:\s*([\s\S]*?)(?=Strengths:)', summary)
            
            if cleaned_matched_match:
                cleaned_matched_str = cleaned_matched_match.group(1).strip()
                if gap:
                    gap['matched_skills'] = [s.strip().strip("[]") for s in cleaned_matched_str.split(',') if s.strip() and s.strip().lower() != 'none']
            if cleaned_missing_match:
                cleaned_missing_str = cleaned_missing_match.group(1).strip()
                if gap:
                    gap['missing_skills'] = [s.strip().strip("[]") for s in cleaned_missing_str.split(',') if s.strip() and s.strip().lower() != 'none']

            match_info['llm_summary'] = summary

    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"[DEBUG] HTTP ERROR {e.code}: {e.reason}")
        print(f"[DEBUG] Error body: {body[:500]}")
        match_info['llm_summary'] = (
            "We assessed your CV against the job description, "
            "but the AI service is currently unavailable."
        )
    except urllib.error.URLError as e:
        print(f"[DEBUG] URL ERROR (connection failed): {e.reason}")
        print(f"[DEBUG] This could mean: wrong endpoint, no internet, or firewall block")
        match_info['llm_summary'] = (
            "We assessed your CV against the job description, "
            "but the AI service is currently unavailable."
        )
    except Exception as e:
        print(f"[DEBUG] UNEXPECTED ERROR: {type(e).__name__}: {e}")
        match_info['llm_summary'] = (
            "We assessed your CV against the job description, "
            "but the AI service is currently unavailable."
        )

    return match_info


def enrich_matches_with_llm(matches):
    print(f"[DEBUG] === Starting LLM enrichment for {len(matches)} matches ===")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(generate_single_summary, matches))
    print(f"[DEBUG] === LLM enrichment complete ===")
    return matches