from __future__ import annotations

import urllib.error
import urllib.request
from functools import cache

from .errors import TripwireError

USER_AGENT = "tripwire/2.0"


class HttpClient:
    @cache
    def get_text(self, url: str) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise TripwireError(f"{url}: returned HTTP {response.status}")
                return response.read().decode("utf-8")
        except (urllib.error.URLError, UnicodeDecodeError) as error:
            raise TripwireError(f"Could not fetch {url}: {error}") from error
