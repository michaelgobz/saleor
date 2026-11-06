from ..celeryconf import app
from .adapter import AccountingGraphQLAdapter
from .models import JournalEntry
from .services import export_journal


@app.task
def export_journal_task(entry_pk: int) -> None:
    entry = JournalEntry.objects.get(pk=entry_pk)
    export_journal(entry, adapter=AccountingGraphQLAdapter())
