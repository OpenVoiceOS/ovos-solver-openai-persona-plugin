import json

import requests
from neon_solvers import AbstractSolver


class OpenAICompletionsSolver(AbstractSolver):
    api_url = "https://api.openai.com/v1/completions"

    def __init__(self, config=None, name="OpenAI"):
        super().__init__(name=name, priority=25, config=config,
                         enable_cache=False, enable_tx=False)
        self.engine = self.config.get("model", "davinci")  # "ada" cheaper and faster, "davinci" better
        self.stop_token = "<|im_end|>"
        self.key = self.config.get("key")  # TODO - raise error if missing
        self.memory = True  # todo config
        self.max_utts = 15  # memory size TODO config
        self.qa_pairs = []  # tuple of q+a
        self.current_q = None
        self.current_a = None

    def get_chat_history(self, persona=None):
        # TODO - intro question from skill settings
        intro_q = ("Hello, who are you?", "I am an AI created by OpenAI. How can I help you today?")
        if len(self.qa_pairs) > self.max_utts:
            qa = [intro_q] + self.qa_pairs[-1 * self.max_utts:]
        else:
            qa = [intro_q] + self.qa_pairs

        persona = persona or self.config.get("persona") or "helpful, creative, clever, and very friendly."
        initial_prompt = f"The following is a conversation with an AI assistant. " \
                         f"The assistant understands all languages. " \
                         f"The assistant gives short and factual answers. " \
                         f"The assistant answers in the same language the question was asked. " \
                         f"The assistant is {persona}"
        chat = initial_prompt.strip() + "\n\n"
        if qa:
            qa = "\n".join([f"Human: {q}\nAI: {a}" for q, a in qa])
            if chat.endswith("\nHuman: "):
                chat = chat[-1 * len("\nHuman: "):]
            if chat.endswith("\nAI: "):
                chat += f"Please rephrase the question\n"
            chat += qa
        return chat

    def get_prompt(self, utt, persona=None):
        self.current_q = None
        self.current_a = None
        prompt = self.get_chat_history(persona)
        if not prompt.endswith("\nHuman: "):
            prompt += f"\nHuman: {utt}?\nAI: "
        else:
            prompt += f"{utt}?\nAI: "
        return prompt

    # officially exported Solver methods
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
        print(response)
        return response["choices"][0]["text"]

    def get_spoken_answer(self, query, context=None):
        context = context or {}
        persona = context.get("persona")
        prompt = self.get_prompt(query, persona)
        response = self._do_api_request(prompt)
        answer = response.split("Human: ")[0].split("AI: ")[0].strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            self.qa_pairs.append((query, answer))
        return answer


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


if __name__ == "__main__":
    bot = OpenAICompletionsSolver({"key": "sk-xxxx"})
    print(bot.get_spoken_answer("describe quantum mechanics in simple terms"))
    # Quantum mechanics is a branch of physics that deals with the behavior of particles on a very small scale, such as atoms and subatomic particles. It explores the idea that particles can exist in multiple states at once and that their behavior is not predictable in the traditional sense.
    print(bot.spoken_answer("Quem encontrou o caminho maritimo para o Brazil", {"lang": "pt-pt"}))
    # Explorador português Pedro Álvares Cabral é creditado com a descoberta do Brasil em 1500
