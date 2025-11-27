#!/usr/bin/env python3
"""
Simple integration test - just verify the system can start and initialize.

Run with: python -m pytest test_simple_integration.py -v
"""

import os
import pytest

# Set dummy API key for testing
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

from agent.graph import build_graph
from agent.state import BookingState
from langchain_core.messages import HumanMessage
from test_helpers import create_booking_state


class TestBasicIntegration:
    """Basic integration tests that don't require real LLM calls."""
    
    def test_graph_can_be_built(self):
        """Test that the graph can be built without errors."""
        graph = build_graph()
        assert graph is not None
    
    def test_initial_state_can_be_created(self):
        """Test that initial state can be created."""
        state = create_booking_state(messages=[HumanMessage(content="Hello")])
        assert state is not None
        assert len(state["messages"]) == 1
    
    def test_imports_work_correctly(self):
        """Test that all required modules can be imported."""
        from agent.nodes import (
            greet_node,
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
        from apis.booking import create_booking
        from apis.sms import send_sms
        
        # If we got here, imports worked
        assert True
    
    def test_mock_apis_work(self):
        """Test that mock APIs can be called."""
        from apis.booking import create_booking
        from apis.sms import send_sms
        
        # Test booking API
        booking_result = create_booking(
            restaurant="Test Restaurant",
            date="2025-12-01",
            time="19:00",
            party_size=2,
            name="Test User",
            phone="555-1234"
        )
        
        assert booking_result is not None
        assert "success" in booking_result
        
        # Test SMS API
        sms_result = send_sms(
            phone="555-1234",
            message="Test message"
        )
        
        assert sms_result is not None
        assert "success" in sms_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])