import graphene

from ...accounting.models import Account
from ...accounting.services import post_journal
from ..core import ResolveInfo
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.mutations import BaseMutation
from ..core.scalars import Decimal
from ..core.utils import from_global_id_or_error
from .types import AccountingJournalEntryCreateError, JournalEntry


class JournalLineInput(graphene.InputObjectType):
    account_id = graphene.ID(
        required=True, description="ID of the account receiving the journal line."
    )
    debit = Decimal(
        required=False, description="Debit amount. Use zero for a credit line."
    )
    credit = Decimal(
        required=False, description="Credit amount. Use zero for a debit line."
    )
    description = graphene.String(required=False, description="Line description.")


class JournalEntryCreate(BaseMutation):
    journal_entry = graphene.Field(
        JournalEntry, description="The balanced journal entry created."
    )

    class Arguments:
        reference = graphene.String(required=True, description="Unique entry reference.")
        description = graphene.String(required=True, description="Entry description.")
        currency = graphene.String(required=True, description="Three-letter currency.")
        lines = graphene.List(
            JournalLineInput,
            required=True,
            description="Debit and credit lines. The list must balance.",
        )

    class Meta:
        description = (
            "Creates an immutable balanced double-entry accounting journal."
            + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_ORDERS
        error_type_class = AccountingJournalEntryCreateError
        error_type_field = "accounting_errors"

    @classmethod
    def perform_mutation(
        cls, _root, _info: ResolveInfo, /, *, reference, description, currency, lines
    ):
        normalized_lines = [
            {
                "account_pk": from_global_id_or_error(
                    line["account_id"], Account
                )[1],
                "debit": line.get("debit") or 0,
                "credit": line.get("credit") or 0,
                "description": line.get("description", ""),
            }
            for line in lines
        ]
        entry = post_journal(
            reference=reference,
            description=description,
            currency=currency,
            lines=normalized_lines,
        )
        return cls(journal_entry=entry)
