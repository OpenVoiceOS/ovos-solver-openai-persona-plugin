from ovos_solver_openai_persona.engines import OpenAICompletionsSolver


# Voice Assistant Promp Engineering
class OpenAIPersonaPromptSolver(OpenAICompletionsSolver):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = "text-davinci-03"
        super().__init__(name="OpenAI Persona", config=config)
        self.memory = config.get("enable_memory", True)
        self.max_utts = config.get("memory_size", 15)
        self.qa_pairs = []  # tuple of q+a
        self.current_q = None
        self.current_a = None
        self.default_persona = config.get("persona") or "helpful, creative, clever, and very friendly."

    def get_chat_history(self, persona=None):
        # TODO - intro question from skill settings
        intro_q = ("Hello, who are you?", "I am an AI created by OpenAI. How can I help you today?")
        if len(self.qa_pairs) > self.max_utts:
            qa = [intro_q] + self.qa_pairs[-1 * self.max_utts:]
        else:
            qa = [intro_q] + self.qa_pairs

        persona = persona or self.config.get("persona") or self.default_persona
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
    def get_spoken_answer(self, query, context=None):
        context = context or {}
        persona = context.get("persona") or self.default_persona
        prompt = self.get_prompt(query, persona)
        response = self._do_api_request(prompt)
        answer = response.split("Human: ")[0].split("AI: ")[0].strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            self.qa_pairs.append((query, answer))
        return answer

