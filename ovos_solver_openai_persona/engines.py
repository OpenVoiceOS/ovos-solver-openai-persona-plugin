import json
from typing import Optional, Iterable

import requests
from ovos_plugin_manager.templates.solvers import QuestionSolver
from ovos_utils.log import LOG


class OpenAICompletionsSolver(QuestionSolver):
    enable_tx = False
    priority = 25

    def __init__(self, config=None):
        super().__init__(config)
        self.api_url = f"{self.config.get('api_url', 'https://api.openai.com/v1')}/completions"
        self.engine = self.config.get("model", "text-davinci-002")  # "ada" cheaper and faster, "davinci" better
        self.stop_token = "<|im_end|>"
        self.key = self.config.get("key")
        if not self.key:
            LOG.error("key not set in config")
            raise ValueError("key must be set")

    # OpenAI API integration
    def _do_api_request(self, prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.key
        }

        # TODO - params from config
        # https://platform.openai.com/docs/api-reference/completions/create
        payload = {
            "model": self.engine,
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 1,
            # between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
            "top_p": 1,
            # nucleus sampling alternative to temperature, the model considers the results of the tokens with top_p probability mass. 0.1 means only tokens comprising top 10% probability mass are considered.
            "n": 1,  # How many completions to generate for each prompt.
            "frequency_penalty": 0,
            # Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
            "presence_penalty": 0,
            # Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
            "stop": self.stop_token
        }
        response = requests.post(self.api_url, headers=headers, data=json.dumps(payload)).json()
        return response["choices"][0]["text"]

    # officially exported Solver methods
    def get_spoken_answer(self, query: str,
                          lang: Optional[str] = None,
                          units: Optional[str] = None) -> Optional[str]:
        """
        Obtain the spoken answer for a given query.

        Args:
            query (str): The query text.
            lang (Optional[str]): Optional language code. Defaults to None.
            units (Optional[str]): Optional units for the query. Defaults to None.

        Returns:
            str: The spoken answer as a text response.
        """
        response = self._do_api_request(query)
        answer = response.strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        return answer


class OpenAIChatCompletionsSolver(QuestionSolver):
    enable_tx = False
    priority = 25

    def __init__(self, config=None):
        super().__init__(config)
        self.api_url = f"{self.config.get('api_url', 'https://api.openai.com/v1')}/chat/completions"
        self.engine = self.config.get("model", "gpt-3.5-turbo")  # "ada" cheaper and faster, "davinci" better
        self.stop_token = "<|im_end|>"
        self.key = self.config.get("key")
        if not self.key:
            LOG.error("key not set in config")
            raise ValueError("key must be set")
        self.memory = config.get("enable_memory", True)
        self.max_utts = config.get("memory_size", 15)
        self.qa_pairs = []  # tuple of q+a
        self.initial_prompt = config.get("initial_prompt", "You are a helpful assistant.")

    # OpenAI API integration
    def _do_api_request(self, messages):
        s = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.key
        }

        # TODO - params from config
        # https://platform.openai.com/docs/api-reference/completions/create
        payload = {
            "model": self.engine,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 1,
            # between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
            "top_p": 1,
            # nucleus sampling alternative to temperature, the model considers the results of the tokens with top_p probability mass. 0.1 means only tokens comprising top 10% probability mass are considered.
            "n": 1,  # How many completions to generate for each prompt.
            "frequency_penalty": 0,
            # Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
            "presence_penalty": 0,
            # Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
            "stop": self.stop_token
        }
        response = s.post(self.api_url, headers=headers, data=json.dumps(payload)).json()
        return response["choices"][0]["message"]["content"]

    def _do_streaming_api_request(self, messages):

        s = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.key
        }

        # TODO - params from config
        # https://platform.openai.com/docs/api-reference/completions/create
        payload = {
            "model": self.engine,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 1,
            # between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
            "top_p": 1,
            # nucleus sampling alternative to temperature, the model considers the results of the tokens with top_p probability mass. 0.1 means only tokens comprising top 10% probability mass are considered.
            "n": 1,  # How many completions to generate for each prompt.
            "frequency_penalty": 0,
            # Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
            "presence_penalty": 0,
            # Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
            "stop": self.stop_token,
            "stream": True
        }
        for chunk in s.post(self.api_url, headers=headers,
                            stream=True, data=json.dumps(payload)).iter_lines():
            if chunk:
                chunk = chunk.decode("utf-8")
                chunk = json.loads(chunk.split("data: ", 1)[-1])
                if chunk["choices"][0].get("finish_reason"):
                    break
                if "content" not in chunk["choices"][0]["delta"]:
                    continue
                yield chunk["choices"][0]["delta"]["content"]

    def get_chat_history(self, initial_prompt=None):
        qa = self.qa_pairs[-1 * self.max_utts:]
        initial_prompt = self.initial_prompt or "You are a helpful assistant."
        messages = [
            {"role": "system", "content": initial_prompt},
        ]
        for q, a in qa:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})
        return messages

    def get_prompt(self, utt, initial_prompt=None):
        messages = self.get_chat_history(initial_prompt)
        messages.append({"role": "user", "content": utt})
        return messages

    # asbtract Solver methods
    def stream_utterances(self, query: str,
                          lang: Optional[str] = None,
                          units: Optional[str] = None) -> Iterable[str]:
        """
        Stream utterances for the given query as they become available.

        Args:
            query (str): The query text.
            lang (Optional[str]): Optional language code. Defaults to None.
            units (Optional[str]): Optional units for the query. Defaults to None.

        Returns:
            Iterable[str]: An iterable of utterances.
        """
        messages = self.get_prompt(query)
        answer = ""
        for chunk in self._do_streaming_api_request(messages):
            answer += chunk
            if any(chunk.endswith(p) for p in [".", "!", "?", "\n", ":"]):
                if len(chunk) >= 2 and chunk[-2].isdigit() and chunk[-1] == ".":
                    continue  # dont split numbers
                if answer.strip():
                    yield answer
                answer = ""

    def get_spoken_answer(self, query: str,
                          lang: Optional[str] = None,
                          units: Optional[str] = None) -> Optional[str]:
        """
        Obtain the spoken answer for a given query.

        Args:
            query (str): The query text.
            lang (Optional[str]): Optional language code. Defaults to None.
            units (Optional[str]): Optional units for the query. Defaults to None.

        Returns:
            str: The spoken answer as a text response.
        """
        messages = self.get_prompt(query)
        response = self._do_api_request(messages)
        answer = response.strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            self.qa_pairs.append((query, answer))
        return answer
