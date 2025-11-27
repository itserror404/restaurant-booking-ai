#Node functions for the restaurant booking agent.
#Each node handles a specific part of the booking workflow.

import os
from typing import Optional, Literal
from datetime import datetime, timedelta
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field
from langfuse.langchain import CallbackHandler

from agent.state import BookingState
from apis.booking import create_booking
from apis.sms import send_sms

# Load environment variables
load_dotenv()

# Initialize LangFuse callback handler
langfuse_handler = CallbackHandler()

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
    temperature=0.7
)


# ===== Pydantic Models for Structured Output =====

#Structured output for booking information extraction.
class BookingInfo(BaseModel):
    restaurant_name: Optional[str] = Field(None, description="Name of the restaurant")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Time in HH:MM 24-hour format")
    party_size: Optional[int] = Field(None, description="Number of people")
    customer_name: Optional[str] = Field(None, description="Customer's full name")
    phone: Optional[str] = Field(None, description="Phone number")
    response_message: str = Field(
        description="What to say to the user. IMPORTANT: Just acknowledge what you collected and ask for missing info. DO NOT say the booking is confirmed or successful - that happens later."
    )


#Structured output for confirmation interpretation.
class ConfirmationResponse(BaseModel):
    user_wants_to_proceed: bool = Field(
        description="True if user confirmed (yes, correct, looks good, etc.), False if user wants changes"
    )
    requested_changes: Optional[str] = Field(
        None,
        description="What the user wants to change, if anything"
    )


# ===== Node Functions =====

def greet_node(state: BookingState) -> BookingState:

    greeting = (
        "Hello! I'm your restaurant booking assistant.\n\n"
        "I can help you make a reservation. I'll need to collect a few details:\n"
        "- Restaurant name\n"
        "- Date and time\n"
        "- Party size (number of people)\n"
        "- Your name\n"
        "- Your phone number\n\n"
        "Let's get started! What restaurant would you like to book?"
    )

    return {
        "messages": [AIMessage(content=greeting)],
        "all_info_collected": False,
        "awaiting_confirmation": False
    }

#Route to appropriate node
def router_node(state: BookingState) -> str:

    if state.get("awaiting_confirmation"):
        return "handle_confirmation"
    else:
        return "collect_info"

#Collect booking information 
def collect_info_node(state: BookingState) -> BookingState:


    # Get current date for context
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    day_of_week = today.strftime("%A")
    today_full = today.strftime("%A, %B %d, %Y")

    # system prompt
    system_prompt = f"""You are a friendly restaurant booking assistant. Today is {today_full}.

DATES: "today"={today_str}, "tomorrow"={(today + timedelta(days=1)).strftime('%Y-%m-%d')}, "next week [day]"=7+ days out. Format: YYYY-MM-DD.



Your job is to extract booking information from the user's messages and ask for anything that's missing.

COLLECT IN ORDER (one at a time):
1. Restaurant → 2. Date → 3. Time → 4. Party size → 5. Name → 6. Phone


Guidelines:
- Extract information naturally from conversation
- When you ask "What time?" and user says just a number (1-12), interpret as PM like "2" = 14:00, "7" = 19:00, "10" = 22:00 etc
- For cases like "2pm" or "14:00", use as-is
- Question unusual times: "2am is unusual. Did you mean 2pm?"
- ACCEPT bookings for today ({today_str}) and future dates
- ONLY REJECT dates that are actually in the past (before {today_str})
- If date is in the past (before {today_str}), say: "That date has already passed. Please choose a future date."
- For dates 6+ months out, confirm: "Just to confirm, that's [month/year] - quite a ways out. Is that correct?"
- For dates within normal booking range (next few months), just accept them naturally without comment
- Don't assume meal type (breakfast/lunch/dinner)
- Ensure party size is reasonable (1-20 people)
- Handle updates gracefully (if user says "actually make it 8pm", update the time)
- Ask for the NEXT missing field in the sequence, one at a time

CRITICAL: When user says "change X to Y", extract the NEW value for X in proper format.
Example: "change time to 7pm" → extract time="19:00" (not a description)
For fields not mentioned, return null.


Current booking information:
- Restaurant: {state.get('restaurant_name') or 'MISSING'}
- Date: {state.get('date') or 'MISSING'}
- Time: {state.get('time') or 'MISSING'}
- Party size: {state.get('party_size') or 'MISSING'}
- Name: {state.get('customer_name') or 'MISSING'}
- Phone: {state.get('phone') or 'MISSING'}

"""

    # Build messages for LLM
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    # Call LLM with structured output
    llm_with_structure = llm.with_structured_output(BookingInfo)
    response: BookingInfo = llm_with_structure.invoke(messages, config={"callbacks": [langfuse_handler]})

    # Update state with extracted information (only update non-null values)
    updates = {
        "messages": [AIMessage(content=response.response_message)]
    }

    if response.restaurant_name:
        updates["restaurant_name"] = response.restaurant_name
    if response.date:
        updates["date"] = response.date
    if response.time:
        updates["time"] = response.time
    if response.party_size:
        updates["party_size"] = response.party_size
    if response.customer_name:
        updates["customer_name"] = response.customer_name
    if response.phone:
        updates["phone"] = response.phone

    return updates

