"""Tests for middleware formatting functions."""

from event_bus.middleware import (
    _BOLD,
    _CYAN,
    _DIM,
    _GREEN,
    _MAGENTA,
    _RED,
    _format_args,
    _format_list,
    _format_result,
    _parse_sse_response,
)


class TestFormatArgs:
    """Tests for _format_args function."""

    def test_empty_args(self):
        """Empty args returns empty string."""
        assert _format_args({}) == ""

    def test_simple_args(self):
        """Simple args are formatted as key=value."""
        result = _format_args({"limit": 10})
        assert "limit=10" in result

    def test_string_args(self):
        """String values are JSON-quoted."""
        result = _format_args({"type": "test"})
        assert 'type="test"' in result

    def test_highlighted_fields(self):
        """session_id, name, channel, client_id are highlighted."""
        result = _format_args({"session_id": "test-session"})
        assert _CYAN in result
        assert _BOLD in result
        assert "session_id" in result
        assert "test-session" in result

    def test_multiple_args(self):
        """Multiple args are comma-separated."""
        result = _format_args({"limit": 10, "order": "desc"})
        assert "limit=10" in result
        assert 'order="desc"' in result
        assert ", " in result


class TestFormatList:
    """Tests for _format_list function."""

    def test_empty_list(self):
        """Empty list shows 'empty'."""
        result = _format_list([])
        assert "empty" in result
        assert _DIM in result

    def test_session_list(self):
        """List with session_id shows names."""
        items = [
            {"session_id": "brave-tiger"},
            {"session_id": "happy-falcon"},
        ]
        result = _format_list(items)
        assert "brave-tiger" in result
        assert "happy-falcon" in result
        assert _CYAN in result

    def test_channel_list(self):
        """List with channel+subscribers shows channel names."""
        items = [
            {"channel": "all", "subscribers": 5},
            {"channel": "repo:test", "subscribers": 2},
        ]
        result = _format_list(items)
        assert "all" in result
        assert "repo:test" in result

    def test_generic_list(self):
        """List without session_id/channel shows count."""
        items = [{"foo": "bar"}, {"baz": "qux"}]
        result = _format_list(items)
        assert "2 items" in result


class TestFormatResult:
    """Tests for _format_result function."""

    def test_session_id_result(self):
        """Result with session_id shows session=name."""
        result = _format_result({"session_id": "tender-hawk"})
        assert "session=tender-hawk" in result
        assert _CYAN in result

    def test_events_result_empty(self):
        """Empty events result shows 0 events."""
        result = _format_result({"events": [], "next_cursor": "0"})
        assert "0 events" in result
        assert "cursor=0" in result

    def test_events_result_with_count(self):
        """Events result shows count and cursor."""
        events = [
            {"id": 1, "session_id": "test", "timestamp": "2026-01-01T12:00:00"},
            {"id": 2, "session_id": "test", "timestamp": "2026-01-01T12:05:00"},
        ]
        result = _format_result({"events": events, "next_cursor": "2"})
        assert "2 events" in result
        assert "cursor=2" in result

    def test_events_result_with_publishers(self):
        """Events result shows unique publishers."""
        events = [
            {"id": 1, "session_id": "brave-tiger", "timestamp": "2026-01-01T12:00:00"},
            {"id": 2, "session_id": "happy-falcon", "timestamp": "2026-01-01T12:05:00"},
        ]
        result = _format_result({"events": events, "next_cursor": "2"})
        assert "from:" in result
        assert "brave-tiger" in result
        assert "happy-falcon" in result

    def test_events_result_excludes_anonymous(self):
        """Anonymous publishers are not shown."""
        events = [
            {"id": 1, "session_id": "anonymous", "timestamp": "2026-01-01T12:00:00"},
        ]
        result = _format_result({"events": events, "next_cursor": "1"})
        assert "from:" not in result

    def test_event_id_result(self):
        """Result with event_id shows event #N."""
        result = _format_result({"event_id": 42, "channel": "all"})
        assert "event #42" in result
        assert "[all]" in result
        assert _MAGENTA in result

    def test_success_true_result(self):
        """Success=true shows OK."""
        result = _format_result({"success": True})
        assert "OK" in result
        assert _GREEN in result

    def test_success_false_result(self):
        """Success=false shows FAILED."""
        result = _format_result({"success": False})
        assert "FAILED" in result
        assert _RED in result

    def test_error_result(self):
        """Error result shows ERROR: message."""
        result = _format_result({"error": "Something went wrong"})
        assert "ERROR:" in result
        assert "Something went wrong" in result

    def test_structured_content_unwrapping(self):
        """FastMCP structuredContent wrapper is unwrapped."""
        wrapped = {
            "structuredContent": {"session_id": "test-session"},
            "content": [],
            "isError": False,
        }
        result = _format_result(wrapped)
        assert "session=test-session" in result

    def test_list_result(self):
        """List result delegates to _format_list."""
        result = _format_result([{"session_id": "a"}, {"session_id": "b"}])
        assert "a" in result
        assert "b" in result

    def test_fallback_shows_keys(self):
        """Unknown dict shows keys."""
        result = _format_result({"foo": "bar", "baz": 123})
        assert "foo" in result or "baz" in result


class TestParseSSEResponse:
    """Tests for _parse_sse_response function."""

    def test_valid_sse_response(self):
        """Valid SSE response extracts JSON from data line."""
        sse = 'event: message\ndata: {"result": {"session_id": "test"}}\n\n'
        result = _parse_sse_response(sse)
        assert result == {"result": {"session_id": "test"}}

    def test_multiline_sse_response(self):
        """SSE with multiple data lines uses first valid one."""
        sse = 'event: message\ndata: {"first": true}\nevent: other\ndata: {"second": true}\n\n'
        result = _parse_sse_response(sse)
        assert result == {"first": True}

    def test_empty_response(self):
        """Empty response returns empty dict."""
        result = _parse_sse_response("")
        assert result == {}

    def test_no_data_line(self):
        """Response without data line returns empty dict."""
        result = _parse_sse_response("event: message\n\n")
        assert result == {}

    def test_invalid_json(self):
        """Invalid JSON in data line returns empty dict."""
        result = _parse_sse_response("data: not-valid-json\n\n")
        assert result == {}

    def test_data_prefix_only(self):
        """data: prefix without content returns empty dict."""
        result = _parse_sse_response("data: \n\n")
        assert result == {}
