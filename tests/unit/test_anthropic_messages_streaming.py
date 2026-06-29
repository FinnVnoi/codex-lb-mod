from __future__ import annotations

import pytest

from app.core.openai.anthropic import stream_anthropic_messages


@pytest.mark.asyncio
async def test_stream_anthropic_messages_drains_upstream_after_terminal_event() -> None:
    drained_after_terminal = False

    async def upstream():
        nonlocal drained_after_terminal
        yield 'data: {"type":"response.output_text.delta","delta":"Hi"}\n\n'
        yield (
            'data: {"type":"response.completed","response":{"id":"resp_1",'
            '"usage":{"input_tokens":4,"output_tokens":1,"total_tokens":5}}}\n\n'
        )
        drained_after_terminal = True

    chunks = [chunk async for chunk in stream_anthropic_messages(upstream(), model="gpt-5.2")]

    assert drained_after_terminal is True
    assert any('event: message_stop' in chunk for chunk in chunks)
    assert any('"output_tokens":1' in chunk for chunk in chunks)
