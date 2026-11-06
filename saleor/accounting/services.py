from decimal import Decimal

from django.db import transaction
from django.utils.timezone import now

from .adapter import AccountingGraphQLAdapter
from .models import JournalEntry, JournalStatus

EXPORT_JOURNAL = """
mutation ExportJournal($input: JournalInput!) {
  exportJournal(input: $input) {
    id
  }
}
"""


def post_journal(
    *,
    reference: str,
    description: str,
    currency: str,
    lines: list[dict],
    order=None,
) -> JournalEntry:
    debit = sum((Decimal(line["debit"]) for line in lines), Decimal("0"))
    credit = sum((Decimal(line["credit"]) for line in lines), Decimal("0"))
    if debit != credit:
        raise ValueError("Journal entry debits and credits must balance.")
    with transaction.atomic():
        entry = JournalEntry.objects.create(
            reference=reference,
            description=description,
            currency=currency,
            date=now().date(),
            order=order,
        )
        entry.lines.bulk_create(
            [
                entry.lines.model(
                    account_id=line["account_pk"],
                    description=line.get("description", ""),
                    debit=line["debit"],
                    credit=line["credit"],
                )
                for line in lines
            ]
        )
    return entry


def export_journal(entry: JournalEntry, *, adapter: AccountingGraphQLAdapter) -> None:
    payload = adapter.execute(
        EXPORT_JOURNAL,
        {
            "input": {
                "reference": entry.reference,
                "currency": entry.currency,
                "date": entry.date.isoformat(),
                "description": entry.description,
                "lines": [
                    {
                        "accountCode": line.account.code,
                        "debit": str(line.debit),
                        "credit": str(line.credit),
                    }
                    for line in entry.lines.select_related("account")
                ],
            }
        },
        idempotency_key=f"journal:{entry.pk}",
    )
    external_reference = (payload.get("exportJournal") or {}).get("id", "")
    JournalEntry.objects.filter(pk=entry.pk).update(
        external_reference=external_reference, status=JournalStatus.EXPORTED
    )
