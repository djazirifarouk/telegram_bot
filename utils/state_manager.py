class StateManager:
    """Manage user states for multi-step operations."""
    
    def __init__(self):
        self._states = {}
    
    def get_state(self, user_id: int) -> dict:
        """Get state for a user."""
        return self._states.get(user_id, {})
    
    def set_state(self, user_id: int, state: dict):
        """Set state for a user."""
        self._states[user_id] = state
    
    def update_state(self, user_id: int, updates: dict):
        """Update state for a user."""
        if user_id in self._states:
            self._states[user_id].update(updates)
        else:
            self._states[user_id] = updates
    
    def clear_state(self, user_id: int):
        """Clear state for a user."""
        if user_id in self._states:
            del self._states[user_id]
    
    def has_state(self, user_id: int) -> bool:
        """Check if user has state."""
        return user_id in self._states


# Global state manager instance
state_manager = StateManager()
