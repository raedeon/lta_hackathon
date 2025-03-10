from flask import request, jsonify
from backend.schema.event_storage import EventStorage

crowdsource_event_storage = EventStorage()
filtered_event_storage = EventStorage()
verified_event_storage = EventStorage()

event_storages = {
    "crowdsource": crowdsource_event_storage,
    "filtered": filtered_event_storage,
    "verified": verified_event_storage
}

def create_event(storage_type):
    """Create a new event."""
    if storage_type not in event_storages:
        return jsonify({'message': f'Event Storage {storage_type} not found!'}), 400
    storage = event_storages[storage_type]
    data = request.get_json()

    event = storage.create(**data)
    return jsonify(event.to_dict()), 201


def get_event(storage_type, event_id):
    """Get an event by ID."""
    if storage_type not in event_storages:
        return jsonify({'message': f'Event Storage {storage_type} not found!'}), 400
    storage = event_storages[storage_type]
    event = storage.read(event_id)
    if event:
        return jsonify(event.to_dict()), 200
    return jsonify({'message': 'Event not found'}), 404


def update_event(storage_type, event_id):
    """Update an event by ID."""
    if storage_type not in event_storages:
        return jsonify({'message': f'Event Storage {storage_type} not found!'}), 400
    storage = event_storages[storage_type]
    data = request.get_json()

    updated_event = storage.update(
        event_id,
        **data
    )
    if updated_event:
        return jsonify(updated_event.to_dict()), 200
    return jsonify({'message': 'Event not found'}), 404


def delete_event(storage_type, event_id):
    """Delete an event by ID."""
    if storage_type not in event_storages:
        return jsonify({'message': f'Event Storage {storage_type} not found!'}), 400
    storage = event_storages[storage_type]
    deleted_event = storage.delete(event_id)
    if deleted_event:
        return jsonify({'message': 'Event deleted'}), 200
    return jsonify({'message': 'Event not found'}), 404


def list_events(storage_type):
    """List all events."""
    if storage_type not in event_storages:
        return jsonify({'message': f'Event Storage {storage_type} not found!'}), 400
    storage = event_storages[storage_type]
    events = storage.list_events()
    return jsonify([event.to_dict() for event in events]), 200