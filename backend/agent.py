import json
import os
from openai import OpenAI
from scheduler import (
    get_available_doctors,
    book_appointment,
    cancel_appointment,
    get_patient_appointments
)
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Tool definitions for GPT-4o ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_available_doctors",
            "description": "Get list of all doctors and their available appointment slots",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book an appointment for a patient with a doctor at a specific time slot",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_phone": {"type": "string", "description": "Patient phone number"},
                    "doctor_id": {"type": "integer", "description": "Doctor ID"},
                    "slot": {"type": "string", "description": "Time slot in format YYYY-MM-DD HH:MM"},
                    "language": {"type": "string", "description": "Language code: en, hi, or ta"}
                },
                "required": ["patient_phone", "doctor_id", "slot", "language"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment by appointment ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Appointment ID to cancel"}
                },
                "required": ["appointment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_appointments",
            "description": "Get all upcoming confirmed appointments for a patient",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_phone": {"type": "string", "description": "Patient phone number"}
                },
                "required": ["patient_phone"]
            }
        }
    }
]

TOOL_MAP = {
    "get_available_doctors": get_available_doctors,
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "get_patient_appointments": get_patient_appointments
}

SYSTEM_PROMPT = """You are a helpful clinical appointment booking assistant for an Indian healthcare platform.
You can speak English, Hindi, and Tamil. Always detect and match the patient's language.

You help patients:
- Book new appointments with doctors
- View their existing appointments  
- Cancel or reschedule appointments
- Understand doctor availability

Rules:
- Always confirm details before booking (doctor name, time, date)
- If a slot is taken, immediately offer alternatives
- Be warm, professional, and concise (this is a voice conversation)
- Never make up doctor names or slots — always use the tools
- For Hindi responses use Devanagari script, for Tamil use Tamil script
- Keep responses short — under 3 sentences where possible (voice UX)

Current patient phone: {patient_phone}
Detected language: {language}
"""

def run_agent(messages: list, patient_phone: str, language: str) -> str:
    """Run one turn of the agent, handling tool calls automatically."""
    
    system = SYSTEM_PROMPT.format(patient_phone=patient_phone, language=language)
    full_messages = [{"role": "system", "content": system}] + messages

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=full_messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # No tool call — return the text response
        if not message.tool_calls:
            return message.content

        # Handle tool calls
        full_messages.append(message)

        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            print(f"[TOOL CALL] {fn_name}({fn_args})")  # visible reasoning trace

            fn = TOOL_MAP.get(fn_name)
            result = fn(**fn_args) if fn else {"error": "Unknown tool"}

            print(f"[TOOL RESULT] {result}")

            full_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })