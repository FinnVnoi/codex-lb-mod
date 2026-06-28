from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator, Iterable, Mapping
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from app.core.openai.exceptions import ClientPayloadError
from app.core.openai.requests import ResponsesReasoning, ResponsesRequest
from app.core.types import JsonValue
from app.core.utils.json_guards import is_json_list, is_json_mapping
from app.core.utils.sse import format_sse_data, parse_sse_data_json

_ANTHROPIC_TEXT_PART_TYPES = frozenset({"text", "input_text", "output_text"})
_ANTHROPIC_IMAGE_MEDIA_TO_MIME = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


class AnthropicThinkingConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str | None = None
    budget_tokens: StrictInt | None = Field(default=None, ge=0)


class AnthropicMessagesRequest(BaseModel):
    """Anthropic Messages-compatible request surface.

    This is intentionally a compatibility adapter: it accepts the common
    Anthropic Messages fields and maps the request to codex-lb's internal
    Responses path. Unsupported Anthropic-only controls are accepted via
    ``extra='allow'`` and ignored unless they have a close Responses
    equivalent.
    """

    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1)
    messages: list[JsonValue] = Field(default_factory=list)
    system: JsonValue | None = None
    tools: JsonValue | None = None
    tool_choice: JsonValue | None = None
    stream: JsonValue | None = None
    max_tokens: JsonValue | None = None
    stop_sequences: JsonValue | None = None
    temperature: JsonValue | None = None
    top_p: JsonValue | None = None
    top_k: JsonValue | None = None
    metadata: JsonValue | None = None
    thinking: AnthropicThinkingConfig | JsonValue | None = None

    @model_validator(mode="after")
    def _validate_messages(self) -> "AnthropicMessagesRequest":
        for index, message in enumerate(self.messages):
            message_mapping = _json_mapping(message)
            if message_mapping is None:
                raise ValueError(f"messages[{index}] must be an object")
            role = message_mapping.get("role")
            if role not in ("user", "assistant", "system", "developer"):
                raise ValueError(
                    f"messages[{index}].role must be 'user', 'assistant', 'system', or 'developer'"
                )
        return self

    def to_responses_request(self) -> ResponsesRequest:
        instructions = "\n".join(
            part
            for part in (
                _anthropic_system_to_instructions(self.system),
                _anthropic_messages_to_instructions(self.messages),
            )
            if part
        )
        payload: dict[str, JsonValue] = {
            "model": self.model,
            "instructions": instructions,
            "input": _anthropic_messages_to_responses_input(self.messages),
            "store": False,
        }
        stream = _anthropic_bool_or_none(self.stream)
        if stream is not None:
            payload["stream"] = stream
        stop_sequences = _anthropic_stop_sequences(self.stop_sequences)
        if stop_sequences is not None:
            payload["stop"] = stop_sequences
        reasoning = _anthropic_thinking_to_reasoning(self.thinking)
        if reasoning is not None:
            payload["reasoning"] = reasoning.model_dump(mode="json", exclude_none=True)
        tools = _anthropic_tools_to_responses(_anthropic_list_field(self.tools, field_name="tools"))
        if tools:
            payload["tools"] = tools
        tool_choice = _anthropic_tool_choice_to_responses(self.tool_choice)
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        return ResponsesRequest.model_validate(payload)


def _json_mapping(value: JsonValue) -> Mapping[str, JsonValue] | None:
    if not is_json_mapping(value):
        return None
    return value


def _json_list(value: JsonValue) -> list[JsonValue] | None:
    if not is_json_list(value):
        return None
    return value


def _anthropic_list_field(value: JsonValue | None, *, field_name: str) -> list[JsonValue]:
    if value is None:
        return []
    values = _json_list(value)
    if values is None:
        raise ClientPayloadError(f"{field_name} must be an array.", param=field_name)
    return values


def _anthropic_bool_or_none(value: JsonValue | None) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _anthropic_stop_sequences(value: JsonValue | None) -> str | list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    values = _json_list(value)
    if values is None:
        return None
    return [item for item in values if isinstance(item, str)]


def _anthropic_system_to_instructions(system: JsonValue | None) -> str:
    if system is None:
        return ""
    if isinstance(system, str):
        return system
    parts: list[str] = []
    for part in _json_list(system) or [system]:
        if isinstance(part, str):
            parts.append(part)
            continue
        mapping = _json_mapping(part)
        if mapping is None:
            continue
        text = mapping.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "\n".join(part for part in parts if part)


