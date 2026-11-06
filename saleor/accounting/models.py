from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.indexes import BTreeIndex
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from ..core.models import ModelWithMetadata
from ..order.models import Order


class AccountType(models.TextChoices):
    ASSET = "ASSET", "Asset"
    LIABILITY = "LIABILITY", "Liability"
    EQUITY = "EQUITY", "Equity"
    REVENUE = "REVENUE", "Revenue"
    EXPENSE = "EXPENSE", "Expense"


class JournalStatus(models.TextChoices):
    POSTED = "POSTED", "Posted"
    EXPORTED = "EXPORTED", "Exported"
    FAILED = "FAILED", "Failed"


class Account(ModelWithMetadata):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=16, choices=AccountType.choices)
    active = models.BooleanField(default=True)


class JournalEntry(ModelWithMetadata):
    reference = models.CharField(max_length=128, unique=True)
    order = models.ForeignKey(
        Order, related_name="accounting_journal_entries", null=True, blank=True,
        on_delete=models.PROTECT,
    )
    date = models.DateField()
    description = models.CharField(max_length=512)
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=16, choices=JournalStatus.choices, default=JournalStatus.POSTED
    )
    external_reference = models.CharField(max_length=255, blank=True, default="")

    class Meta(ModelWithMetadata.Meta):
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            BTreeIndex(fields=("date",), name="journal_entry_date_idx"),
            BTreeIndex(
                fields=("external_reference",),
                name="journal_entry_external_ref_idx",
                condition=Q(external_reference__gt=""),
            ),
        ]


class JournalLine(models.Model):
    entry = models.ForeignKey(
        JournalEntry, related_name="lines", on_delete=models.PROTECT
    )
    account = models.ForeignKey(
        Account, related_name="journal_lines", on_delete=models.PROTECT
    )
    description = models.CharField(max_length=512, blank=True, default="")
    debit = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    credit = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(debit__gt=0, credit=0) | Q(credit__gt=0, debit=0),
                name="journal_line_one_sided_amount",
            )
        ]


class StandardCost(ModelWithMetadata):
    variant = models.ForeignKey(
        "product.ProductVariant", related_name="standard_costs", on_delete=models.PROTECT
    )
    currency = models.CharField(max_length=3)
    unit_cost = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        validators=[MinValueValidator(Decimal("0"))],
    )
    effective_from = models.DateTimeField()
    active = models.BooleanField(default=True)

    class Meta(ModelWithMetadata.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=("variant", "currency", "effective_from"),
                name="standard_cost_variant_currency_effective_unique",
            )
        ]
