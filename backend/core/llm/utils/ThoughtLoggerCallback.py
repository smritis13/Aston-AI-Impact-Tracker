from langchain.callbacks.base import BaseCallbackHandler

class ThoughtLoggerCallback(BaseCallbackHandler):
    def __init__(self):
        self.thoughts = []

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.thoughts.append(f"🤔 LLM is starting with prompt:\n{prompts[0]}") #🤔

    def on_llm_end(self, response, **kwargs):
        self.thoughts.append(f"✅ LLM responded:\n{response.generations[0][0].text}") #✅

    def get_thoughts(self):
        return self.thoughts
