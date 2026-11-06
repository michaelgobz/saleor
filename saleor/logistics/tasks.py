from ..celeryconf import app
from .adapter import LogisticsGraphQLAdapter
from .models import Shipment

CREATE_SHIPMENT = """
mutation CreateShipment($input: CreateShipmentInput!) {
  createShipment(input: $input) {
    id
    trackingNumber
    labelUrl
  }
}
"""


def dispatch_shipment(shipment: Shipment, *, adapter: LogisticsGraphQLAdapter) -> None:
    payload = adapter.execute(
        CREATE_SHIPMENT,
        {
            "input": {
                "reference": shipment.pk,
                "orderReference": shipment.order.pk,
                "carrier": shipment.carrier,
            }
        },
        idempotency_key=f"shipment:{shipment.pk}",
    )
    result = payload.get("createShipment") or {}
    Shipment.objects.filter(pk=shipment.pk).update(
        tracking_number=result.get("trackingNumber", ""),
        label_url=result.get("labelUrl", ""),
        external_reference=result.get("id", ""),
    )


@app.task
def dispatch_shipment_task(shipment_pk: int) -> None:
    shipment = Shipment.objects.get(pk=shipment_pk)
    dispatch_shipment(shipment, adapter=LogisticsGraphQLAdapter())
