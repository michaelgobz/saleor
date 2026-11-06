from django.db import transaction

from ..order.models import Fulfillment
from .models import Shipment
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
