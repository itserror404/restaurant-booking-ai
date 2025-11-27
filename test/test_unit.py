#!/usr/bin/env python3
"""
Unit tests for restaurant booking agent nodes.

Run with: python -m pytest test_unit.py -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agent.state import BookingState
from agent.nodes import (
    should_continue_collecting,
    router_node,
    check_confirmation_routing
)
from test_helpers import create_booking_state, create_complete_booking_state


class TestNodeRouting:
    """Test routing logic between nodes."""
    
    def test_should_continue_collecting_all_missing(self):
        """When all fields are missing, should continue collecting."""
        state = create_booking_state()
        
        result = should_continue_collecting(state)
        assert result == "collect"
    
    def test_should_continue_collecting_partial_info(self):
        """When some fields are missing, should continue collecting."""
        state = create_booking_state(
            restaurant_name="Mario's",
            date="2025-12-01",
            time=None,  # Missing
            party_size=4,
            customer_name="John",
            phone=None  # Missing
        )
        
        result = should_continue_collecting(state)
        assert result == "collect"
    
    def test_should_continue_collecting_all_complete(self):
        """When all fields are filled, should move to confirmation."""
        state = create_complete_booking_state(
            customer_name="John Smith"
        )
        
        result = should_continue_collecting(state)
        assert result == "confirm"
    
    def test_router_node_awaiting_confirmation(self):
        """When awaiting confirmation, should route to handle_confirmation."""
        state = create_booking_state(
            awaiting_confirmation=True
        )
        
        result = router_node(state)
        assert result == "handle_confirmation"
    
    def test_router_node_not_awaiting_confirmation(self):
        """When not awaiting confirmation, should route to collect_info."""
        state = BookingState(
            messages=[],
            awaiting_confirmation=False
        )
        
        result = router_node(state)
        assert result == "collect_info"
    
    def test_check_confirmation_routing_confirmed(self):
        """When user confirmed, should proceed to booking."""
        state = create_booking_state(
            user_confirmed=True
        )
        
        result = check_confirmation_routing(state)
        assert result == "proceed"
    
    def test_check_confirmation_routing_not_confirmed(self):
        """When user wants changes, should go back to collect."""
        state = create_booking_state(
            user_confirmed=False
        )
        
        result = check_confirmation_routing(state)
        assert result == "collect"


class TestMockAPIResponses:
    """Test mock API response handling."""
    
    @patch('agent.nodes.create_booking')
    def test_create_booking_node_success(self, mock_create_booking):
        """Test successful booking creation."""
        from agent.nodes import create_booking_node
        
        mock_create_booking.return_value = {
            "success": True,
            "booking_ref": "BK-12345"
        }
        
        state = BookingState(
            messages=[],
            restaurant_name="Mario's",
            date="2025-12-01",
            time="19:00",
            party_size=4,
            customer_name="John Smith",
            phone="555-1234"
        )
        
        result = create_booking_node(state)
        
        assert result["booking_ref"] == "BK-12345"
        assert "Perfect! I've created your booking" in result["messages"][0].content
    
    @patch('agent.nodes.create_booking')
    def test_create_booking_node_failure(self, mock_create_booking):
        """Test booking creation failure."""
        from agent.nodes import create_booking_node
        
        mock_create_booking.return_value = {
            "success": False,
            "error": "System unavailable"
        }
        
        state = BookingState(
            messages=[],
            restaurant_name="Mario's",
            date="2025-12-01",
            time="19:00",
            party_size=4,
            customer_name="John Smith",
            phone="555-1234"
        )
        
        result = create_booking_node(state)
        
        assert result["booking_ref"] is None
    
    @patch('agent.nodes.send_sms')
    def test_send_sms_node_success(self, mock_send_sms):
        """Test successful SMS sending."""
        from agent.nodes import send_sms_node
        
        mock_send_sms.return_value = {
            "success": True,
            "message_id": "SMS-12345"
        }
        
        state = BookingState(
            messages=[],
            restaurant_name="Mario's",
            date="2025-12-01",
            time="19:00",
            party_size=4,
            customer_name="John Smith",
            phone="555-1234",
            booking_ref="BK-12345"
        )
        
        result = send_sms_node(state)
        
        assert "I've sent a confirmation SMS" in result["messages"][0].content
    
    @patch('agent.nodes.send_sms')
    def test_send_sms_node_failure(self, mock_send_sms):
        """Test SMS sending failure."""
        from agent.nodes import send_sms_node
        
        mock_send_sms.return_value = {
            "success": False,
            "error": "SMS service unavailable"
        }
        
        state = BookingState(
            messages=[],
            restaurant_name="Mario's",
            date="2025-12-01",
            time="19:00",
            party_size=4,
            customer_name="John Smith",
            phone="555-1234",
            booking_ref="BK-12345"
        )
        
        result = send_sms_node(state)
        
        # SMS failure returns empty dict to trigger error handler
        assert result == {}


class TestErrorHandling:
    """Test error handling nodes."""
    
    @patch('agent.nodes.create_booking')
    def test_handle_booking_error_retry_success(self, mock_create_booking):
        """Test booking error handler with successful retry."""
        from agent.nodes import handle_booking_error_node
        
        mock_create_booking.return_value = {
            "success": True,
            "booking_ref": "BK-67890"
        }
        
        state = BookingState(
            messages=[],
            restaurant_name="Mario's",
            date="2025-12-01",
            time="19:00",
            party_size=4,
            customer_name="John Smith",
            phone="555-1234"
        )
        
        result = handle_booking_error_node(state)
        
        assert result["booking_ref"] == "BK-67890"
        assert "Success! Your booking has been created" in result["messages"][0].content
    
    @patch('agent.nodes.create_booking')
    def test_handle_booking_error_retry_failure(self, mock_create_booking):
        """Test booking error handler with failed retry."""
        from agent.nodes import handle_booking_error_node
        
        mock_create_booking.return_value = {
            "success": False,
            "error": "System down"
        }
        
        state = BookingState(
            messages=[],
            restaurant_name="Mario's",
            date="2025-12-01",
            time="19:00",
            party_size=4,
            customer_name="John Smith",
            phone="555-1234"
        )
        
        result = handle_booking_error_node(state)
        
        assert "booking_ref" not in result
        assert "I'm having trouble creating your booking" in result["messages"][0].content
        assert "Can I have someone from the restaurant call you back" in result["messages"][0].content
    
    def test_handle_sms_error_node(self):
        """Test SMS error handler provides booking details."""
        from agent.nodes import handle_sms_error_node
        
        state = BookingState(
            messages=[],
            restaurant_name="Mario's",
            date="2025-12-01",
            time="19:00",
            party_size=4,
            customer_name="John Smith",
            phone="555-1234",
            booking_ref="BK-12345"
        )
        
        result = handle_sms_error_node(state)
        
        message = result["messages"][0].content
        assert "Your booking is confirmed!" in message
        assert "couldn't send the confirmation SMS" in message
        assert "BK-12345" in message
        assert "Mario's" in message


class TestStateValidation:
    """Test state management and validation."""
    
    def test_empty_state_fields(self):
        """Test handling of empty state fields."""
        state = BookingState(messages=[])
        
        # All fields should be None or missing
        assert state.get("restaurant_name") is None
        assert state.get("date") is None
        assert state.get("time") is None
        assert state.get("party_size") is None
        assert state.get("customer_name") is None
        assert state.get("phone") is None
        assert state.get("all_info_collected", False) is False
        assert state.get("awaiting_confirmation", False) is False
    
    def test_partial_state_fields(self):
        """Test state with some fields filled."""
        state = BookingState(
            messages=[],
            restaurant_name="Mario's",
            party_size=4
        )
        
        assert state["restaurant_name"] == "Mario's"
        assert state["party_size"] == 4
        assert state.get("date") is None
        assert state.get("time") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])