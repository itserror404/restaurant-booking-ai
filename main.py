"""
Restaurant Booking Agent - Main Entry Point
Interactive CLI for conversational restaurant bookings.
"""

import os
import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agent.graph import build_graph
from agent.state import BookingState


def print_separator():
    print("\n" + "="*60 + "\n")

#Run the restaurant booking agent 
def run_agent():
    
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file")
        return

    print("\n" + "="*60)
    print("RESTAURANT BOOKING AGENT")
    print("="*60 + "\n")

    # Build the graph
    print("Initializing agent...")
    app = build_graph()
    print("Agent ready!\n")

    # Generate session ID for tracing
    session_id = str(uuid.uuid4())
    print(f"[LANGFUSE] Session ID: {session_id}")

    # Initialize state
    state: BookingState = {
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

  
    greeting = """Hello! I'm your restaurant booking assistant.

I can help you make a reservation. I'll need to collect a few details:
- Restaurant name
- Date and time
- Party size (number of people)
- Your name
- Your phone number

Let's get started! What restaurant would you like to book?"""

    print("Agent:", greeting)

    # Main conversation loop
    while True:
        print_separator()

        # Get user input
        user_input = input("You: ").strip()

        if not user_input:
            print("(Please enter a message)")
            continue

        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
            print("\nThank you for using the restaurant booking agent! Goodbye!\n")
            break

        # Add user message to state
        state["messages"].append(HumanMessage(content=user_input))

        # Process with agent
        try:
            state = app.invoke(state)

            # Get agent response
            agent_response = state["messages"][-1].content
            print(f"\nAgent: {agent_response}")

            # Check if conversation ended
            if state.get("conversation_complete"):
                    print_separator()
                    print("Booking complete and saved!")
                    if state.get("booking_ref"):
                        print(f"Your booking reference is: {state['booking_ref']}")

                    # Ask if user wants to make another booking
                    print("\nYour current booking is confirmed.")
                    print("Would you like to make ANOTHER booking? (type 'yes' or 'no')")
                    response = input("You: ").strip().lower()

                    if response in ["cancel", "cancel booking", "undo"]:
                        print("\nNote: Your booking is already confirmed and saved.")
                        print("To cancel or modify, please contact the restaurant directly with your reference number.")
                        print("\nWould you like to make a different booking instead? (yes/no)")
                        response = input("You: ").strip().lower()

                    if response in ["yes", "y", "sure", "ok"]:
                        # Log session completion
                        print(f"[LANGFUSE] Session {session_id}: COMPLETED")
                        
                        # Reset state for new booking
                        session_id = str(uuid.uuid4())  # New session ID
                        print(f"[LANGFUSE] New Session ID: {session_id}")
                        state = {
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
                        print("\nAgent:", greeting)
                    else:
                        # Log session completion
                        print(f"[LANGFUSE] Session {session_id}: COMPLETED")
                        print("\nThank you for using the restaurant booking agent! Goodbye!\n")
                        break

        except KeyboardInterrupt:
            print("\n\nBooking cancelled. Goodbye!\n")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'exit' to quit.")


def main():
    """Main entry point."""
    try:
        run_agent()
    except KeyboardInterrupt:
        print("\n\nGoodbye!\n")
    except Exception as e:
        print(f"\nFatal error: {e}\n")


if __name__ == "__main__":
    main()
