import asyncio
import logging
from .advocate import AdvocateAgent
from .skeptic import SkepticAgent
from .judge import JudgeAgent
from .roadmap import RoadmapAgent

logger = logging.getLogger(__name__)

class DebateOrchestrator:
    """
    Coordinates the autonomous debate between the Advocate, Skeptic, and Judge,
    then generates a personalised Career Roadmap via the RoadmapAgent.
    """

    def __init__(self, api_key=None):
        self.advocate = AdvocateAgent(api_key=api_key)
        self.skeptic = SkepticAgent(api_key=api_key)
        self.judge = JudgeAgent(api_key=api_key)
        self.roadmap_agent = RoadmapAgent(api_key=api_key)

    async def run_debate(self, cv_text: str, job_text: str, faiss_score: float) -> dict:
        """
        Executes the full multi-agent pipeline.
        Returns the final verdict, career roadmap, and the internal debate logs.
        """
        logger.debug("Starting Agentic Debate for score: %.1f%%", faiss_score)

        # Run Advocate and Skeptic in parallel
        advocate_arg, skeptic_arg = await asyncio.gather(
            self.advocate.analyze(cv_text, job_text, faiss_score),
            self.skeptic.analyze(cv_text, job_text, faiss_score),
        )

        logger.debug("Judge is synthesizing the verdict...")
        final_verdict = await self.judge.decide(faiss_score, advocate_arg, skeptic_arg, cv_text, job_text)

        logger.debug("RoadmapAgent is generating the career plan...")
        roadmap = await self.roadmap_agent.generate(
            cv_text=cv_text,
            job_text=job_text,
            gaps=final_verdict.get("gaps", ""),
            fit_score=faiss_score,
        )

        logger.debug("Debate concluded.")

        return {
            "overall":  final_verdict.get("overall", ""),
            "strengths": final_verdict.get("strengths", ""),
            "gaps":      final_verdict.get("gaps", ""),
            "advice":    final_verdict.get("advice", ""),
            "roadmap":   roadmap,
            "debate_logs": {
                "advocate": advocate_arg,
                "skeptic":  skeptic_arg,
            }
        }
