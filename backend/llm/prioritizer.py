import logging 

logger = logging.getLogger(__name__)

import json
import os
import numpy as np
from openai import AzureOpenAI
from backend.schema.event import Event

class Prioritizer():

    SYSTEM_MESSAGE = {
        "role": "system",
        "content": """\
You are a highly skilled Traffic Analyst specializing in determining the severity of a traffic event. You will be given details about a traffic event, and your task is to evaluate its severity across five different metrics. For each metric, assign a score from 1 to 5, where:

- 1 indicates the least severity or impact.
- 5 indicates the highest severity or impact.

Here are the five metrics you will need to assess:

1. **Impact on Traffic Flow** – Evaluate how much this event disrupts the normal flow of traffic in the affected area.
   - 1: No significant impact.
   - 5: Complete gridlock or severe delays.

2. **Location of the Event** – Consider whether the event occurred in a high-traffic area or a busy intersection.
   - 1: Low-traffic area.
   - 5: Major intersection or highway.

3. **Cause of the Event** – Evaluate the seriousness of the event's cause (e.g., accident, mechanical failure, weather conditions).
   - 1: Minor incident (e.g., stalled car).
   - 5: Major accident or extreme weather event.

4. **Injuries or Fatalities** – Assess whether any injuries or fatalities occurred during the event.
   - 1: No injuries or fatalities.
   - 5: Multiple fatalities or severe injuries.

5. **Duration of the Event** – Evaluate how long the event has been ongoing or how long it is expected to continue.
   - 1: Event is short-lived, expected to clear quickly.
   - 5: Event is prolonged or ongoing for hours.

### Output Format:
Respond in JSON format, as shown below:

```json
{
    "metrics": {
        "impact_on_traffic_flow": 1 to 5,
        "location_of_event": 1 to 5,
        "cause_of_event": 1 to 5,
        "injuries_or_fatalities": 1 to 5,
        "duration_of_event": 1 to 5 
    },
    "explantion": Concise reasoning for scores given. (max 200 words)
}
"""
    }

    def __init__(self, model: AzureOpenAI):
        self.model = model

    def __user_message_builder(self, event: Event):
        prompt = f"""\
Here is an event: 

{event}

Please score this event accordingly.\
"""
        return {"role":"user", "content": prompt}
    
    def __compute_serverity(self, metrics):
        logger.info("Priority LLM: Computing Serverity")
        WEIGHTS = {
            "impact_on_traffic_flow": 0.2,
            "location_of_event": 0.2,
            "cause_of_event": 0.2,
            "injuries_or_fatalities": 0.2,
            "duration_of_event": 0.2 
        }

        weights = list(WEIGHTS.values())
        scores = metrics.values()
        normalized_scores = [(score - 1) / 4 for score in scores]
        return np.dot(normalized_scores, weights).item()


    def prioritize(self, event: Event):
        logging.info("Priority LLM: Prioritizing...")
        user_message = self.__user_message_builder(event)
        messages = [self.SYSTEM_MESSAGE, user_message]
        response = self.model.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT"),
            messages=messages,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        try:
            content = json.loads(content)
            metrics = content.get('metrics')
            explanation = content.get('explanation')
            score = self.__compute_serverity(metrics)
            return score, explanation
        except json.JSONDecodeError as e:
            logger.warning("Priority LLM: Unable to get JSON, retrying...")
            return self.prioritize(event)
        
        
if __name__ == "__main__":
    from backend.llm.model import client
    p = Prioritizer(client)




