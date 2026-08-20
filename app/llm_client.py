import os
from typing import Tuple, Optional

from app.prompt import SYSTEM_PROMPT
from app.store import get_session
from app.booking import simulate_booking
from app import mock_agent

MODEL = "gemini-2.5-flash"


def _use_real_llm() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


async def generate_reply(session_id: str, user_message: str, username: Optional[str] = None) -> Tuple[str, bool]:
    """Returns (reply_text, should_end)."""
    if not _use_real_llm():
        return await mock_agent.generate_reply(session_id, user_message, username)
    return await _generate_reply_real(session_id, user_message, username)


def _book_site_visit_declaration():
    from google.genai import types

    return types.FunctionDeclaration(
        name="book_site_visit",
        description=(
            "Attempt to book a site visit to Northstar One (Sector 79, Gurugram) for the "
            "customer. Only call this once you have all four fields confirmed with the "
            "customer."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "date": types.Schema(type=types.Type.STRING, description="Requested visit date, as the customer said it"),
                "time": types.Schema(type=types.Type.STRING, description="Requested visit time window, as the customer said it"),
                "name": types.Schema(type=types.Type.STRING, description="Customer's name"),
                "phone": types.Schema(type=types.Type.STRING, description="Customer's phone number"),
            },
            required=["date", "time", "name", "phone"],
        ),
    )


def _build_contents(messages):
    from google.genai import types

    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
    return contents


async def _generate_reply_real(session_id: str, user_message: str, username: Optional[str] = None) -> Tuple[str, bool]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    session = get_session(session_id)
    session["messages"].append({"role": "user", "content": user_message})

    contents = _build_contents(session["messages"])
    tool = types.Tool(function_declarations=[_book_site_visit_declaration()])
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[tool],
        max_output_tokens=600,
    )

    while True:
        response = client.models.generate_content(model=MODEL, contents=contents, config=config)
        parts = response.candidates[0].content.parts or []
        function_calls = [p.function_call for p in parts if p.function_call]
        text_parts = [p.text for p in parts if p.text]

        if not function_calls:
            reply_text = "\n".join(text_parts).strip()
            session["messages"].append({"role": "assistant", "content": reply_text})
            should_end = _looks_like_ending(reply_text)
            return reply_text, should_end

        # Model turn included a function call — replay it, execute it, feed the result back.
        contents.append(types.Content(role="model", parts=parts))

        function_response_parts = []
        for fc in function_calls:
            if fc.name == "book_site_visit":
                args = dict(fc.args)
                result = await simulate_booking(
                    args.get("date"), args.get("time"), args.get("name"), args.get("phone"),
                    session_id=session_id, username=username,
                )
                sv = session["state"]["site_visit"]
                sv["date"], sv["time"] = args.get("date"), args.get("time")
                sv["status"] = "booked" if result["success"] else "failed"
                session["state"]["name"] = args.get("name")
                session["state"]["phone"] = args.get("phone")
                function_response_parts.append(
                    types.Part.from_function_response(name=fc.name, response={"result": result})
                )
        contents.append(types.Content(role="user", parts=function_response_parts))


def _looks_like_ending(text: str) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in ["have a great day", "take care", "won't reach out again", "good day"])