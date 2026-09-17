from resq_shared.bus import EventBus

from .config import settings

bus = EventBus(settings.redis_url)
