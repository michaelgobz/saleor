from django.contrib.postgres.indexes import BTreeIndex
from django.db import models
from django.db.models import Q
from django.utils.timezone import now

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
    current_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    current_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    current_location_accuracy_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    current_location_updated_at = models.DateTimeField(null=True, blank=True)

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


class DeliveryLocation(models.Model):
    shipment = models.ForeignKey(
        Shipment, related_name="locations", on_delete=models.CASCADE
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    captured_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ("-captured_at", "-pk")
        indexes = [
            BTreeIndex(
                fields=("shipment", "-captured_at"),
                name="delivery_location_ship_time_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(latitude__gte=-90, latitude__lte=90),
                name="delivery_location_latitude_range",
            ),
            models.CheckConstraint(
                condition=Q(longitude__gte=-180, longitude__lte=180),
                name="delivery_location_longitude_range",
            ),
            models.CheckConstraint(
                condition=Q(accuracy_meters__isnull=True)
                | Q(accuracy_meters__gte=0),
                name="delivery_location_accuracy_non_negative",
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
