import graphene

from ...logistics.services import create_shipment
from ..core import ResolveInfo
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.mutations import BaseMutation
from ..order.types import Fulfillment
from .types import LogisticsShipmentCreateError, Shipment


class ShipmentCreate(BaseMutation):
    shipment = graphene.Field(
        Shipment,
        description="The shipment created for the fulfillment.",
    )

    class Arguments:
        fulfillment_id = graphene.ID(
            required=True,
            description="ID of the fulfillment to send to the logistics provider.",
        )
        carrier = graphene.String(
            required=True,
            description="Carrier identifier used by the logistics provider.",
        )

    class Meta:
        description = (
            "Creates a shipment and queues it for the configured logistics adapter."
            + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_ORDERS
        error_type_class = LogisticsShipmentCreateError
        error_type_field = "logistics_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, fulfillment_id, carrier):
        fulfillment = cls.get_node_or_error(info, fulfillment_id, only_type=Fulfillment)
        shipment = create_shipment(fulfillment, carrier)
        return cls(shipment=shipment)
