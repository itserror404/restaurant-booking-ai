#LangGraph workflow for the restaurant booking agent.
#Defines the workflow, nodes, and routing logic.


from langgraph.graph import StateGraph, END
from agent.state import BookingState
from agent.nodes import (
    router_node,
    collect_info_node,
    should_continue_collecting,
    confirm_node,
    handle_confirmation_node,
    check_confirmation_routing,
    create_booking_node,
    handle_booking_error_node,
    send_sms_node,
    handle_sms_error_node
)

#Route based on booking creation success.
def check_booking_success(state: BookingState) -> str:
    booking_ref = state.get("booking_ref")
    if booking_ref:
        return "send_sms"
    else:
        return "handle_booking_error"


#Route based on SMS sending success.
def check_sms_success(state: BookingState) -> str:
    last_message = state["messages"][-1].content
    if "sent a confirmation SMS" in last_message:
        return END
    else:
        return "handle_sms_error"


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph state machine.

    Graph flow:
    START → greet → collect_info → [all fields filled?]
                         ↑              ↓ yes
                         └─── no ───────┘
                                        ↓
                                    confirm → [user confirms?]
                                        ↑          ↓ yes
                                        └── no ────┘
                                                   ↓
                                            create_booking → [success?]
                                                   ↓ yes         ↓ no
                                                send_sms    handle_booking_error → END
                                                   ↓
                                              [success?]
                                         ↓ yes         ↓ no
                                        END      handle_sms_error → END
    """

    # Create the graph
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("router", lambda state: state)  # Dummy node, routing done via conditional edge
    workflow.add_node("collect_info", collect_info_node)
    workflow.add_node("confirm", confirm_node)
    workflow.add_node("handle_confirmation", handle_confirmation_node)
    workflow.add_node("create_booking", create_booking_node)
    workflow.add_node("send_sms", send_sms_node)
    workflow.add_node("handle_booking_error", handle_booking_error_node)
    workflow.add_node("handle_sms_error", handle_sms_error_node)

    # Set entry point - router decides where to go
    workflow.set_entry_point("router")

    # Router conditional edge
    workflow.add_conditional_edges(
        "router",
        router_node,
        {
            "collect_info": "collect_info",
            "handle_confirmation": "handle_confirmation"
        }
    )

    # From collect_info: check if all fields collected
    workflow.add_conditional_edges(
        "collect_info",
        should_continue_collecting,
        {
            "collect": END,              # Exit graph, wait for user to provide more info
            "confirm": "confirm"         # All info collected, move to confirmation
        }
    )

    # After confirm, exit and wait for user response
    workflow.add_edge("confirm", END)

    # From handle_confirmation: proceed or collect more
    workflow.add_conditional_edges(
        "handle_confirmation",
        check_confirmation_routing,
        {
            "proceed": "create_booking",
            "collect": END  # Exit to collect more changes from user
        }
    )

    # Conditional edge: booking success or failure
    workflow.add_conditional_edges(
        "create_booking",
        check_booking_success,
        {
            "send_sms": "send_sms",
            "handle_booking_error": "handle_booking_error"
        }
    )

    # Conditional edge: SMS success or failure
    workflow.add_conditional_edges(
        "send_sms",
        check_sms_success,
        {
            END: END,
            "handle_sms_error": "handle_sms_error"
        }
    )

    # Error handlers end the conversation
    workflow.add_edge("handle_booking_error", END)
    workflow.add_edge("handle_sms_error", END)

    # Compile the graph
    return workflow.compile()
