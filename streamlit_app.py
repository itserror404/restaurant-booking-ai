import streamlit as st
import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from agent.graph import build_graph
from agent.state import BookingState

# Load environment variables
load_dotenv()

# PAGE CONFIGURATION

st.set_page_config(
    page_title="Restaurant Booking Agent",
    layout="wide"
)

st.title("Restaurant Booking Agent")
st.write("Interactive AI assistant for restaurant reservations")


# SESSION STATE INITIALIZATION
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'booking_state' not in st.session_state:
    st.session_state.booking_state = {
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

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
    st.session_state.app = None

# AGENT INITIALIZATION

@st.cache_resource
def initialize_agent():
    """Initialize the booking agent."""
    return build_graph()

if not st.session_state.agent_initialized:
    with st.spinner("Initializing booking agent..."):
        st.session_state.app = initialize_agent()
        st.session_state.agent_initialized = True
        
        # Add initial greeting to conversation
        greeting = """Hello! I'm your restaurant booking assistant.

I can help you make a reservation. I'll need to collect a few details:
- Restaurant name
- Date and time
- Party size (number of people)
- Your name
- Your phone number

Let's get started! What restaurant would you like to book?"""
        
        st.session_state.conversation_history.append({
            "role": "assistant", 
            "content": greeting,
            "timestamp": st.session_state.session_id
        })


# SIDEBAR - BOOKING STATUS
with st.sidebar:
    st.header("Booking Status")
    
    booking_info = {
        "Restaurant": st.session_state.booking_state.get("restaurant_name") or "Missing",
        "Date": st.session_state.booking_state.get("date") or "Missing", 
        "Time": st.session_state.booking_state.get("time") or "Missing",
        "Party Size": st.session_state.booking_state.get("party_size") or "Missing",
        "Name": st.session_state.booking_state.get("customer_name") or "Missing",
        "Phone": st.session_state.booking_state.get("phone") or "Missing"
    }
    
    for key, value in booking_info.items():
        if value == "Missing":
            st.write(f"**{key}:** {value}")
        else:
            st.write(f"**{key}:** {value}")
    
    # Booking reference if available
    if st.session_state.booking_state.get("booking_ref"):
        st.success(f"**Booking Confirmed!**\nRef: {st.session_state.booking_state['booking_ref']}")
    
    # Session info
    st.write("---")
    st.caption(f"Session: {st.session_state.session_id[:8]}...")
    st.caption(f"Messages: {len(st.session_state.conversation_history)}")
    
    # Reset button
    if st.button("New Booking"):
        st.session_state.conversation_history = []
        st.session_state.booking_state = {
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
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()


# MAIN CONVERSATION INTERFACE

# Display conversation history
st.header("Conversation")

# Create a container for the conversation
conversation_container = st.container()

with conversation_container:
    for i, message in enumerate(st.session_state.conversation_history):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:  # assistant
            with st.chat_message("assistant"):
                st.write(message["content"])

# USER INPUT 

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to conversation
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_input,
        "timestamp": st.session_state.session_id
    })
    
    # Add to booking state messages
    st.session_state.booking_state["messages"].append(HumanMessage(content=user_input))
    
    # Process with agent
    try:
        with st.spinner("Processing..."):
            # Invoke the agent
            updated_state = st.session_state.app.invoke(st.session_state.booking_state)
            
            # Update booking state
            st.session_state.booking_state = updated_state
            
            # Get agent response
            if updated_state["messages"]:
                agent_response = updated_state["messages"][-1].content
                
                # Add agent response to conversation
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": agent_response,
                    "timestamp": st.session_state.session_id
                })
        
        # Rerun to update the display
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing request: {str(e)}")
        st.error("Please try again or refresh the page.")

