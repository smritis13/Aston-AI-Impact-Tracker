# file: myapp/title_generator.py

import openai
from django.conf import settings
from chat.models import Conversation

class ConversationTitleGenerator:
    """
    A separate class that, given a Conversation,
    produces a short descriptive title using OpenAI.
    """

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def generate_title(self, conversation: Conversation) -> str:
        """
        Calls OpenAI to produce a short, descriptive conversation title
        based on the conversation's messages so far.
        """

        # Gather all messages in chronological order
        messages_qs = conversation.messages.order_by("timestamp")
        # Build a text snippet with user/system content
        conversation_text = "\n".join(f"{m.sender}: {m.text}" for m in messages_qs)

        # We can use a ChatCompletion with gpt-5.2, or a Completion with text-davinci-003
        # Example using ChatCompletion:
        chat_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a conversation summarizer. Given the conversation below, "
                    "create a concise, descriptive title (a short phrase)."
                ),
            },
            {
                "role": "user",
                "content": conversation_text,
            },
        ]

        response = openai.chat.completions.create(
            model="gpt-5.4-mini",
            messages=chat_prompt,
            max_tokens=100,
            temperature=0.7
        )

        # Extract the text
        # generated_title = response.choices[0].message["content"].strip()
        generated_title = response.choices[0].message.content.strip()

        # Optionally truncate to fit the database field
        return generated_title[:200]