def _anthropic_messages_to_instructions(messages: list[JsonValue]) -> str:
    parts: list[str] = []
    for message in messages:
        mapping = _json_mapping(message)
        if mapping is None:
            continue
        role = mapping.get("role")
        if role not in ("system", "developer"):
            continue
        text = _anthropic_content_to_text(mapping.get("content"))
        if text:
            parts.append(text)
    return "\n".join(parts)


def _anthropic_messages_to_responses_input(messages: list[JsonValue]) -> list[JsonValue]:
    output: list[JsonValue] = []
    for message in messages:
        mapping = _json_mapping(message)
        if mapping is None:
            raise ClientPayloadError("Each message must be an object.", param="messages")
        role = mapping.get("role")
        if role in ("system", "developer"):
            continue
        if role not in ("user", "assistant"):
            raise ClientPayloadError("Anthropic messages only support user and assistant roles.", param="messages")
        content = mapping.get("content")
        output.extend(_anthropic_message_to_responses_items(cast(str, role), content))
    return output


def _anthropic_message_to_responses_items(role: str, content: JsonValue) -> list[JsonValue]:
    if isinstance(content, str) or content is None:
        return [
            {
                "role": role,
                "content": [
                    {
                        "type": "output_text" if role == "assistant" else "input_text",
                        "text": content or "",
                    }
                ],
            }
        ]

    parts = _json_list(content)
    if parts is None:
        raise ClientPayloadError("message content must be a string or array.", param="messages.content")

    message_parts: list[JsonValue] = []
    items: list[JsonValue] = []
    for part in parts:
        part_mapping = _json_mapping(part)
        if part_mapping is None:
            if isinstance(part, str):
                message_parts.append(
                    {"type": "output_text" if role == "assistant" else "input_text", "text": part}
                )
                continue
            raise ClientPayloadError("message content parts must be objects.", param="messages.content")

        part_type = part_mapping.get("type")
        if part_type in _ANTHROPIC_TEXT_PART_TYPES or (part_type is None and isinstance(part_mapping.get("text"), str)):
            text = part_mapping.get("text")
            if not isinstance(text, str):
                raise ClientPayloadError("text content blocks must include text.", param="messages.content")
            message_parts.append(
                {"type": "output_text" if role == "assistant" else "input_text", "text": text}
            )
            continue

        if role == "user" and part_type == "image":
            message_parts.append(_anthropic_image_to_responses_part(part_mapping))
            continue

        if role == "assistant" and part_type == "tool_use":
            if message_parts:
                items.append({"role": "assistant", "content": message_parts})
                message_parts = []
            items.append(_anthropic_tool_use_to_responses_item(part_mapping))
            continue

        if role == "user" and part_type == "tool_result":
            if message_parts:
                items.append({"role": "user", "content": message_parts})
                message_parts = []
            items.append(_anthropic_tool_result_to_responses_item(part_mapping))
            continue

        if part_type in {"thinking", "redacted_thinking"}:
            continue

        fallback_text = _anthropic_content_block_fallback_text(part_mapping)
        if fallback_text is not None:
            message_parts.append(
                {"type": "output_text" if role == "assistant" else "input_text", "text": fallback_text}
            )
            continue

        raise ClientPayloadError(f"Unsupported Anthropic content block type: {part_type}", param="messages.content")

    if message_parts or not items:
        items.append({"role": role, "content": message_parts})
    return items


def _anthropic_content_block_fallback_text(part: Mapping[str, JsonValue]) -> str | None:
    text = part.get("text")
    if isinstance(text, str):
        return text
    content = part.get("content")
    if content is not None:
        extracted = _anthropic_content_to_text(content)
        if extracted:
            return extracted
    return None


def _anthropic_image_to_responses_part(part: Mapping[str, JsonValue]) -> JsonValue:
    source = _json_mapping(part.get("source"))
    if source is None:
        raise ClientPayloadError("image blocks require a source object.", param="messages.content.source")
    source_type = source.get("type")
    if source_type == "url":
        url = source.get("url")
        if not isinstance(url, str) or not url:
            raise ClientPayloadError("image url source requires url.", param="messages.content.source.url")
        return {"type": "input_image", "image_url": url}
    if source_type == "base64":
        data = source.get("data")
        media_type = source.get("media_type") or source.get("mediaType")
        if not isinstance(data, str) or not data:
            raise ClientPayloadError("base64 image source requires data.", param="messages.content.source.data")
        if not isinstance(media_type, str) or not media_type:
            media_type = "image/png"
        return {"type": "input_image", "image_url": f"data:{media_type};base64,{data}"}
    raise ClientPayloadError(f"Unsupported image source type: {source_type}", param="messages.content.source.type")


