#BookingState definition for the restaurant booking agent.
#Maintains conversation context and booking information.


from typing import TypedDict, Optional, List, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class BookingState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

    # Booking information
    restaurant_name: Optional[str]
    date: Optional[str]
    time: Optional[str]
    party_size: Optional[int]
    customer_name: Optional[str]
    phone: Optional[str]
    booking_ref: Optional[str]

    # Control flags
    all_info_collected: bool
    awaiting_confirmation: bool
    user_confirmed: bool
    conversation_complete: bool
