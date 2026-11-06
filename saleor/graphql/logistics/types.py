import graphene

from ...logistics import models
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.scalars import DateTime, Decimal
from ..core.types import Error, ModelObjectType
from ..meta.types import ObjectWithMetadata


class DeliveryLocation(ModelObjectType[models.DeliveryLocation]):
    latitude = Decimal(
        required=True,
        description="Latitude in decimal degrees." + ADDED_IN_324,
    )
    longitude = Decimal(
        required=True,
        description="Longitude in decimal degrees." + ADDED_IN_324,
    )
    accuracy_meters = Decimal(
        description="GPS accuracy in meters." + ADDED_IN_324,
    )
    captured_at = DateTime(
        required=True,
        description="Time when the device captured the location." + ADDED_IN_324,
    )

    class Meta:
        description = "Represents a GPS sample captured by a delivery device." + ADDED_IN_324
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [graphene.relay.Node]
        model = models.DeliveryLocation


class Shipment(ModelObjectType[models.Shipment]):
    carrier = graphene.String(
        required=True,
        description="Carrier identifier for this shipment." + ADDED_IN_324,
    )
    status = graphene.String(
        required=True,
        description="Current logistics status of this shipment." + ADDED_IN_324,
    )
    tracking_number = graphene.String(
        required=True,
        description="Carrier tracking number." + ADDED_IN_324,
    )
    latest_location = graphene.Field(
        DeliveryLocation,
        description="The latest GPS location reported for this shipment." + ADDED_IN_324,
    )

    class Meta:
        description = "Represents a logistics shipment." + ADDED_IN_324
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [ObjectWithMetadata, graphene.relay.Node]
        model = models.Shipment

    @staticmethod
    def resolve_latest_location(root: models.Shipment, _info):
        return root.locations.order_by("-captured_at", "-pk").first()


class LogisticsShipmentCreateError(Error):
    code = graphene.String(description="Internal logistics error code.", required=True)

    class Meta:
        description = "An error raised while creating a logistics shipment." + ADDED_IN_324
        doc_category = DOC_CATEGORY_ORDERS


class LogisticsShipmentLocationUpdateError(Error):
    code = graphene.String(description="Internal logistics error code.", required=True)

    class Meta:
        description = (
            "An error raised while updating a shipment GPS location." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_ORDERS
