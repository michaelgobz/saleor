import graphene
from django.core.exceptions import ValidationError
from django.utils.timezone import now

from ...permission.enums import OrderPermissions
from ...logistics.services import create_shipment, update_shipment_location
from ..core import ResolveInfo
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.mutations import BaseMutation
from ..core.scalars import DateTime, Decimal
from ..order.types import Fulfillment
from .types import (
    LogisticsShipmentCreateError,
    LogisticsShipmentLocationUpdateError,
    Shipment,
)


class ShipmentCreate(BaseMutation):
    shipment = graphene.Field(
        Shipment,
        description="The shipment created for the fulfillment." + ADDED_IN_324,
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
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = LogisticsShipmentCreateError
        error_type_field = "logistics_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, fulfillment_id, carrier):
        fulfillment = cls.get_node_or_error(info, fulfillment_id, only_type=Fulfillment)
        shipment = create_shipment(fulfillment, carrier)
        return cls(shipment=shipment)


class ShipmentLocationUpdate(BaseMutation):
    shipment = graphene.Field(
        Shipment,
        description="The shipment with its current GPS location updated."
        + ADDED_IN_324,
    )

    class Arguments:
        shipment_id = graphene.ID(
            required=True, description="ID of the shipment being tracked." + ADDED_IN_324
        )
        latitude = Decimal(
            required=True, description="Latitude in decimal degrees." + ADDED_IN_324
        )
        longitude = Decimal(
            required=True, description="Longitude in decimal degrees." + ADDED_IN_324
        )
        accuracy_meters = Decimal(
            required=False,
            description="Optional GPS accuracy in meters." + ADDED_IN_324,
        )
        captured_at = DateTime(
            required=False,
            description="Time when the device captured the location." + ADDED_IN_324,
        )

    class Meta:
        description = (
            "Stores a delivery device GPS sample and updates the shipment map position."
            + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = LogisticsShipmentLocationUpdateError
        error_type_field = "logistics_errors"

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        shipment_id,
        latitude,
        longitude,
        accuracy_meters=None,
        captured_at=None,
    ):
        shipment = cls.get_node_or_error(info, shipment_id, only_type=Shipment)
        captured_at = captured_at or now()
        try:
            update_shipment_location(
                shipment,
                latitude=latitude,
                longitude=longitude,
                accuracy_meters=accuracy_meters,
                captured_at=captured_at,
            )
        except ValueError as error:
            raise ValidationError(str(error), code="invalid") from error
        shipment.refresh_from_db(
            fields=(
                "current_latitude",
                "current_longitude",
                "current_location_accuracy_meters",
                "current_location_updated_at",
            )
        )
        return cls(shipment=shipment)
