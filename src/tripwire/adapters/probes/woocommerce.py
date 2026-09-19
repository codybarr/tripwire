from __future__ import annotations

import html
import json
import re
from typing import Any

from ...domain.models import Observation
from ...errors import TripwireError
from ...http import HttpClient


class WooCommerceVariationProbe:
    """Probe WooCommerce's embedded variation data for a selected variation."""

    def observe(self, spec: dict[str, Any], http: HttpClient) -> Observation:
        url = spec["url"]
        page = http.get_text(url)
        match = re.search(r'data-product_variations="(.*?)"', page, re.DOTALL)
        if not match:
            raise TripwireError("WooCommerce variation data was not found")
        try:
            variations = json.loads(html.unescape(match.group(1)))
        except json.JSONDecodeError as error:
            raise TripwireError("WooCommerce variation data was invalid JSON") from error

        attribute, value = spec["attribute"], spec["value"]
        variation = next(
            (item for item in variations if item.get("attributes", {}).get(attribute) == value), None
        )
        if variation is None:
            raise TripwireError(f"WooCommerce variation {attribute}={value!r} was not found")
        in_stock = variation.get("is_in_stock")
        if not isinstance(in_stock, bool):
            raise TripwireError("WooCommerce variation had no usable stock status")
        status = "available" if in_stock else "unavailable"
        return Observation(status, f"Variation {attribute}={value} is {status}", url, {attribute: value})
