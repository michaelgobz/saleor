import graphene

from ...permission.enums import OrderPermissions
from ..core.descriptions import ADDED_IN_324
from ..core.fields import PermissionsField
from .mutations import ShipmentCreate, ShipmentLocationUpdate
from .types import DeliveryLocation, Shipment


class LogisticsQueries(graphene.ObjectType):
    logistics_shipment = PermissionsField(
        Shipment,
        id=graphene.ID(required=True),
        description="Retrieves a logistics shipment by ID." + ADDED_IN_324,
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    logistics_shipment_locations = PermissionsField(
        graphene.List(DeliveryLocation),
        shipment_id=graphene.ID(required=True),
        limit=graphene.Int(
            required=False,
            description=(
                "Maximum number of GPS samples to return, up to 100."
                + ADDED_IN_324
            ),
        ),
        description=(
            "Returns GPS samples for drawing a shipment route on a map."
            + ADDED_IN_324
        ),
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )

    @staticmethod
    def resolve_logistics_shipment(_root, info, id):
        return Shipment.get_node_from_global_id(info, id)

    @staticmethod
    def resolve_logistics_shipment_locations(_root, info, shipment_id, limit=100):
        shipment = Shipment.get_node_from_global_id(info, shipment_id)
        return shipment.locations.all()[: min(limit or 100, 100)]


class LogisticsMutations(graphene.ObjectType):
    logistics_shipment_create = ShipmentCreate.Field()
    logistics_shipment_location_update = ShipmentLocationUpdate.Field()
