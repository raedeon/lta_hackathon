import logging

logger = logging.getLogger(__name__)

import threading
from flask import Response, request, jsonify
from backend.schema.event import Event
from backend.server.manager.crowdsource_manager import CrowdsourceManager
from backend.server.manager.verified_manager import VerifiedManager
from backend.server.manager.filtered_manager import FilteredManager

MANAGERS = {
    "crowdsource": CrowdsourceManager(),
    "filtered": FilteredManager(),
    "verified": VerifiedManager() 
}

lock = threading.Lock()

def get_manager(storage_type):
    if storage_type not in MANAGERS:
        return None
    return MANAGERS[storage_type]

def create_event_from_crowdsource():
    logger.info("Flask: POST /event/crowdsource Invoked")

    manager: CrowdsourceManager = MANAGERS['crowdsource']
    data = request.get_json()
    pending_event_id = manager.get_next_event_id()

    def background_task():
        with lock:
            manager.add(**data)

    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    return jsonify({"event_id": pending_event_id}), 202

def check_event_from_crowdsource_created(event_id):
    logger.info(f"Flask: GET /event/crowdsource/{event_id}/created Invoked")

    manager: CrowdsourceManager = MANAGERS['crowdsource']
    is_created = manager.check_event_created(event_id)
    if not is_created:
        return jsonify({"event_id": event_id}), 202
    return jsonify({"event_id": event_id}), 201

def add_verified_event():
    logger.info("Flask: POST /events/verified Invoked")
    manager: VerifiedManager = MANAGERS['verified']
    data = request.get_json()
    verified_event = Event.from_dict(data)

    event = manager.add_verified_event(verified_event)
    return event

def get_all_events(storage_type):
    logger.info(f"Flask: GET /events/{storage_type} Invoked")
    manager = get_manager(storage_type)
    if not manager:
        return jsonify({'message': f'Event Storage {storage_type} not found!'}), 400
    events = manager.get_all()
    return jsonify([event.to_dict() for event in events]), 200
    
def get_one_event(storage_type, event_id):
    logger.info(f"Flask: GET /events/{storage_type}/{event_id} Invoked")
    manager = get_manager(storage_type)
    if not manager:
        return jsonify({'message': f'Event Storage {storage_type} not found!'}), 400
    event = manager.get_one(event_id)
    if not event:
        return jsonify({'message': 'Event not found'}), 404
    return jsonify(event.to_dict()), 200

def stream_crowdsource():
    manager = MANAGERS["crowdsource"]
    def event_stream():
        while True:
            with lock:
                if manager.queue:
                    event_id = manager.queue.pop(0)
                    yield f"data: {event_id}\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

def stream_filtered():
    manager = MANAGERS["filtered"]
    def event_stream():
        while True:
            with lock:
                if manager.queue:
                    event_id = manager.queue.pop(0)
                    yield f"data: {event_id}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")
