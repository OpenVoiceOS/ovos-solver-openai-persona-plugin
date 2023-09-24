import json

import requests
from ovos_plugin_manager.templates.solvers import AbstractSolver
from ovos_utils.log import LOG


class OpenAICompletionsSolver(AbstractSolver):

    def __init__(self, config=None, name="OpenAI"):
        super().__init__(name=name, priority=25, config=config,
                         enable_cache=False, enable_tx=False)
        self.api_url = f"{self.config.get('api_url', 'https://api.openai.com/v1')}/completions"
        self.engine = self.config.get("model", "text-davinci-002")  # "ada" cheaper and faster, "davinci" better
        self.stop_token = "<|im_end|>"
        if not key:
            LOG.error("key not set in config")
            raise ValueError("key must be set")
        else:
            self.key = key

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
    def get_spoken_answer(self, query, context=None):
        response = self._do_api_request(query)
        answer = response.strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        return answer


class OpenAIChatCompletionsSolver(AbstractSolver):

    def __init__(self, config=None, name="OpenAI Chat"):
        super().__init__(name=name, priority=25, config=config,
                         enable_cache=False, enable_tx=False)
        self.api_url = f"{self.config.get('api_url', 'https://api.openai.com/v1')}/chat/completions"
        self.engine = self.config.get("model", "gpt-3.5-turbo")  # "ada" cheaper and faster, "davinci" better
        self.stop_token = "<|im_end|>"
        key = self.config.get("key")
        if not key:
            LOG.error("key not set in config")
            raise ValueError("key must be set")
        else:
            self.key = key
        self.memory = config.get("enable_memory", True)
        self.max_utts = config.get("memory_size", 15)
        self.qa_pairs = []  # tuple of q+a
        self.current_q = None
        self.current_a = None
        self.initial_prompt = config.get("initial_prompt", "You are a helpful assistant.")

    # OpenAI API integration
    def _do_api_request(self, messages):
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
        response = requests.post(self.api_url, headers=headers, data=json.dumps(payload)).json()
        return response["choices"][0]["message"]["content"]

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
        self.current_q = None
        self.current_a = None
        messages = self.get_chat_history(initial_prompt)
        messages.append({"role": "user", "content": utt})
        return messages

    # officially exported Solver methods
    def get_spoken_answer(self, query, context=None):
        messages = self.get_prompt(query)
        response = self._do_api_request(messages)
        answer = response.strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            self.qa_pairs.append((query, answer))
        return answer


# Base models
class GPT35Turbo(OpenAIChatCompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "gpt-3.5-turbo"
        super().__init__(name="GPT 3.5 Turbo", config=config)


class AdaSolver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "ada"
        super().__init__(name="Ada", config=config)


class BabbageSolver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "babbage"
        super().__init__(name="Babbage", config=config)


class CurieSolver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "curie"
        super().__init__(name="Curie", config=config)


class DavinciSolver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "davinci"
        super().__init__(name="Davinci", config=config)


class Davinci2Solver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "text-davinci-02"
        super().__init__(name="Davinci 2", config=config)


class Davinci3Solver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "text-davinci-03"
        super().__init__(name="Davinci 3", config=config)


# Code completion
class DavinciCodeSolver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "code-davinci-002"
        super().__init__(name="Code Davinci", config=config)


class CushmanCodeSolver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "code-cushman-001"
        super().__init__(name="Code Cushman", config=config)

