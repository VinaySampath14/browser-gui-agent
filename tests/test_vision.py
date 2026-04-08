"""
Tests for the vision layer's _validate() function in agent/vision.py
These verify GPT-4o response parsing — no API calls made.
"""
import pytest
from agent.vision import _validate


VALID_RESPONSE = {
    "observation": "A search results page with car listings",
    "reasoning": "I need to click the first listing to open it",
    "action": "click",
    "params": {"x": 640, "y": 300, "description": "first listing"},
}


class TestValidate:
    def test_valid_click(self):
        result = _validate(VALID_RESPONSE)
        assert result["action"] == "click"

    def test_valid_fill(self):
        response = {**VALID_RESPONSE, "action": "fill", "params": {"selector": "input[name='email']", "text": "test@example.com"}}
        result = _validate(response)
        assert result["action"] == "fill"

    def test_valid_done(self):
        response = {**VALID_RESPONSE, "action": "done", "params": {"result": "VW Golf, 12.500 €"}}
        result = _validate(response)
        assert result["action"] == "done"

    def test_valid_extract(self):
        response = {**VALID_RESPONSE, "action": "extract", "params": {"result": "Autohaus Müller"}}
        result = _validate(response)
        assert result["action"] == "extract"

    def test_valid_click_selector(self):
        response = {**VALID_RESPONSE, "action": "click_selector", "params": {"selector": "button:has-text('Preis')", "description": "open price filter"}}
        result = _validate(response)
        assert result["action"] == "click_selector"

    def test_all_valid_actions(self):
        valid_actions = {"click", "click_selector", "type", "fill", "scroll", "press", "navigate", "extract", "done"}
        for action in valid_actions:
            response = {**VALID_RESPONSE, "action": action}
            result = _validate(response)
            assert result["action"] == action

    def test_missing_observation_raises(self):
        bad = {k: v for k, v in VALID_RESPONSE.items() if k != "observation"}
        with pytest.raises(ValueError, match="missing fields"):
            _validate(bad)

    def test_missing_action_raises(self):
        bad = {k: v for k, v in VALID_RESPONSE.items() if k != "action"}
        with pytest.raises(ValueError, match="missing fields"):
            _validate(bad)

    def test_missing_params_raises(self):
        bad = {k: v for k, v in VALID_RESPONSE.items() if k != "params"}
        with pytest.raises(ValueError, match="missing fields"):
            _validate(bad)

    def test_unknown_action_raises(self):
        bad = {**VALID_RESPONSE, "action": "hover"}
        with pytest.raises(ValueError, match="Unknown action"):
            _validate(bad)

    def test_unknown_action_submit_raises(self):
        bad = {**VALID_RESPONSE, "action": "submit"}
        with pytest.raises(ValueError, match="Unknown action"):
            _validate(bad)

    def test_returns_full_dict(self):
        result = _validate(VALID_RESPONSE)
        assert set(result.keys()) >= {"observation", "reasoning", "action", "params"}