def _anthropic_tool_use_to_responses_item(part: Mapping[str, JsonValue]) -> JsonValue:
    call_id = part.get("id")
    name = part.get("name")
    arguments = part.get("input")
    if not isinstance(call_id, str) or not call_id:
        raise ClientPayloadError("tool_use blocks require id.", param="messages.content.id")
    if not isinstance(name, str) or not name:
        raise ClientPayloadError("tool_use blocks require name.", param="messages.content.name")
    return {
        "type": "function_call",
        "call_id": call_id,
        "name": name,
        "arguments": json.dumps(arguments if arguments is not None else {}, separators=(",", ":")),
    }


def _anthropic_tool_result_to_responses_item(part: Mapping[str, JsonValue]) -> JsonValue:
    call_id = part.get("tool_use_id")
    if not isinstance(call_id, str) or not call_id:
        raise ClientPayloadError("tool_result blocks require tool_use_id.", param="messages.content.tool_use_id")
    content = part.get("content")
    if isinstance(content, str):
        output = content
    elif content is None:
        output = ""
    else:
        output = _anthropic_content_to_text(content)
    return {"type": "function_call_output", "call_id": call_id, "output": output}


def _anthropic_content_to_text(content: JsonValue) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for part in _json_list(content) or [content]:
        if isinstance(part, str):
            parts.append(part)
            continue
        mapping = _json_mapping(part)
        if mapping is None:
            continue
        text = mapping.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts)


def _anthropic_tools_to_responses(tools: list[JsonValue]) -> list[JsonValue]:
    normalized: list[JsonValue] = []
    for index, tool in enumerate(tools):
        mapping = _json_mapping(tool)
        if mapping is None:
            raise ClientPayloadError(f"tools[{index}] must be an object", param=f"tools[{index}]")
        name = mapping.get("name")
        if not isinstance(name, str) or not name:
            raise ClientPayloadError(f"tools[{index}].name is required", param=f"tools[{index}].name")
        description = mapping.get("description")
        input_schema = mapping.get("input_schema") or mapping.get("inputSchema") or {"type": "object"}
        tool_payload: dict[str, JsonValue] = {
            "type": "function",
            "name": name,
            "parameters": input_schema,
        }
        if isinstance(description, str):
            tool_payload["description"] = description
        normalized.append(tool_payload)
    return normalized


def _anthropic_tool_choice_to_responses(tool_choice: JsonValue | None) -> JsonValue | None:
    if tool_choice is None:
        return None
    if isinstance(tool_choice, str):
        if tool_choice in ("auto", "none", "required"):
            return "auto" if tool_choice == "auto" else tool_choice
        return {"type": "function", "name": tool_choice}
    mapping = _json_mapping(tool_choice)
    if mapping is None:
        return tool_choice
    choice_type = mapping.get("type")
    if choice_type == "auto":
        return "auto"
    if choice_type == "none":
        return "none"
    if choice_type == "any":
        return "required"
    if choice_type == "tool":
        name = mapping.get("name")
        if isinstance(name, str) and name:
            return {"type": "function", "name": name}
    return tool_choice


def _anthropic_thinking_to_reasoning(thinking: AnthropicThinkingConfig | JsonValue | None) -> ResponsesReasoning | None:
    if thinking is None:
        return None
    if isinstance(thinking, AnthropicThinkingConfig):
        thinking_type = thinking.type
    else:
        mapping = _json_mapping(thinking)
        if mapping is None:
            return None
        raw_type = mapping.get("type")
        thinking_type = raw_type if isinstance(raw_type, str) else None
    if thinking_type == "disabled":
        return None
    if thinking_type == "enabled":
        return ResponsesReasoning(effort="medium")
    return None


class AnthropicUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    input_tokens: int = 0
    output_tokens: int = 0


