import graphene

from ...accounting import models
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.types import Error, ModelObjectType
from ..meta.types import ObjectWithMetadata


class JournalEntry(ModelObjectType[models.JournalEntry]):
    class Meta:
        description = (
            "Represents an immutable double-entry accounting journal." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [ObjectWithMetadata, graphene.relay.Node]
        model = models.JournalEntry


class AccountingJournalEntryCreateError(Error):
    code = graphene.String(description="Internal accounting error code.", required=True)

    class Meta:
        description = (
            "An error raised while creating an accounting journal." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_ORDERS
