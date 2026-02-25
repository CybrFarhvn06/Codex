import os
import unittest

from research_engine import PromptEngine, ResearchService


class PromptEngineTests(unittest.TestCase):
    def test_system_prompt_mentions_json(self):
        prompt = PromptEngine.build_system_prompt()
        self.assertIn("Return valid JSON", prompt)

    def test_user_prompt_contains_required_keys(self):
        prompt = PromptEngine.build_user_prompt("Edge AI", "How to optimize edge inference?")
        self.assertIn("abstract", prompt)
        self.assertIn("datasets_and_tools", prompt)


class ResearchServiceTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("OPENAI_API_KEY", None)

    def test_generate_report_contains_required_sections(self):
        report = ResearchService.generate_report("Computer Vision", "How can students improve defect detection?")
        for key in ResearchService.REQUIRED_KEYS:
            self.assertIn(key, report)

    def test_literature_review_has_three_sources(self):
        report = ResearchService.generate_report("NLP", "Topic")
        sources = [entry["source"] for entry in report["literature_review"]]
        self.assertEqual(sources, ["Google Scholar", "IEEE Xplore", "PubMed"])


if __name__ == "__main__":
    unittest.main()