# check if all required fields are filled
def should_continue_collecting(state: BookingState) -> Literal["confirm", "collect"]:

    required_fields = [
        state.get("restaurant_name"),
        state.get("date"),
        state.get("time"),
        state.get("party_size"),
        state.get("customer_name"),
        state.get("phone")
    ]

    all_filled = all(field is not None for field in required_fields)


    if all_filled:
        return "confirm"
    else:
        return "collect"

#show all collected details and ask for user confirmation
def confirm_node(state: BookingState) -> BookingState:


    confirmation_message = f"""Great! Let me confirm the details of your booking:

Restaurant: {state['restaurant_name']}
Date: {state['date']}
Time: {state['time']}
Party size: {state['party_size']} people
Name: {state['customer_name']}
Phone: {state['phone']}

Does everything look correct? (You can say 'yes' to confirm, or let me know if you'd like to change anything)"""

    return {
        "messages": [AIMessage(content=confirmation_message)],
        "all_info_collected": True,
        "awaiting_confirmation": True
    }

#handle user's confirmation response
def handle_confirmation_node(state: BookingState) -> BookingState:


    system_prompt = """Interpret the user's response to booking confirmation.

They were shown booking details and asked if everything looks correct.

- If they confirm (yes, correct, looks good, yep, etc.) → user_wants_to_proceed = True, requested_changes = null
- If they say "no" without specifying changes → user_wants_to_proceed = False, requested_changes = "Please specify what changes you would like to make to the booking."
- If they want specific changes (change time, different restaurant, etc.) → user_wants_to_proceed = False, requested_changes = describe what they want to change
- If unclear/uncertain ("maybe", "i guess", "not sure", "um") → user_wants_to_proceed = False, requested_changes = "I need a clear yes or no. Do the booking details look correct to you?"

ALWAYS provide a helpful requested_changes message when user_wants_to_proceed = False."""

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    llm_with_structure = llm.with_structured_output(ConfirmationResponse)
    response: ConfirmationResponse = llm_with_structure.invoke(messages, config={"callbacks": [langfuse_handler]})


    # If user didn't confirm, provide helpful message
    if not response.user_wants_to_proceed and response.requested_changes:
        return {
            "user_confirmed": False,
            "awaiting_confirmation": False,  # Go back to collect mode
            "messages": [AIMessage(content=response.requested_changes)]
        }
    else:
        return {
            "user_confirmed": response.user_wants_to_proceed,
            "awaiting_confirmation": False
        }


#Route based on user confirmation.
def check_confirmation_routing(state: BookingState) -> Literal["proceed", "collect"]:
    if state.get("user_confirmed"):
        return "proceed"
    else:
        return "collect"

#Call the mock booking API to create the reservation.
def create_booking_node(state: BookingState) -> BookingState:


    result = create_booking(
        restaurant=state["restaurant_name"],
        date=state["date"],
        time=state["time"],
        party_size=state["party_size"],
        name=state["customer_name"],
        phone=state["phone"]
    )

    if result["success"]:
        updates = {
            "booking_ref": result["booking_ref"],
            "messages": [AIMessage(content=f"Perfect! I've created your booking. Reference: {result['booking_ref']}")]
        }
        return updates
    else:
        # Will be handled by error node
        return {"booking_ref": None}


def handle_booking_error_node(state: BookingState) -> BookingState:
    """Handle booking API failures with retry and graceful error message."""

    # Retry once
    result = create_booking(
        restaurant=state["restaurant_name"],
        date=state["date"],
        time=state["time"],
        party_size=state["party_size"],
        name=state["customer_name"],
        phone=state["phone"]
    )

    if result["success"]:
        return {
            "booking_ref": result["booking_ref"],
            "messages": [AIMessage(content=f"Success! Your booking has been created. Reference: {result['booking_ref']}")]
        }
    else:
        error_message = f"""I'm having trouble creating your booking right now. This might be a temporary issue with the booking system.

I've recorded your details:
- Restaurant: {state['restaurant_name']}
- Date: {state['date']} at {state['time']}
- Party size: {state['party_size']}
- Name: {state['customer_name']}
- Phone: {state['phone']}

Can I have someone from the restaurant call you back to confirm the booking?"""

        return {
            "messages": [AIMessage(content=error_message)],
            "conversation_complete": True
        }


#Send SMS confirmation to the customer.
def send_sms_node(state: BookingState) -> BookingState:

    sms_message = f"""Your booking is confirmed!

Restaurant: {state['restaurant_name']}
Date: {state['date']}
Time: {state['time']}
Party: {state['party_size']} people
Ref: {state['booking_ref']}

See you there! Reply CANCEL to modify."""

    result = send_sms(phone=state["phone"], message=sms_message)

    if result["success"]:
        return {
            "messages": [AIMessage(content="I've sent a confirmation SMS to your phone. Your booking is all set!")],
            "conversation_complete": True
        }
    else:
        # Will be handled by error node
        return {}


#Handle SMS API failures and inform the user that the booking is confirmed.
def handle_sms_error_node(state: BookingState) -> BookingState:

    error_message = f"""Your booking is confirmed!

However, I couldn't send the confirmation SMS. Please save this information:

Restaurant: {state['restaurant_name']}
Date: {state['date']}
Time: {state['time']}
Party size: {state['party_size']}
Booking Reference: {state['booking_ref']}

Please screenshot or write down your booking reference: {state['booking_ref']}"""

    return {
        "messages": [AIMessage(content=error_message)],
        "conversation_complete": True
    }
