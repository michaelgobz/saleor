import graphene

from ..core.descriptions import ADDED_IN_324
from .mutations import JournalEntryCreate
from .types import JournalEntry


class AccountingQueries(graphene.ObjectType):
    accounting_journal_entry = graphene.Field(
        JournalEntry,
        id=graphene.ID(required=True),
        description="Retrieves an accounting journal entry by ID." + ADDED_IN_324,
    )

    @staticmethod
    def resolve_accounting_journal_entry(_root, info, id):
        return JournalEntry.get_node_from_global_id(info, id)


class AccountingMutations(graphene.ObjectType):
    accounting_journal_entry_create = JournalEntryCreate.Field()
