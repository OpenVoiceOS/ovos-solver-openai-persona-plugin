import os
import random
from datetime import date
from neon_solvers import AbstractSolver
from os import listdir, remove as remove_file
from os.path import dirname, isfile
from os.path import join, dirname
from ovos_utils.log import LOG
import openai as ai


class ChatGPTSolver(AbstractSolver):
    def __init__(self):
        super().__init__(name="ChatGPT", priority=25, enable_cache=False, enable_tx=False)
        # this is a leaked gpt model that is free to use, unmoderated free and slow
        self.engine = "text-chat-davinci-002-20221122"  # "ada" cheaper and faster, "davinci" better
        self.stop_token = "<|im_end|>"
        self.key = self.config.get("key")
        ai.api_key = self.key
        self.chatgpt = ai.Completion()
        self.memory = True  # todo config
        self.max_utts = 15  # memory size TODO config
        self.qa_pairs = []  # tuple of q+a
        self.current_q = None
        self.current_a = None

    @property
    def initial_prompt(self):
        start_chat_log = """The assistant is helpful, creative, clever, and very friendly."""
        s = self.config.get("initial_prompt", start_chat_log)
        return f"The following is a conversation with an AI assistant. The assistant understands all languages. The assistant gives short and factual answers. {s}"

    @property
    def chat_history(self):
        # TODO - intro question from skill settings
        intro_q = ("Hello, who are you?", "I am an AI created by OpenAI. How can I help you today?")
        if len(self.qa_pairs) > self.max_utts:
            qa = [intro_q] + self.qa_pairs[-1*self.max_utts:]
        else:
            qa = [intro_q] + self.qa_pairs
        chat = self.initial_prompt.strip() + "\n\n"
        if qa:
            qa = "\n".join([f"Human: {q}\nAI: {a}" for q, a in qa])
            if chat.endswith("\nHuman: "):
                chat = chat[-1*len("\nHuman: "):]
            if chat.endswith("\nAI: "):
                chat += f"Please rephrase the question\n"
            chat += qa
        return chat

    def get_prompt(self, utt):
        self.current_q = None
        self.current_a = None
        prompt = self.chat_history
        if not prompt.endswith("\nHuman: "):
            prompt += f"\nHuman: {utt}?\nAI: "
        else:
            prompt += f"{utt}?\nAI: "
        return prompt

    # officially exported Solver methods
    def get_spoken_answer(self, query, context=None):
        prompt = self.get_prompt(query)
        # TODO - params from config
        response = self.chatgpt.create(prompt=prompt, engine=self.engine, temperature=0.85,
                                       top_p=1, frequency_penalty=0,
                                       presence_penalty=0.7, best_of=2, max_tokens=300,
                                       stop=self.stop_token)
        answer = response.choices[0].text.split("Human: ")[0].split("AI: ")[0].strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            self.qa_pairs.append((query, answer))
        return answer


if __name__ == "__main__":
    bot = ChatGPTSolver()
    print(bot.get_spoken_answer("describe quantum mechanics in simple terms"))
    # Quantum mechanics is a branch of physics that deals with the behavior of particles on a very small scale, such as atoms and subatomic particles. It explores the idea that particles can exist in multiple states at once and that their behavior is not predictable in the traditional sense.
    print(bot.spoken_answer("Quem encontrou o caminho maritimo para o Brazil", {"lang": "pt-pt"}))
    # Explorador português Pedro Álvares Cabral é creditado com a descoberta do Brasil em 1500