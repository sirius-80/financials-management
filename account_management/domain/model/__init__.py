class Entity:
    def __init__(self, entity_id):
        self.id = entity_id
        self._domain_events = []

    def register_domain_event(self, event):
        self._domain_events.append(event)

    def flush_domain_events(self):
        """Returns the list of domain events and clears the list of registered events on this Aggregate Root.
        This method is typically called by the infrastructure, which is responsible for actually publishing
        the registered events.

        See 2-step domain-event publishing:
        https://paucls.wordpress.com/2018/05/31/ddd-aggregate-roots-and-domain-events-publication/
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self):
        return hash(self.id)


class DomainEvent:
    pass
