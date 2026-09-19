from __future__ import annotations

from typing import Any, Protocol

from ...domain.models import Observation
from ...errors import TripwireError
from ...http import HttpClient
from .http_json import HttpJsonProbe
from .laudisi import LaudisiProductCardsProbe
from .woocommerce import WooCommerceVariationProbe


class Probe(Protocol):
    def observe(self, spec: dict[str, Any], http: HttpClient) -> Observation: ...


BUILTIN_PROBES: dict[str, Probe] = {
    "http.json": HttpJsonProbe(),
    "woocommerce.variation": WooCommerceVariationProbe(),
    "laudisi.product_cards": LaudisiProductCardsProbe(),
}


def observe(spec: dict[str, Any], http: HttpClient) -> Observation:
    probe_type = spec["type"]
    probe = BUILTIN_PROBES.get(probe_type)
    if probe is None:
        raise TripwireError(f"unsupported probe type {probe_type!r}")
    return probe.observe(spec, http)
