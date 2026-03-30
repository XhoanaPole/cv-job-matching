import os
import urllib.request
import json
import concurrent.futures


def generate_single_summary(match_info):
    gap = match_info.get('gap_analysis', {})
    raw_score = match_info.get('similarity_score', 0)
    score = min(100.0, max(0.0, raw_score * 100.0))
    matched = gap.get('matched_skills', [])[:8]
    missing = gap.get('missing_skills', [])[:8]
    matched_str = ', '.join(matched) if matched else "None"
    missing_str = ', '.join(missing) if missing else "None"

    prompt = f"""
You are MatchAI, a friendly but highly analytical career assistant.
Your job is to explain CV-to-job matching results in a way that feels human, supportive, and easy to understand — like a mentor talking to a student.
You MUST follow these rules:
- Be friendly, but NEVER vague or generic
- Do NOT use phrases like "you're on a great path"
- Base everything ONLY on the provided skills
- Be specific and grounded in evidence
- Keep response under 120 words
- No markdown, no bullet points formatting outside structure below
- CRITICAL: Acknowledge their exact match percentage in the 'Overall' section.
DATA:
FAISS Semantic Match Score: {score:.1f}%
Matched Skills: {matched_str}
Missing Skills: {missing_str}
Now respond using EXACT structure:
Strengths:
Explain clearly why the matched skills make the candidate a good fit.
Gaps:
Explain what is missing and why it matters for the role.
Advice:
Give 2–3 very practical next steps to improve.
Overall:
Reference their {score:.1f}% match score. Explain whether this is a strong, moderate, or weak fit based on the percentage, and briefly explain why this specific job ranked the way it did.
Tone:
Friendly, supportive, like a helpful mentor explaining things clearly to a student.
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

    # === DEBUG: Check if OPENAI_API_BASE or similar overrides exist ===
    for env_var in ['OPENAI_API_BASE', 'OPENAI_BASE_URL', 'OLLAMA_HOST', 'OLLAMA_API_BASE']:
        val = os.environ.get(env_var)
        if val:
            print(f"[DEBUG] WARNING: {env_var} is set to: {val}")

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
        "max_tokens": 220
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
            # === DEBUG: Check actual response details ===
            print(f"[DEBUG] Response status: {response.status}")
            print(f"[DEBUG] Response URL (after redirects): {response.url}")
            print(f"[DEBUG] Response headers:")
            for header in ['server', 'x-request-id', 'openai-organization', 'openai-model']:
                val = response.getheader(header)
                if val:
                    print(f"[DEBUG]   {header}: {val}")

            raw = response.read().decode('utf-8')
            result = json.loads(raw)

            # === DEBUG: Check what model actually responded ===
            model_used = result.get('model', 'UNKNOWN')
            usage = result.get('usage', {})
            print(f"[DEBUG] Model that responded: {model_used}")
            print(f"[DEBUG] Token usage: {usage}")
            print(f"[DEBUG] Response ID: {result.get('id', 'UNKNOWN')}")

            summary = result['choices'][0]['message']['content'].strip()
            print(f"[DEBUG] Summary length: {len(summary)} chars")
            print(f"[DEBUG] Summary preview: {summary[:100]}...")

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