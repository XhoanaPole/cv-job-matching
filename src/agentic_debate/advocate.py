from openai import AsyncOpenAI
import os

class AdvocateAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def analyze(self, cv_text: str, job_text: str, faiss_score: float) -> str:
        prompt = f"""
        You are the 'Advocate Agent' in an AI recruitment debate.
        Your job is to fiercely defend the candidate. 
        You must find every possible alignment, transferable skill, and positive trajectory connecting their CV to the Job Description.
        Even if there are gaps, explain why the candidate is still a great fit based on their proven ability to learn or adapt.
        
        FAISS Semantic Similarity Score: {faiss_score}%
        
        CV:
        {cv_text}
        
        Job Description:
        {job_text}
        
        Output a single paragraph (max 150 words) making the strongest possible case for why this candidate should be hired.
        Focus on evidence.
        """
        
        if not self.api_key:
            return "Advocate Agent: Candidate shows strong potential but API key is missing to run deep analysis."

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a fierce advocate for the candidate."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Advocate Agent Error: {str(e)}"
