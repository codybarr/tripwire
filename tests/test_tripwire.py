import unittest
from unittest.mock import patch

from tripwire.adapters.probes.laudisi import LaudisiProductCardsProbe
from tripwire.application.runner import run
from tripwire.domain.models import Observation
from tripwire.errors import TripwireError


class LaudisiProductCardsTest(unittest.TestCase):
    spec = {"url": "https://example.test/products", "name_contains_any": ["(302)", "(303)"]}

    def check(self, page: str) -> bool:
        http = type("Http", (), {"get_text": lambda _, url: page})()
        return LaudisiProductCardsProbe().observe(self.spec, http).status == "available"

    def test_unavailable_when_all_matching_cards_are_out_of_stock(self) -> None:
        page = '''
        <div class="prodBox"><h3 class="prodName">System (302)</h3><p class="outStock">Out</p></div>
        <div class="prodBox"><h3 class="prodName">System (303)</h3><p class="outStock">Out</p></div>
        '''
        self.assertFalse(self.check(page))

    def test_available_when_any_matching_card_lacks_out_of_stock_marker(self) -> None:
        page = '''
        <div class="prodBox"><h3 class="prodName">System (302)</h3><p class="outStock">Out</p></div>
        <div class="prodBox"><h3 class="prodName"><span>System</span> (303)</h3></div>
        '''
        self.assertTrue(self.check(page))

    def test_missing_matching_products_is_an_error(self) -> None:
        http = type("Http", (), {"get_text": lambda _, url: '<div class="prodBox">(309)</div>'})()
        with self.assertRaisesRegex(TripwireError, "no matching Laudisi products"):
            LaudisiProductCardsProbe().observe(self.spec, http)


class RunnerTest(unittest.TestCase):
    config = {
        "notifiers": {"first": {"type": "ntfy"}, "second": {"type": "ntfy"}},
        "monitors": [
            {
                "id": "test",
                "name": "Test monitor",
                "probe": {"type": "fake"},
                "notify": {"on": ["available"], "notifiers": ["first", "second"]},
            }
        ],
    }

    @patch("tripwire.application.runner.timestamp", return_value="2026-01-01T00:00:00+00:00")
    @patch("tripwire.application.runner.deliver")
    @patch("tripwire.application.runner.observe")
    def test_retries_only_notifiers_that_did_not_receive_transition(self, observe, deliver, _timestamp) -> None:
        observe.return_value = Observation("available", "ready", "https://example.test")
        deliver.side_effect = [None, TripwireError("temporary failure")]
        state = {"version": 2, "monitors": {}}
        self.assertEqual(run(self.config, state), 1)
        self.assertEqual(state["monitors"]["test"]["deliveries"], {"available:2026-01-01T00:00:00+00:00": {"first": "2026-01-01T00:00:00+00:00"}})

        deliver.reset_mock()
        deliver.side_effect = None
        deliver.return_value = None
        self.assertEqual(run(self.config, state), 0)
        deliver.assert_called_once()
        self.assertEqual(deliver.call_args.args[0], self.config["notifiers"]["second"])


if __name__ == "__main__":
    unittest.main()
