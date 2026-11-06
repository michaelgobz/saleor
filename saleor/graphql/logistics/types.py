import graphene

from ...logistics import models
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.types import Error, ModelObjectType
from ..meta.types import ObjectWithMetadata


class Shipment(ModelObjectType[models.Shipment]):
    class Meta:
        description = "Represents a logistics shipment." + ADDED_IN_324
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [ObjectWithMetadata, graphene.relay.Node]
        model = models.Shipment


class LogisticsShipmentCreateError(Error):
    code = graphene.String(description="Internal logistics error code.", required=True)

    class Meta:
        description = "An error raised while creating a logistics shipment." + ADDED_IN_324
        doc_category = DOC_CATEGORY_ORDERS
