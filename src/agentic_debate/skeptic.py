from openai import AsyncOpenAI
import os

class SkepticAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def analyze(self, cv_text: str, job_text: str, faiss_score: float) -> str:
        prompt = f"""
        You are the 'Skeptic Agent' in an AI recruitment debate.
        Your job is to act as a rigorous technical interviewer and play devil's advocate.
        You must critically analyze the CV against the Job Description and point out exaggerated skills, missing critical requirements, and potential risks of hiring this candidate.
        
        FAISS Semantic Similarity Score: {faiss_score}%
        
        CV:
        {cv_text}
        
        Job Description:
        {job_text}
        
        Output a single paragraph (max 150 words) making the strongest possible case for why this candidate might STRUGGLE in this role.
        Be objective, professional, but ruthless.
        """
        
        if not self.api_key:
            return "Skeptic Agent: Several potential gaps exist but API key is missing to run deep analysis."

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a rigorous, highly critical technical interviewer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # Lower temperature for more factual, critical reasoning
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Skeptic Agent Error: {str(e)}"
