#Mock Booking API for restaurant reservations.


import random
from typing import Dict, Any

BOOKING_FAILURE_RATE = 0.05  # 5% random failure rate --> for testing mainly
BOOKING_REF_MIN = 10000
BOOKING_REF_MAX = 99999


def create_booking(
    restaurant: str,
    date: str,
    time: str,
    party_size: int,
    name: str,
    phone: str,
    simulate_failure: bool = False
) -> Dict[str, Any]:

    # Simulate random failures or forced failure for testing 
    if simulate_failure or restaurant == "Test Failure Restaurant" or random.random() < BOOKING_FAILURE_RATE:
        return {
            "success": False,
            "error": "Unable to connect to booking system. Please try again.",
            "booking_ref": None
        }

    # Generate booking reference
    booking_ref = f"BK-{random.randint(BOOKING_REF_MIN, BOOKING_REF_MAX)}"

    print(f"\n{'='*60}")
    print(f"BOOKING CREATED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"Reference: {booking_ref}")
    print(f"Restaurant: {restaurant}")
    print(f"Date: {date}")
    print(f"Time: {time}")
    print(f"Party Size: {party_size}")
    print(f"Name: {name}")
    print(f"Phone: {phone}")
    print(f"{'='*60}\n")

    return {
        "success": True,
        "booking_ref": booking_ref,
        "details": {
            "restaurant": restaurant,
            "date": date,
            "time": time,
            "party_size": party_size,
            "customer_name": name,
            "phone": phone
        }
    }
