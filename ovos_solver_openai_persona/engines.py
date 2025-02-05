import json
from typing import Optional, Iterable, List, Dict

import requests
from ovos_plugin_manager.templates.solvers import QuestionSolver
from ovos_utils.log import LOG

from ovos_plugin_manager.templates.solvers import ChatMessageSolver

MessageList = List[Dict[str, str]]  # for typing

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


def post_process_sentence(text: str) -> str:
    text = text.replace("*", "")  # TTS often literally reads "asterisk"
    return text.strip()


class OpenAIChatCompletionsSolver(ChatMessageSolver):
    enable_tx = False
    priority = 25

    def __init__(self, config=None):
        super().__init__(config)
        self.api_url = f"{self.config.get('api_url', 'https://api.openai.com/v1')}/chat/completions"
        self.engine = self.config.get("model", "gpt-4o-mini")  # "ada" cheaper and faster, "davinci" better
        self.stop_token = "<|im_end|>"
        self.key = self.config.get("key")
        if not self.key:
            LOG.error("key not set in config")
            raise ValueError("key must be set")
        self.memory = config.get("enable_memory", True)
        self.max_utts = config.get("memory_size", 15)
        self.qa_pairs = []  # tuple of q+a
        self.system_prompt = config.get("system_prompt", "You are a helpful assistant.")

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
                if "error" in chunk and "message" in chunk["error"]:
                    LOG.error("API returned an error: " + chunk["error"]["message"])
                    break
                if chunk["choices"][0].get("finish_reason"):
                    break
                if "content" not in chunk["choices"][0]["delta"]:
                    continue
                yield chunk["choices"][0]["delta"]["content"]

    def get_chat_history(self, system_prompt=None):
        qa = self.qa_pairs[-1 * self.max_utts:]
        system_prompt = system_prompt or self.system_prompt or "You are a helpful assistant."
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        for q, a in qa:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})
        return messages

    def get_messages(self, utt, system_prompt=None) -> MessageList:
        messages = self.get_chat_history(system_prompt)
        messages.append({"role": "user", "content": utt})
        return messages

    # asbtract Solver methods
    def continue_chat(self, messages: MessageList,
                      lang: Optional[str],
                      units: Optional[str] = None) -> Optional[str]:
        """Generate a response based on the chat history.

        Args:
            messages (List[Dict[str, str]]): List of chat messages, each containing 'role' and 'content'.
            lang (Optional[str]): The language code for the response. If None, will be auto-detected.
            units (Optional[str]): Optional unit system for numerical values.

        Returns:
            Optional[str]: The generated response or None if no response could be generated.
        """
        messages = [{"role": "system", "content": self.system_prompt }] + messages
        response = self._do_api_request(messages)
        answer = post_process_sentence(response)
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            query = messages[-1]["content"]
            self.qa_pairs.append((query, answer))
        return answer

    def stream_chat_utterances(self, messages: List[Dict[str, str]],
                               lang: Optional[str] = None,
                               units: Optional[str] = None) -> Iterable[str]:
        """
        Stream utterances for the given chat history as they become available.

        Args:
            messages: The chat messages.
            lang (Optional[str]): Optional language code. Defaults to None.
            units (Optional[str]): Optional units for the query. Defaults to None.

        Returns:
            Iterable[str]: An iterable of utterances.
        """
        messages = [{"role": "system", "content": self.system_prompt }] + messages
        answer = ""
        query = messages[-1]["content"]
        if self.memory:
            self.qa_pairs.append((query, answer))

        for chunk in self._do_streaming_api_request(messages):
            answer += chunk
            if any(chunk.endswith(p) for p in [".", "!", "?", "\n", ":"]):
                if len(chunk) >= 2 and chunk[-2].isdigit() and chunk[-1] == ".":
                    continue  # dont split numbers
                if answer.strip():
                    if self.memory:
                        full_ans = f"{self.qa_pairs[-1][-1]}\n{answer}".strip()
                        self.qa_pairs[-1] = (query, full_ans)
                    yield post_process_sentence(answer)
                answer = ""

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
        messages = self.get_messages(query)
        yield from self.stream_chat_utterances(messages, lang, units)

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
        messages = self.get_messages(query)
        # just for api compat since it's a subclass, shouldn't be directly used
        return self.continue_chat(messages=messages, lang=lang, units=units)
