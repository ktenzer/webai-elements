from uuid import UUID
import json, aiohttp
from string import Template
from typing import Any, Dict

from webai_element_sdk.comms.messages import Frame
from webai_element_sdk.element import Context, Element
from webai_element_sdk.element.variables import ElementInputs, Input
from webai_element_sdk.element.settings import (
    ElementSettings,
    TextSetting,
    BoolSetting,
    NumberSetting,
)

# Globals
ENDPOINT: str
HTTP_METHOD: str
HEADERS: Dict[str, str]
BODY_TEMPLATE: Template
TIMEOUT_SEC: int

# Settings
class Settings(ElementSettings):
    url = TextSetting(
        name="url",
        display_name="Endpoint URL",
        default="https://slack.com/api/chat.postMessage",
        description="Target REST endpoint (e.g. Slack, Discord, or any webhook).",
        required=True,
    )

    method = TextSetting(
        name="method",
        display_name="HTTP Method",
        default="POST",
        description="HTTP verb to use when sending the request.",
        valid_values=["GET", "POST", "PUT", "PATCH", "DELETE"],
        hints=["dropdown"],          
        required=True,
    )

    auth_token = TextSetting(
        name="auth_token",
        display_name="Auth token (optional)",
        description="Bearer or other token appended to the Authorization header.",
        default="",
        required=False,
    )

    extra_headers = TextSetting(
        name="extra_headers",
        display_name="Extra headers (JSON object)",
        default="{}",
        description='Additional request headers, e.g. {"X-Custom":"1"}.',
        required=False,
    )

    payload_template = TextSetting(
        name="payload_template",
        display_name="Body template (JSON with $text placeholder)",
        default='{"channel":"a-slack-channel","message":"$message"}',
        description="Rendered with incoming Frame data using $placeholders.",
        required=True,
    )

    timeout_sec = NumberSetting[int](
        name="timeout_sec",
        display_name="Timeout (seconds)",
        default=10,
        description="Request timeout in seconds.",
    )

    log_payload = BoolSetting(
        name="log_payload",
        display_name="Log rendered JSON body",
        default=True,
    )

    enabled = BoolSetting(
        name="enabled",
        display_name="Enable or Disable",
        default=True,
    )

# Inputs
class Inputs(ElementInputs):
    input = Input[Frame]()

# Element definition
element = Element(
    id=UUID("5c62aa25-cee0-4d20-914e-caadb73ae97f"),
    name="rest",
    display_name="REST API",
    description="Send an HTTP request to any REST endpoint using a template body.",
    version="0.1.8",
    settings=Settings(),
    inputs=Inputs(),
)

# Startup
@element.startup
async def startup(ctx: Context[Inputs, None, Settings]):
    global ENDPOINT, HTTP_METHOD, HEADERS, BODY_TEMPLATE, TIMEOUT_SEC

    ENDPOINT = ctx.settings.url.value
    HTTP_METHOD = ctx.settings.method.value
    TIMEOUT_SEC = ctx.settings.timeout_sec.value

    # Parse headers
    try:
        extra = json.loads(ctx.settings.extra_headers.value or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"extra_headers is not valid JSON: {exc}") from exc
    if not isinstance(extra, dict):
        raise ValueError("extra_headers must decode to a JSON object")

    HEADERS = {"Content-Type": "application/json", **extra}
    if ctx.settings.auth_token.value:
        HEADERS["Authorization"] = f"Bearer {ctx.settings.auth_token.value}"

    # Body
    BODY_TEMPLATE = Template(ctx.settings.payload_template.value)

# Shutdown
@element.shutdown
async def shutdown(_: Context[Inputs, None, Settings]):
    print("Generic REST element shutting down")

# Executor
@element.executor
async def run(ctx: Context[Inputs, None, Settings]):
    
    if ctx.settings.enabled.value:
        frame: Frame = ctx.inputs.input.value

        # Map for placeholders
        mapping: Dict[str, Any] = {
            "text": getattr(frame, "text", ""),
            **frame.other_data,
        }

        # Render template
        rendered = BODY_TEMPLATE.safe_substitute(mapping)
        if "$" in rendered:
            print("Unresolved placeholders in body:", rendered)
            return

        # JSON validation
        try:
            body_dict = json.loads(rendered)
        except json.JSONDecodeError as exc:
            print("Body template rendered invalid JSON:", exc)
            return

        if ctx.settings.log_payload.value:
            print("Payload:", body_dict)

        # HTTP request
        req_kwargs = {
            "method": HTTP_METHOD,
            "url": ENDPOINT,
            "headers": HEADERS,
            "timeout": aiohttp.ClientTimeout(total=TIMEOUT_SEC),
        }
        if HTTP_METHOD in {"GET", "DELETE"}:
            req_kwargs["params"] = body_dict
        else:
            req_kwargs["json"] = body_dict

        # Send request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(**req_kwargs) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        print(f"HTTP {resp.status}: {text[:200]} {req_kwargs}")
                    else:
                        print(f"{resp.status} {len(text)} bytes {req_kwargs}")
        except Exception as e:
            print("Network error:", e)