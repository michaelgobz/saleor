from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils.timezone import now

from ..order.models import Fulfillment
from .models import DeliveryLocation, Shipment
from .tasks import dispatch_shipment_task

CREATE_SHIPMENT = """
mutation CreateShipment($input: CreateShipmentInput!) {
  createShipment(input: $input) {
    id
    trackingNumber
    labelUrl
  }
}
"""


def create_shipment(
    fulfillment: Fulfillment,
    carrier: str,
) -> Shipment:
    with transaction.atomic():
        shipment = Shipment.objects.create(
            fulfillment=fulfillment,
            order=fulfillment.order,
            carrier=carrier,
        )
        transaction.on_commit(
            lambda: dispatch_shipment_task.delay(
                shipment.pk,
            )
        )
    return shipment


def update_shipment_location(
    shipment: Shipment,
    *,
    latitude: Decimal,
    longitude: Decimal,
    accuracy_meters: Decimal | None,
    captured_at: datetime | None,
) -> DeliveryLocation | None:
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees.")
    if accuracy_meters is not None and accuracy_meters < 0:
        raise ValueError("GPS accuracy cannot be negative.")
    captured_at = captured_at or now()
    with transaction.atomic():
        locked_shipment = Shipment.objects.select_for_update().get(pk=shipment.pk)
        if (
            locked_shipment.current_location_updated_at
            and captured_at <= locked_shipment.current_location_updated_at
        ):
            return None

        location = DeliveryLocation.objects.create(
            shipment=locked_shipment,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            captured_at=captured_at,
        )
        Shipment.objects.filter(pk=locked_shipment.pk).update(
            current_latitude=latitude,
            current_longitude=longitude,
            current_location_accuracy_meters=accuracy_meters,
            current_location_updated_at=captured_at,
        )
    return location
