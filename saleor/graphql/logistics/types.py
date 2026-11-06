import graphene

from ...logistics import models
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.types import Error, ModelObjectType
from ..meta.types import ObjectWithMetadata


class DeliveryLocation(ModelObjectType[models.DeliveryLocation]):
    class Meta:
        description = "Represents a GPS sample captured by a delivery device." + ADDED_IN_324
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [graphene.relay.Node]
        model = models.DeliveryLocation


class Shipment(ModelObjectType[models.Shipment]):
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
