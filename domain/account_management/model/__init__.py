class Entity:
    """Superclass of all Entities (as in Domain Driven Design Entities). Entities may have domain events registered
    on them. These events need to be published by the infrastructure when the Entity is persisted (e.g. to the
    database)."""

    def __init__(self, entity_id):
        self.id = entity_id
        self._domain_events = []

    def register_domain_event(self, event):
        """Registers (adds) a new domain event on this entity. Domain events will be dispatched by the infrastructure
        when the entity is persisted.

        See 2-step account_management-event publishing:
        https://paucls.wordpress.com/2018/05/31/ddd-aggregate-roots-and-domain-events-publication/
        """
        self._domain_events.append(event)

    def flush_domain_events(self):
        """Returns the list of account_management events and clears the list of registered events on this Aggregate Root.
        This method is typically called by the infrastructure, which is responsible for actually publishing
        the registered events.

        See 2-step account_management-event publishing:
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
    """Common superclass for all domain events."""
    pass
