import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agentic_debate.orchestrator import DebateOrchestrator

async def main():
    print("=== INITIALIZING AGENTIC DEBATE TEST ===")
    
    cv_text = """
    John Doe
    Software Engineer with 2 years of experience.
    Skills: Python, JavaScript, React, HTML/CSS.
    Experience: Built web applications using Django and React. Maintained basic databases.
    """
    
    job_text = """
    Senior Python Backend Developer
    We are looking for a Senior Developer with 5+ years of experience.
    Must have expert knowledge in Python, FastAPI, Docker, Kubernetes, and AWS cloud architecture.
    Experience scaling high-traffic microservices is required.
    """
    
    faiss_score = 45.2  # Artificial low score to make the debate interesting
    
    orchestrator = DebateOrchestrator()
    
    print("\n[Running Agents in Parallel... Please wait 3-5 seconds]")
    result = await orchestrator.run_debate(cv_text, job_text, faiss_score)
    
    print("\n===========================================")
    print("ADVOCATE AGENT'S ARGUMENT:")
    print("-------------------------------------------")
    print(result['debate_logs']['advocate'])
    
    print("\n===========================================")
    print("SKEPTIC AGENT'S ARGUMENT:")
    print("-------------------------------------------")
    print(result['debate_logs']['skeptic'])
    
    print("\n===========================================")
    print("JUDGE AGENT'S FINAL VERDICT:")
    print("-------------------------------------------")
    print(result['final_summary'])
    print("===========================================")

if __name__ == "__main__":
    asyncio.run(main())
