from django.conf import settings
from django.contrib.postgres.indexes import BTreeIndex
from django.db import models
from django.db.models import Q

from ..core.models import ModelWithMetadata
from ..order.models import Fulfillment, Order


class ShipmentStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    IN_TRANSIT = "IN_TRANSIT", "In transit"
    DELIVERED = "DELIVERED", "Delivered"
    CANCELED = "CANCELED", "Canceled"


class ReturnStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    RECEIVED = "RECEIVED", "Received"
    COMPLETED = "COMPLETED", "Completed"
    CANCELED = "CANCELED", "Canceled"


class Shipment(ModelWithMetadata):
    fulfillment = models.OneToOneField(
        Fulfillment, related_name="shipment", on_delete=models.PROTECT
    )
    order = models.ForeignKey(Order, related_name="shipments", on_delete=models.PROTECT)
    carrier = models.CharField(max_length=128)
    status = models.CharField(
        max_length=32, choices=ShipmentStatus.choices, default=ShipmentStatus.CREATED
    )
    tracking_number = models.CharField(max_length=255, blank=True, default="")
    external_reference = models.CharField(max_length=255, blank=True, default="")
    label_url = models.URLField(max_length=2048, blank=True, default="")
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta(ModelWithMetadata.Meta):
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            BTreeIndex(fields=("status",), name="shipment_status_idx"),
            BTreeIndex(
                fields=("external_reference",),
                name="shipment_external_ref_idx",
                condition=Q(external_reference__gt=""),
            ),
        ]


class Return(ModelWithMetadata):
    order = models.ForeignKey(Order, related_name="logistics_returns", on_delete=models.PROTECT)
    shipment = models.ForeignKey(
        Shipment,
        related_name="returns",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        max_length=32, choices=ReturnStatus.choices, default=ReturnStatus.REQUESTED
    )
    external_reference = models.CharField(max_length=255, blank=True, default="")

    class Meta(ModelWithMetadata.Meta):
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            BTreeIndex(fields=("status",), name="logistics_return_status_idx"),
        ]