class AnthropicContentBlock(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    text: str | None = None
    id: str | None = None
    name: str | None = None
    input: JsonValue | None = None


class AnthropicMessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    model: str
    content: list[AnthropicContentBlock]
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: AnthropicUsage


def anthropic_message_from_chat_completion(chat: Any, *, model: str) -> AnthropicMessageResponse:
    response_id = getattr(chat, "id", None) or f"msg_{time.time_ns()}"
    content_blocks: list[AnthropicContentBlock] = []
    stop_reason: str | None = "end_turn"
    usage = _anthropic_usage_from_chat(chat)
    choices = getattr(chat, "choices", None) or []
    if choices:
        choice = choices[0]
        finish_reason = getattr(choice, "finish_reason", None)
        stop_reason = _anthropic_stop_reason(finish_reason)
        message = getattr(choice, "message", None)
        text = getattr(message, "content", None) if message is not None else None
        if isinstance(text, str) and text:
            content_blocks.append(AnthropicContentBlock(type="text", text=text))
        tool_calls = getattr(message, "tool_calls", None) if message is not None else None
        if tool_calls:
            for tool_call in tool_calls:
                tool_id = getattr(tool_call, "id", None)
                function = getattr(tool_call, "function", None)
                name = getattr(function, "name", None) if function is not None else None
                arguments = getattr(function, "arguments", None) if function is not None else None
                content_blocks.append(
                    AnthropicContentBlock(
                        type="tool_use",
                        id=tool_id,
                        name=name,
                        input=_parse_json_object(arguments),
                    )
                )
    if not content_blocks:
        content_blocks.append(AnthropicContentBlock(type="text", text=""))
    return AnthropicMessageResponse(
        id=response_id,
        model=model,
        content=content_blocks,
        stop_reason=stop_reason,
        usage=usage,
    )


def _anthropic_usage_from_chat(chat: Any) -> AnthropicUsage:
    usage = getattr(chat, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", None) if usage is not None else None
    output_tokens = getattr(usage, "completion_tokens", None) if usage is not None else None
    return AnthropicUsage(
        input_tokens=input_tokens if isinstance(input_tokens, int) else 0,
        output_tokens=output_tokens if isinstance(output_tokens, int) else 0,
    )


def _anthropic_stop_reason(finish_reason: str | None) -> str | None:
    if finish_reason == "tool_calls":
        return "tool_use"
    if finish_reason == "length":
        return "max_tokens"
    if finish_reason == "content_filter":
        return "stop_sequence"
    return "end_turn"


def _parse_json_object(value: str | None) -> JsonValue:
    if not isinstance(value, str) or not value:
        return {}
    try:
        parsed = json.loads(value)
    except ValueError:
        return {}
    return parsed if is_json_mapping(parsed) else {}


async def stream_anthropic_messages(
    stream: AsyncIterator[str],
    *,
    model: str,
) -> AsyncIterator[str]:
    """Convert Responses SSE events to Anthropic Messages SSE events."""

    message_id = f"msg_{time.time_ns()}"
    input_tokens = 0
    output_tokens = 0
    content_started = False
    text_index: int | None = None
    tool_index_by_key: dict[str, int] = {}
    next_index = 0
    completed = False

    def event(event_type: str, payload: Mapping[str, JsonValue]) -> str:
        data = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        return f"event: {event_type}\ndata: {data}\n\n"

    yield event(
        "message_start",
        {
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [],
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        },
    )

    async for line in stream:
        payload = parse_sse_data_json(line)
        if not payload:
            continue
        event_type = payload.get("type")

        if event_type == "response.output_text.delta":
            delta = payload.get("delta")
            if not isinstance(delta, str):
                continue
            if text_index is None:
                text_index = next_index
                next_index += 1
                content_started = True
                yield event(
                    "content_block_start",
                    {
                        "type": "content_block_start",
                        "index": text_index,
                        "content_block": {"type": "text", "text": ""},
                    },
                )
            yield event(
                "content_block_delta",
                {"type": "content_block_delta", "index": text_index, "delta": {"type": "text_delta", "text": delta}},
            )
            continue

        tool_delta = _responses_tool_delta(payload)
        if tool_delta is not None:
            key, tool_id, name, arguments = tool_delta
            index = tool_index_by_key.get(key)
            if index is None:
                index = next_index
                next_index += 1
                tool_index_by_key[key] = index
                yield event(
                    "content_block_start",
                    {
                        "type": "content_block_start",
                        "index": index,
                        "content_block": {
                            "type": "tool_use",
                            "id": tool_id or key,
                            "name": name or "tool",
                            "input": {},
                        },
                    },
                )
            if arguments:
                yield event(
                    "content_block_delta",
                    {
                        "type": "content_block_delta",
                        "index": index,
                        "delta": {"type": "input_json_delta", "partial_json": arguments},
                    },
                )
            continue

        if event_type in ("response.completed", "response.incomplete"):
            response = _json_mapping(payload.get("response"))
            usage = _json_mapping(response.get("usage")) if response is not None else None
            if usage is not None:
                raw_input = usage.get("input_tokens")
                raw_output = usage.get("output_tokens")
                input_tokens = raw_input if isinstance(raw_input, int) else input_tokens
                output_tokens = raw_output if isinstance(raw_output, int) else output_tokens
            break

        if event_type in ("response.failed", "error"):
            yield _anthropic_error_event(payload)
            completed = True
            break

    if text_index is None and not content_started and not tool_index_by_key:
        text_index = next_index
        next_index += 1
        yield event(
            "content_block_start",
            {"type": "content_block_start", "index": text_index, "content_block": {"type": "text", "text": ""}},
        )
    for index in range(next_index):
        yield event("content_block_stop", {"type": "content_block_stop", "index": index})
    if not completed:
        stop_reason = "tool_use" if tool_index_by_key else "end_turn"
        yield event(
            "message_delta",
            {
                "type": "message_delta",
                "delta": {"stop_reason": stop_reason, "stop_sequence": None},
                "usage": {"output_tokens": output_tokens},
            },
        )
        yield event("message_stop", {"type": "message_stop"})


def iter_anthropic_messages_from_chat_chunks(lines: Iterable[str]) -> Iterable[str]:
    """Best-effort OpenAI chat-SSE to Anthropic SSE adapter for tests/tools."""

    for line in lines:
        payload = parse_sse_data_json(line)
        if payload is None:
            continue
        yield format_sse_data(payload)


def _anthropic_error_event(payload: Mapping[str, JsonValue]) -> str:
    error = payload.get("error")
    if not isinstance(error, Mapping):
        response = payload.get("response")
        if isinstance(response, Mapping):
            error = response.get("error")
    if not isinstance(error, Mapping):
        error = {"message": "Upstream error", "type": "api_error"}
    message = error.get("message") if isinstance(error.get("message"), str) else "Upstream error"
    error_type = error.get("type") if isinstance(error.get("type"), str) else "api_error"
    data = {"type": "error", "error": {"type": error_type, "message": message}}
    return f"event: error\ndata: {json.dumps(data, ensure_ascii=True, separators=(',', ':'))}\n\n"


def _responses_tool_delta(payload: Mapping[str, JsonValue]) -> tuple[str, str | None, str | None, str | None] | None:
    if not _is_tool_event(payload):
        return None
    candidate = _tool_candidate(payload)
    call_id = _first_str(candidate.get("call_id"), candidate.get("tool_call_id"), candidate.get("id"))
    item_id = _first_str(candidate.get("item_id"), candidate.get("id"))
    item = _json_mapping(candidate.get("item"))
    if item is not None:
        call_id = call_id or _first_str(item.get("call_id"), item.get("id"))
        item_id = item_id or _first_str(item.get("id"), item.get("call_id"))
    name = _first_str(candidate.get("name"), candidate.get("tool_name"))
    arguments = candidate.get("arguments") if isinstance(candidate.get("arguments"), str) else None
    delta = candidate.get("delta")
    if isinstance(delta, str) and arguments is None:
        arguments = delta
    delta_mapping = _json_mapping(delta)
    if delta_mapping is not None:
        name = name or _first_str(delta_mapping.get("name"))
        if arguments is None and isinstance(delta_mapping.get("arguments"), str):
            arguments = cast(str, delta_mapping.get("arguments"))
        function = _json_mapping(delta_mapping.get("function"))
        if function is not None:
            name = name or _first_str(function.get("name"))
            if arguments is None and isinstance(function.get("arguments"), str):
                arguments = cast(str, function.get("arguments"))
    function = _json_mapping(candidate.get("function"))
    if function is not None:
        name = name or _first_str(function.get("name"))
        if arguments is None and isinstance(function.get("arguments"), str):
            arguments = cast(str, function.get("arguments"))
    if item is not None:
        name = name or _first_str(item.get("name"))
        if arguments is None and isinstance(item.get("arguments"), str):
            arguments = cast(str, item.get("arguments"))
    key = call_id or item_id or name
    if key is None:
        return None
    return key, call_id or item_id, name, arguments


def _is_tool_event(payload: Mapping[str, JsonValue]) -> bool:
    event_type = payload.get("type")
    if isinstance(event_type, str) and ("function_call" in event_type or "tool_call" in event_type):
        return True
    item = _json_mapping(payload.get("item"))
    if item is not None:
        item_type = item.get("type")
        if isinstance(item_type, str) and ("function" in item_type or "tool" in item_type):
            return True
    return any(key in payload for key in ("call_id", "tool_call_id", "arguments"))


def _tool_candidate(payload: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    item = _json_mapping(payload.get("item"))
    if item is not None and payload.get("type") in {"response.output_item.added", "response.output_item.done"}:
        return item
    return payload


def _first_str(*values: JsonValue) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None
