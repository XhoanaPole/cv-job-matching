# Architectural Evolution: Multi-Agent Collaboration

Moving from a single linear algorithm to a **Multi-Agent System (MAS)** transforms the project from a standard script into cutting-edge Enterprise AI. By breaking the monolithic pipeline into specialized, collaborative AI Agents, the system achieves unprecedented scalability and intelligence.

## 1. The Orchestrator Agent (The Manager)
Instead of the backend blindly processing files, this Agent receives the user's CV and Job URLs. It assesses the complexity of the request and delegates tasks to the sub-agents. It evaluates their outputs before returning the final JSON to the frontend.

## 2. The Extraction Agent (The Data Miner)
Currently, the `SkillsExtractor` relies on regex and basic NLP. This new Agent uses a Large Language Model (LLM) to intelligently read the documents. It doesn't just look for keywords; it understands context (e.g., *"This candidate used React.js 5 years ago, but the job requires recent React experience."*).

## 3. The Embedding Agent (The Core Analytics Engine)
This Agent specializes exclusively in mathematics. It takes the structured data from the Extraction Agent, runs it through the existing `SentenceTransformers`, and performs the lightning-fast `FAISS` vector similarity searches already built into the core functionality.

## 4. The Career Coaching Agent (The Product Value Add)
This is where the true user value lies. Once the embedding score and Gap Analysis are calculated, the Orchestrator passes the results to the Coaching Agent. This agent dynamically generates:
- A custom, tailored **Cover Letter** explaining why the candidate is a match.
- Specific **Interview Prep** questions based on the "Missing Skills" gap.
- Strategic **Career Advice** on which courses the candidate should take to boost their 60% match to an 85% match.

## Implementation Strategy
To implement this pipeline in Python, the backend architecture would be migrated to integrate with an agentic framework like **CrewAI** or **LangChain's LangGraph**. The specific "Roles" and "Goals" for each specialized agent are explicitly defined, and the existing FAISS index is provided to the Orchestrator as a "Tool" the agents can utilize to formulate responses. This decentralized, decoupled approach represents the absolute forefront of modern Artificial Intelligence software engineering.
