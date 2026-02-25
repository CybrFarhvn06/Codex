import json
import os
from textwrap import dedent
from typing import Any, Dict, List
from urllib import error, request


class PromptEngine:
    """Prompt templates for deep scientific-research generation."""

    @staticmethod
    def build_system_prompt() -> str:
        return dedent(
            """
            You are a scientific research assistant for students.
            Produce rigorous yet easy-to-understand outputs.
            Include evidence-oriented literature analysis, research gap detection,
            a feasible student-level methodology, simulated quantitative results,
            references, PPT outline, viva questions, and tools/datasets suggestions.
            Return valid JSON only.
            """
        ).strip()

    @staticmethod
    def build_user_prompt(topic: str, query: str) -> str:
        return dedent(
            f"""
            Student topic: {topic}
            Student research query: {query}

            Return JSON with these keys exactly:
            abstract, introduction, literature_review, research_gaps,
            methodology, simulated_results, conclusion, references,
            ppt_outline, viva_questions, datasets_and_tools.

            Requirements:
            - literature_review must include source + finding entries from: Google Scholar, IEEE Xplore, PubMed
            - methodology must include design + steps
            - simulated_results must include summary + table[] with metric, baseline, proposed
            - references must be a list of citation strings
            - datasets_and_tools must include datasets[] and tools[]
            """
        ).strip()


class ResearchService:
    """Deep-research synthesis service with optional OpenAI HTTP integration."""

    REQUIRED_KEYS = {
        "abstract",
        "introduction",
        "literature_review",
        "research_gaps",
        "methodology",
        "simulated_results",
        "conclusion",
        "references",
        "ppt_outline",
        "viva_questions",
        "datasets_and_tools",
    }

    @staticmethod
    def _simulate_sources(topic: str) -> List[Dict[str, str]]:
        return [
            {
                "source": "Google Scholar",
                "finding": f"Recent studies on {topic} show measurable gains from hybrid and retrieval-augmented AI pipelines.",
            },
            {
                "source": "IEEE Xplore",
                "finding": f"Engineering papers report trade-offs between model accuracy, latency, and deployment cost in {topic} systems.",
            },
            {
                "source": "PubMed",
                "finding": f"Human-impact studies emphasize ethics, safety, and reproducibility for {topic}-related interventions.",
            },
        ]

    @classmethod
    def _fallback_report(cls, topic: str, query: str) -> Dict[str, Any]:
        return {
            "abstract": (
                f"This project investigates {topic} with a scientist-style workflow. "
                f"It addresses '{query}' through literature synthesis, gap detection, and a practical student-level methodology."
            ),
            "introduction": (
                f"{topic} is an important research area in both academia and industry. "
                "This report explains the current state of knowledge and where a student can contribute new findings."
            ),
            "literature_review": cls._simulate_sources(topic),
            "research_gaps": [
                "Limited benchmarking in low-resource student lab environments.",
                "Inconsistent reproducibility due to missing open protocols and code-sharing.",
                "Few studies jointly evaluate technical performance and real-world usability.",
            ],
            "methodology": {
                "design": "Mixed-method design: quantitative model benchmarking plus qualitative expert/student feedback.",
                "steps": [
                    "Collect and preprocess open datasets relevant to the topic.",
                    "Implement baseline methods and at least one improved approach.",
                    "Measure performance with Accuracy, F1, precision/recall, and latency.",
                    "Analyze error patterns and compare findings with published work.",
                    "Summarize limitations and propose future experiments.",
                ],
            },
            "simulated_results": {
                "summary": "The proposed method is expected to improve baseline quality metrics while maintaining practical inference speed.",
                "table": [
                    {"metric": "Accuracy", "baseline": "78%", "proposed": "86%"},
                    {"metric": "F1 Score", "baseline": "0.74", "proposed": "0.83"},
                    {"metric": "Latency", "baseline": "210ms", "proposed": "185ms"},
                ],
            },
            "conclusion": (
                f"The study offers a feasible roadmap for student research on {topic}. "
                "It identifies concrete research gaps and a publishable experiment plan."
            ),
            "references": [
                f"A. Kumar et al. (2023). Advances in {topic}. Journal of Student Research, 12(4), 1-20.",
                f"L. Chen & P. Smith (2022). Benchmarking {topic} systems under practical constraints. IEEE Learning Systems.",
                f"R. Diaz et al. (2024). Reproducibility and ethics in {topic}. International Review of Applied AI.",
            ],
            "ppt_outline": [
                "Problem statement and motivation",
                "Literature landscape and gap analysis",
                "Research objectives and hypotheses",
                "Methodology and experimental setup",
                "Simulated/expected results",
                "Conclusion, limitations, and future work",
            ],
            "viva_questions": [
                "Why did you choose this topic and what problem does it solve?",
                "How is your methodology better or different than prior work?",
                "What are the strongest limitations of your current design?",
                "How would you validate generalization on larger or noisier datasets?",
                "What ethical or bias issues could affect your findings?",
            ],
            "datasets_and_tools": {
                "datasets": [
                    "Kaggle domain datasets",
                    "UCI Machine Learning Repository",
                    "Government open-data portals",
                ],
                "tools": [
                    "Python (Pandas, scikit-learn, PyTorch)",
                    "Jupyter Notebook",
                    "Zotero or Mendeley",
                    "Tableau or Power BI",
                ],
            },
        }

    @classmethod
    def _try_openai_json(cls, topic: str, query: str) -> Dict[str, Any] | None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": PromptEngine.build_system_prompt()},
                {"role": "user", "content": PromptEngine.build_user_prompt(topic, query)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=45) as response:
                raw = json.loads(response.read().decode("utf-8"))
            content = raw["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if cls.REQUIRED_KEYS.issubset(set(parsed.keys())):
                return parsed
        except (error.URLError, error.HTTPError, KeyError, json.JSONDecodeError, TimeoutError):
            return None

        return None

    @classmethod
    def generate_report(cls, topic: str, query: str) -> Dict[str, Any]:
        external = cls._try_openai_json(topic, query)
        if external:
            return external

        report = cls._fallback_report(topic, query)
        report["prompt_debug"] = {
            "system_prompt": PromptEngine.build_system_prompt(),
            "user_prompt": PromptEngine.build_user_prompt(topic, query),
            "source": "fallback",
        }
        return report
