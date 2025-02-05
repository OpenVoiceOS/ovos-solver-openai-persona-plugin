from ovos_solver_openai_persona.engines import OpenAIChatCompletionsSolver
from ovos_plugin_manager.templates.solvers import TldrSolver
from ovos_plugin_manager.templates.language import LanguageTranslator, LanguageDetector
from typing import Dict, Optional


class OpenAISummarizer(TldrSolver):
    TEMPLATE = """Your task is to summarize the text into a suitable format.
Answer in plaintext with no formatting, 2 paragraphs long at most. 
Focus on the most important information.
---------------------
{content}
"""
    def __init__(self, config: Optional[Dict] = None,
                 translator: Optional[LanguageTranslator] = None,
                 detector: Optional[LanguageDetector] = None,
                 priority: int = 50,
                 enable_tx: bool = False,
                 enable_cache: bool = False,
                 internal_lang: Optional[str] = None):
        super().__init__(config=config, translator=translator,
                         detector=detector, priority=priority,
                         enable_tx=enable_tx, enable_cache=enable_cache,
                         internal_lang=internal_lang)
        self.llm = OpenAIChatCompletionsSolver(config=config, translator=translator,
                                               detector=detector, priority=priority,
                                               enable_tx=enable_tx, enable_cache=enable_cache,
                                               internal_lang=internal_lang)
        self.prompt_template = self.config.get("prompt_template") or self.TEMPLATE


    def get_tldr(self, document: str, lang: Optional[str] = None) -> str:
        """
        Summarize the provided document.

        :param document: The text of the document to summarize, assured to be in the default language.
        :param lang: Optional language code.
        :return: A summary of the provided document.
        """
        prompt = self.prompt_template.format(content=document)
        return self.llm.get_spoken_answer(prompt, lang)
