from openai import AsyncOpenAI
import os
import json

class JudgeAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def decide(self, faiss_score: float, advocate_argument: str, skeptic_argument: str, cv_text: str = "", job_text: str = "") -> dict:
        prompt = f"""
        You are the 'Judge Agent' (a Senior Career Coach writing for a professional career platform).
        Two agents have debated a candidate's fit for a role. The overall compatibility is {faiss_score:.1f}%.
        
        Candidate CV:
        {cv_text[:4000]}

        Job Description:
        {job_text[:4000]}
        
        Advocate (FOR the candidate): "{advocate_argument}"
        Skeptic (AGAINST the candidate): "{skeptic_argument}"
        
        Synthesize the debate into a structured JSON response with exactly these four keys:
        - "overall": 2-3 warm sentences addressing the candidate directly by their first name (extracted from the CV, e.g., "Maria, your profile is currently a 10% match (Weak Fit) for the Paid Advertising Specialist role..."). If the CV name is a placeholder (like "NAME SURNAME", "Your Name", "John Doe") or is missing, address them as "Candidate," or start directly without a name. Explain contextually how their background domain (e.g., medicine) matches or differs from the target job domain (e.g., performance marketing), and note the main conceptual shift required.
        - "strengths": 1-2 sentences about their strongest points from the Advocate.
        - "gaps": 1-2 sentences about the critical weaknesses from the Skeptic.
        - "advice": Exactly 3 concrete, actionable steps the candidate can take to improve. Format as a numbered list: "1. [step] 2. [step] 3. [step]" — each step on its own line starting with the number and a period.
        
        IMPORTANT RULES:
        - Write like a professional career coach talking directly to a job seeker.
        - NEVER use any of these technical terms: FAISS, semantic score, embedding, cosine similarity, vector, NLP, machine learning, similarity index, or any AI/ML jargon.
        - Use natural, professional language only (e.g. "match score", "compatibility", "profile alignment").
        - Respond ONLY with valid JSON. No markdown, no extra text.
        """

        if not self.api_key:
            return {
                "overall": "AI Service unavailable. Please check your OpenAI API key.",
                "strengths": "N/A",
                "gaps": "N/A",
                "advice": "N/A"
            }

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are MatchAI, a career mentor. You ALWAYS respond with valid JSON only, containing exactly the keys: overall, strengths, gaps, advice. No markdown, no extra text."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
                max_tokens=500
            )
            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)

            # Guarantee all 4 keys exist
            return {
                "overall": parsed.get("overall", "No overall analysis provided."),
                "strengths": parsed.get("strengths", "No strengths identified."),
                "gaps": parsed.get("gaps", "No gaps identified."),
                "advice": parsed.get("advice", "No advice available.")
            }
        except Exception as e:
            return {
                "overall": f"Judge Agent Error: {str(e)}",
                "strengths": "N/A",
                "gaps": "N/A",
                "advice": "N/A"
            }
