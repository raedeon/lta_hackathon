import logging

logger = logging.getLogger(__name__)

from backend.schema.event_storage import EventStorage

from backend.llm.model import FILTERER, PRIORITIZER

class FilteredManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "storage"):
            from backend.server.manager.crowdsource_manager import CrowdsourceManager
            logger.info("Filtered Storage: Storage Initialised")
            self.storage = EventStorage()
            self.queue = []
            self.crowdsource_manager = CrowdsourceManager()
    
    def notify(self, crowdsource_manager_event_id):
        logger.info("Filtered Storage: Got Notified of New Crowdsource Event")
        event_from_crowdsource = self.crowdsource_manager.get_one(crowdsource_manager_event_id)
        is_new_event, unique_event_id = self.__filter_event(event_from_crowdsource)
        if is_new_event:
            return self.__create_filtered_event(event_from_crowdsource) 
        else:
            logger.info("Filtered Storage: Add repeated event")
            not_filtered_event = self.__add_repeated_event(unique_event_id, event_from_crowdsource)
            return not_filtered_event

    def get_all(self):
        logger.info("Filtered Storage: Listing all Events")
        return self.storage.list_events()

    def get_one(self, event_id):
        logger.info("Filtered Storage: Listing one event")
        return self.storage.read(event_id)
    
    def delete(self, event_id):
        logger.info("Filtered Storage: Deleting one event")
        return self.storage.delete(event_id)
    
    def __create_filtered_event(self, event_from_crowdsource):
        logger.info("Filtered Storage: Adding unique event")
        crowdsource_event = event_from_crowdsource.crowdsource_event
        image_event = event_from_crowdsource.image_event
        speed_events = event_from_crowdsource.speed_events
        priority_score = self.__calculate_priority_score(event_from_crowdsource)
        filtered_event = self.storage.create(
            crowdsource_event,
            image_event,
            speed_events,
            True,
            priority_score
        )
        self.queue.append(filtered_event.id)
        return filtered_event
    
    def __filter_event(self, new_crowdsource_event):
        logger.info("Filtered Storage: Check Event is unique")
        unique_events = self.get_all()
        for unique_event in unique_events:
            is_repeated, explanation = FILTERER.filter(new_crowdsource_event, unique_event)
            if is_repeated:
                logger.info("Filtered Storage: Duplicated Event Found")
                logger.info(f"FILTERER Explanation: {explanation}")
                return False, unique_event.id 
        logger.info("Filtered Storage: Unique Event Found")
        return True, -1
    
    def __add_repeated_event(self, unique_event_id, repeated_event):
        logger.info("Filtered Storage: Aggregating newly identified repeated event into existing event")
        event = self.storage.update(unique_event_id, repeated_event.id)
        self.queue.append(event.id)
        return event

    def __calculate_priority_score(self, event):
        logger.info("Filtered Storage: Calculating Priority Score")
        score, explanation = PRIORITIZER.prioritize(event)
        logger.info(f"PRIORITIZER Explanation: {explanation}")
        return score
