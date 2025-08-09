import logging 

logger = logging.getLogger(__name__)

import json
import os
from openai import AzureOpenAI
from backend.schema.event import Event

class CrowdsourceFilter():

    SYSTEM_MESSAGE = {
        "role": "system",
        "content" : """\
        You are a higly skilled Traffic Analyst specializing in identifying and verifying traffic events. You are given two data points:

        1. Crowdsource Data - A newly reported traffic incident from the public
        2. Confirmed Event - A previously verified traffic incident

        Your task is to analyze these points and determine whether the crowdsource data represents a new event or a repeated event based on factors such as location, time, serverity and description.

        Respond in JSON format as follow:

        {
            "is_repeated": true | false,
            "explanation": "Concise reasoning for the classification (max 150 words)."
        }

        Your explanation should be clear and based on logical comparisons derived from the data points. Be precise and AVOID unnecessary elaboration.

        """
    }

    def __init__(self, model:AzureOpenAI):
        self.model = model

    def __user_message_builder(self, new_event: Event, verified_event: Event):
        prompt = f"""\
Below is the information of the new event from the crowdsource data:

{new_event}

Below is the information of a verified event:

{verified_event}

Are these events similar to each other?
"""
        return {"role": "user", "content": prompt} 

    def filter(self, new_event: Event, verified_event: Event):
        logger.info("Filter LLM: Filtering...")
        user_message = self.__user_message_builder(new_event, verified_event)
        messages = [self.SYSTEM_MESSAGE, user_message]
        response = self.model.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT"),
            messages=messages,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        try:
            content = json.loads(content)
            return content.get("is_repeated"), content.get("explanation")
        except json.JSONDecodeError as e:
            logger.warning("Filter LLM: Unable to get JSON, retrying...")
            return self.filter(new_event, verified_event)

if __name__ == "__main__":
    from backend.llm.model import client
    f = CrowdsourceFilter(client)

    data = {
      "alert_subtype": None,
      "alert_type": "ACCIDENT",
      "reliability": 6,
      "street": "Tampines Ave 10",
      "timestamp": 1741882880.8779533,
      "town": "Tampines",
      "x": 103.926906,
      "y": 1.351775
    }

    from backend.schema.crowdsource_event import CrowdsourceEvent
    cs_event = CrowdsourceEvent.from_dict(data)

    new_event = Event(2, cs_event)
    similar_event = Event(1, cs_event, is_unique=True, priority_score=0.4)

    is_repeated, explantion = f.filter(new_event, similar_event)
    print(f"Repeated: {is_repeated}\nExplantion:{explantion}")

    # new_event = Event.create("2024-10-21 16:01:00", "Tampines", "Tampines Ave 10", 2, 28.21, "to TPE(SLE)")
    # similar_event = Event.create("2024-10-21 15:51:00", "Tampines", "Tampines Ave 10", 2, 25.58, "to TPE(SLE)")
    # from datetime import datetime
    # different_event = Event.create(datetime.now(), "Tampines", "Tampines Ave 10", 1, 65.28, None)

    # ### new and similar event
    # status, explantion = f.filter(new_event, similar_event)
    # print(f"Status: {status}\nExplantion:{explantion}")

    # ### different event
    # status, explantion = f.filter(new_event, different_event)
    # print(f"Status: {status}\nExplantion:{explantion}")
    


