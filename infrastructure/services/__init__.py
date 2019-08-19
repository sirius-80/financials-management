import logging

import pubsub.pub

logger = logging.getLogger(__name__)


def publish_domain_events(event_list):
    for event in event_list:
        topic = event.__class__.__name__
        pubsub.pub.sendMessage(topic, event=event)
