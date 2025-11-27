#Test helper functions for restaurant booking agent tests.

from agent.state import BookingState
from langchain_core.messages import HumanMessage, AIMessage


def create_booking_state(**overrides) -> BookingState:
    """Create a BookingState with default values and optional overrides.
    
    Args:
        **overrides: Fields to override from defaults
        
    Returns:
        BookingState with defaults applied
    """
    defaults = {
        "messages": [],
        "restaurant_name": None,
        "date": None,
        "time": None,
        "party_size": None,
        "customer_name": None,
        "phone": None,
        "booking_ref": None,
        "all_info_collected": False,
        "awaiting_confirmation": False,
        "user_confirmed": False,
        "conversation_complete": False
    }
    
    # Apply overrides
    defaults.update(overrides)
    
    return BookingState(**defaults)


def create_complete_booking_state(**overrides) -> BookingState:
    """Create a BookingState with all required fields filled.
    
    Args:
        **overrides: Fields to override from defaults
        
    Returns:
        Complete BookingState ready for confirmation
    """
    complete_data = {
        "messages": [],
        "restaurant_name": "Mario's Italian",
        "date": "2025-12-01",
        "time": "19:00",
        "party_size": 4,
        "customer_name": "John Doe",
        "phone": "555-1234",
        "booking_ref": None,
        "all_info_collected": True,
        "awaiting_confirmation": False,
        "user_confirmed": False,
        "conversation_complete": False
    }
    
    # Apply overrides
    complete_data.update(overrides)
    
    return BookingState(**complete_data)