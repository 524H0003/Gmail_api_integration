from typing import Optional

from pydantic import BaseModel


class PubSubMessage(BaseModel):
    """
    https://docs.cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage
    """

    data: str
    message_id: str | None = None


class PubSubEnvelope(BaseModel):
    """
    https://developers.google.com/workspace/gmail/api/guides/push#receive-notifications
    """

    message: PubSubMessage
    subscription: str | None = None


class EmailWatchResponse(BaseModel):
    """
    https://developers.google.com/workspace/gmail/api/guides/push?authuser=1#watch-response
    """

    success: bool
    error: Optional[str] = None
    historyId: Optional[str] = None
    expiration: Optional[str] = None
