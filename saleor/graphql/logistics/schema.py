import graphene

from ..core.descriptions import ADDED_IN_324
from .mutations import ShipmentCreate
from .types import Shipment


class LogisticsQueries(graphene.ObjectType):
    logistics_shipment = graphene.Field(
        Shipment,
        id=graphene.ID(required=True),
        description="Retrieves a logistics shipment by ID." + ADDED_IN_324,
    )

    @staticmethod
    def resolve_logistics_shipment(_root, info, id):
        return Shipment.get_node_from_global_id(info, id)


class LogisticsMutations(graphene.ObjectType):
    logistics_shipment_create = ShipmentCreate.Field()
