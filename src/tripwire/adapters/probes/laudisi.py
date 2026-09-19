from __future__ import annotations

from html.parser import HTMLParser
from typing import Any

from ...domain.models import Observation
from ...errors import TripwireError
from ...http import HttpClient


class LaudisiProductParser(HTMLParser):
    """Extract product names and stock markers from Laudisi product cards."""

    def __init__(self) -> None:
        super().__init__()
        self.products: list[tuple[str, bool]] = []
        self.card_depth = self.name_depth = 0
        self.name_parts: list[str] = []
        self.out_of_stock = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = set((dict(attrs).get("class") or "").split())
        if tag == "div" and "prodBox" in classes and self.card_depth == 0:
            self.card_depth, self.name_parts, self.out_of_stock = 1, [], False
            return
        if not self.card_depth:
            return
        if tag == "div":
            self.card_depth += 1
        if "prodName" in classes:
            self.name_depth = 1
        elif self.name_depth:
            self.name_depth += 1
        if "outStock" in classes:
            self.out_of_stock = True

    def handle_endtag(self, tag: str) -> None:
        if not self.card_depth:
            return
        if self.name_depth:
            self.name_depth -= 1
        if tag == "div":
            self.card_depth -= 1
            if self.card_depth == 0:
                name = " ".join("".join(self.name_parts).split())
                if name:
                    self.products.append((name, self.out_of_stock))

    def handle_data(self, data: str) -> None:
        if self.name_depth:
            self.name_parts.append(data)


class LaudisiProductCardsProbe:
    """Site-specific adapter retained as a built-in compatibility integration."""

    def observe(self, spec: dict[str, Any], http: HttpClient) -> Observation:
        parser = LaudisiProductParser()
        url = spec["url"]
        parser.feed(http.get_text(url))
        needles = spec["name_contains_any"]
        matches = [
            (name, out_of_stock)
            for name, out_of_stock in parser.products
            if any(needle.casefold() in name.casefold() for needle in needles)
        ]
        if not matches:
            raise TripwireError("no matching Laudisi products were found")
        available = any(not out_of_stock for _, out_of_stock in matches)
        status = "available" if available else "unavailable"
        return Observation(status, f"{len(matches)} matching Laudisi product card(s): {status}", url)
