from ovos_solver_openai_persona.engines import OpenAIChatCompletionsSolver


class OpenAIPersonaSolver(OpenAIChatCompletionsSolver):
    """default "Persona" engine"""

    def __init__(self, config=None):
        # defaults to gpt-3.5-turbo
        super().__init__(name="OpenAI ChatGPT Persona", config=config)
        self.default_persona = config.get("persona") or "helpful, creative, clever, and very friendly."

    def get_chat_history(self, persona=None):
        qa = self.qa_pairs[-1 * self.max_utts:]
        persona = persona or self.default_persona
        initial_prompt = f"You are a helpful assistant. " \
                         f"You give short and factual answers. " \
                         f"You are {persona}"
        messages = [
            {"role": "system", "content": initial_prompt},
        ]
        for q, a in qa:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})
        return messages

    # officially exported Solver methods
    def get_spoken_answer(self, query, context=None):
        context = context or {}
        persona = context.get("persona") or self.default_persona
        messages = self.get_prompt(query, persona)
        response = self._do_api_request(messages)
        answer = response.strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            self.qa_pairs.append((query, answer))
        return answer


if __name__ == "__main__":
    bot = OpenAIPersonaSolver({"key": "sk-xxxx"})
    print(bot.get_spoken_answer("describe quantum mechanics in simple terms"))
    # Quantum mechanics is a branch of physics that deals with the behavior of particles on a very small scale, such as atoms and subatomic particles. It explores the idea that particles can exist in multiple states at once and that their behavior is not predictable in the traditional sense.
    print(bot.spoken_answer("Quem encontrou o caminho maritimo para o Brazil", {"lang": "pt-pt"}))
    # Explorador português Pedro Álvares Cabral é creditado com a descoberta do Brasil em 1500
