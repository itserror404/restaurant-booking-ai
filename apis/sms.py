#Mock SMS API for sending confirmation messages.

import random
from typing import Dict, Any


SMS_FAILURE_RATE = 0.03  # 3% random failure rate
MESSAGE_ID_MIN = 10000
MESSAGE_ID_MAX = 99999

# Simulate random failures or forced failure
def send_sms(phone: str, message: str, simulate_failure: bool = False) -> Dict[str, Any]:

    if simulate_failure or phone == "555-SMS-FAIL" or random.random() < SMS_FAILURE_RATE:
        return {
            "success": False,
            "error": "SMS service temporarily unavailable.",
            "message_id": None
        }

    message_id = f"SMS-{random.randint(MESSAGE_ID_MIN, MESSAGE_ID_MAX)}"

    print(f"\n{'='*60}")
    print(f"SMS SENT SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"To: {phone}")
    print(f"Message ID: {message_id}")
    print(f"\nMessage:")
    print(f"{message}")
    print(f"{'='*60}\n")

    return {
        "success": True,
        "message_id": message_id
    }
