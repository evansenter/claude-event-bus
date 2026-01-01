"""Tests for logging middleware formatting functions."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from event_bus.middleware import RequestLoggingMiddleware, _format_args, _format_result


class TestFormatArgs:
    """Tests for _format_args function."""

    def test_empty_args(self):
        """Test empty arguments."""
        assert _format_args({}) == ""

    def test_simple_args(self):
        """Test simple key-value pairs."""
        result = _format_args({"name": "test", "limit": 10})
        assert 'name="test"' in result
        assert "limit=10" in result

    def test_long_string_truncated(self):
        """Test that long strings are truncated at 50 chars."""
        long_value = "x" * 100
        result = _format_args({"payload": long_value})
        # Should be truncated: 47 chars + "..."
        assert "..." in result
        assert len(result) < 100

    def test_preserves_short_strings(self):
        """Test that short strings are not truncated."""
        result = _format_args({"name": "short"})
        assert result == 'name="short"'


class TestFormatResult:
    """Tests for _format_result function (without colors for easier testing)."""

    def test_session_id_result(self):
        """Test formatting result with session_id."""
        result = _format_result({"session_id": "brave-tiger", "name": "test"}, colorize=False)
        assert result == "session=brave-tiger"

    def test_events_result(self):
        """Test formatting events list result."""
        result = _format_result(
            {
                "events": [{"id": 1}, {"id": 2}, {"id": 3}],
                "next_cursor": "42",
            },
            colorize=False,
        )
        assert result == "3 events, cursor=42"

    def test_events_empty(self):
        """Test formatting empty events list."""
        result = _format_result({"events": [], "next_cursor": None}, colorize=False)
        assert "0 events" in result

    def test_event_id_result(self):
        """Test formatting publish_event result."""
        result = _format_result({"event_id": 123, "channel": "repo:my-project"}, colorize=False)
        assert result == "event #123 [repo:my-project]"

    def test_event_id_default_channel(self):
        """Test formatting publish_event result without channel."""
        result = _format_result({"event_id": 456}, colorize=False)
        assert result == "event #456 [all]"

    def test_success_true(self):
        """Test formatting success=True result."""
        result = _format_result({"success": True}, colorize=False)
        assert result == "OK"

    def test_success_false(self):
        """Test formatting success=False result."""
        result = _format_result({"success": False}, colorize=False)
        assert result == "FAILED"

    def test_error_result(self):
        """Test formatting error result."""
        result = _format_result({"error": "Session not found"}, colorize=False)
        assert result == "ERROR: Session not found"

    def test_fallback_keys(self):
        """Test fallback to listing keys."""
        result = _format_result({"foo": 1, "bar": 2, "baz": 3}, colorize=False)
        assert "foo" in result
        assert "bar" in result
        assert "baz" in result

    def test_list_result(self):
        """Test formatting list result."""
        result = _format_result([{"id": 1}, {"id": 2}], colorize=False)
        assert result == "[2 items]"

    def test_structured_content_unwrap(self):
        """Test unwrapping MCP structuredContent format (direct, not nested)."""
        # FastMCP puts the result directly in structuredContent, not nested under "result"
        result = _format_result({"structuredContent": {"session_id": "clever-fox"}}, colorize=False)
        assert result == "session=clever-fox"

    def test_structured_content_legacy_format(self):
        """Test unwrapping legacy MCP structuredContent format with nested result."""
        result = _format_result(
            {"structuredContent": {"result": {"session_id": "clever-fox"}}}, colorize=False
        )
        assert result == "session=clever-fox"

    def test_content_text_unwrap(self):
        """Test unwrapping MCP content/text format."""
        import json

        result = _format_result(
            {"content": [{"text": json.dumps({"session_id": "bold-eagle"})}]}, colorize=False
        )
        assert result == "session=bold-eagle"

    def test_long_string_truncated(self):
        """Test that long string results are truncated."""
        long_string = "x" * 100
        result = _format_result(long_string, colorize=False)
        assert "..." in result
        assert len(result) <= 83  # 80 chars + "..."

    def test_colorized_output_contains_ansi(self):
        """Test that colorized output contains ANSI codes."""
        result = _format_result({"success": True}, colorize=True)
        assert "\033[" in result  # ANSI escape sequence
        assert "OK" in result


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware ASGI behavior."""

    @pytest.mark.asyncio
    async def test_middleware_passes_through_non_http(self):
        """Test that non-HTTP requests are passed through without modification."""
        app = AsyncMock()
        middleware = RequestLoggingMiddleware(app)

        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # App should be called directly without wrapping
        app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_middleware_passes_through_non_mcp_paths(self):
        """Test that non-MCP paths are passed through."""
        app = AsyncMock()
        middleware = RequestLoggingMiddleware(app)

        scope = {"type": "http", "path": "/health", "method": "GET"}

        async def receive():
            return {"type": "http.request", "body": b""}

        send = AsyncMock()

        await middleware(scope, receive, send)

        # App should still be called
        app.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_logs_tool_call(self):
        """Test that MCP tool calls are logged."""

        # Create a mock app that returns an SSE response
        async def mock_app(scope, receive, send):
            # Consume request
            await receive()
            # Send response
            await send({"type": "http.response.start", "status": 200})
            response_data = json.dumps({"result": {"structuredContent": {"session_id": "test"}}})
            sse_body = f"event: message\ndata: {response_data}\n\n"
            await send({"type": "http.response.body", "body": sse_body.encode()})

        middleware = RequestLoggingMiddleware(mock_app)

        scope = {"type": "http", "path": "/mcp", "method": "POST"}
        request_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "register_session", "arguments": {"name": "test"}},
            }
        )

        async def receive():
            return {"type": "http.request", "body": request_body.encode()}

        send_calls = []

        async def send(message):
            send_calls.append(message)

        with patch("event_bus.middleware.logger") as mock_logger:
            await middleware(scope, receive, send)

            # Should have logged the tool call
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            assert "register_session" in log_call

    @pytest.mark.asyncio
    async def test_middleware_parses_sse_response(self):
        """Test that middleware correctly parses SSE format responses."""

        # Create a mock app with SSE response
        async def mock_app(scope, receive, send):
            await receive()
            await send({"type": "http.response.start", "status": 200})
            # SSE format: "event: message\ndata: {...}\n\n"
            response_data = json.dumps({"result": {"structuredContent": {"events": [1, 2, 3]}}})
            sse_body = f"event: message\ndata: {response_data}\n\n"
            await send({"type": "http.response.body", "body": sse_body.encode()})

        middleware = RequestLoggingMiddleware(mock_app)

        scope = {"type": "http", "path": "/mcp", "method": "POST"}
        request_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_events", "arguments": {}},
            }
        )

        async def receive():
            return {"type": "http.request", "body": request_body.encode()}

        async def send(message):
            pass

        with patch("event_bus.middleware.logger") as mock_logger:
            await middleware(scope, receive, send)

            # Should have parsed SSE and logged the result
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            assert "get_events" in log_call

    @pytest.mark.asyncio
    async def test_middleware_handles_malformed_json(self):
        """Test that middleware handles malformed JSON gracefully."""

        async def mock_app(scope, receive, send):
            await receive()
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.body", "body": b"not json"})

        middleware = RequestLoggingMiddleware(mock_app)

        scope = {"type": "http", "path": "/mcp", "method": "POST"}

        async def receive():
            return {"type": "http.request", "body": b"not json either"}

        async def send(message):
            pass

        # Should not raise - malformed requests are logged at debug level
        with patch("event_bus.middleware.logger") as mock_logger:
            await middleware(scope, receive, send)
            # Should have logged a debug message about non-JSON
            mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_middleware_logs_non_tool_mcp_methods(self):
        """Test that non-tool MCP methods (like resources) are logged at debug level."""

        async def mock_app(scope, receive, send):
            await receive()
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.body", "body": b"{}"})

        middleware = RequestLoggingMiddleware(mock_app)

        scope = {"type": "http", "path": "/mcp", "method": "POST"}
        request_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "resources/list",
                "params": {},
            }
        )

        async def receive():
            return {"type": "http.request", "body": request_body.encode()}

        async def send(message):
            pass

        with patch("event_bus.middleware.logger") as mock_logger:
            await middleware(scope, receive, send)

            # Should log at debug level for non-tool methods
            mock_logger.debug.assert_called()
            debug_call = mock_logger.debug.call_args[0][0]
            assert "resources/list" in debug_call
