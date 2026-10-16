from typing import Optional

from pydantic import BaseModel


class EmailWatchResponse(BaseModel):
    """
    https://developers.google.com/workspace/gmail/api/guides/push?authuser=1#watch-response
    """

    success: bool
    error: Optional[str]
    historyId: str
    expiration: str
