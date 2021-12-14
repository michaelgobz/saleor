from django.http import request
import graphene

from ...webhook import models
from ...webhook.deprecated_event_types import WebhookEventType
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core.descriptions import DEPRECATED_IN_3X_FIELD
from ..core.types import ModelObjectType
from . import enums


class WebhookEvent(ModelObjectType):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Webhook event."

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return WebhookEventType.DISPLAY_LABELS.get(root.event_type) or root.event_type


class WebhookEventAsync(ModelObjectType):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeAsyncEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Asynchronous webhook event."

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return (
            WebhookEventAsyncType.DISPLAY_LABELS.get(root.event_type) or root.event_type
        )


class WebhookEventSync(ModelObjectType):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeSyncEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Synchronous webhook event."

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return (
            WebhookEventAsyncType.DISPLAY_LABELS.get(root.event_type) or root.event_type
        )


class Webhook(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    events = graphene.List(
        graphene.NonNull(WebhookEvent),
        description="List of webhook events.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `asyncEvents` or `syncEvents` instead."
        ),
        required=True,
    )
    sync_events = graphene.List(
        graphene.NonNull(WebhookEventSync),
        description="List of synchronous webhook events.",
        required=True,
    )
    async_events = graphene.List(
        graphene.NonNull(WebhookEventAsync),
        description="List of asynchronous webhook events.",
        required=True,
    )
    app = graphene.Field("saleor.graphql.app.types.App", required=True)
    target_url = graphene.String(required=True)
    is_active = graphene.Boolean(required=True)
    secret_key = graphene.String()

    class Meta:
        description = "Webhook."
        model = models.Webhook
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_async_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.filter(event_type__in=WebhookEventAsyncType.ALL)

    @staticmethod
    def resolve_sync_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.filter(event_type__in=WebhookEventSyncType.ALL)

    @staticmethod
    def resolve_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.all()
