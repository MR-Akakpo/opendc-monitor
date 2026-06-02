from fastapi import APIRouter, Query
from app.services.file_reader import read_yaml, read_json, read_jsonl

router = APIRouter()

@router.get('/health')
def health():
    return {
        'status': 'OK',
        'service': 'OpenDC Monitor API',
        'organization': 'STELLARIX'
    }

@router.get('/inventory')
def inventory():
    return read_yaml('datacenter/inventory/datacenter_inventory.yaml')

@router.get('/topics')
def topics():
    return read_yaml('configs/mqtt_topics.yaml')

@router.get('/modules')
def modules():
    return read_yaml('configs/modules.yaml')

@router.get('/thresholds')
def thresholds():
    return read_yaml('configs/thresholds.yaml')

@router.get('/topology')
def topology():
    return read_yaml('configs/site_topology.yaml')

@router.get('/alarms/active')
def active_alarms():
    return read_json('monitoring/alarms/active_alarms.json')

@router.get('/events')
def events(limit: int = Query(default=100, ge=1, le=1000)):
    return {
        'limit': limit,
        'events': read_jsonl('monitoring/events/events.jsonl', limit)
    }

@router.get('/statistics')
def statistics():
    return read_json('monitoring/historian/daily_statistics.json')
