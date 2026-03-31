# mkg/conftest.py
"""Root conftest for MKG — blocks ROS pytest plugins from interfering."""

import pluggy


# Monkey-patch check_pending to skip launch_testing_ros validation errors
_original_check_pending = pluggy._manager.PluginManager.check_pending


def _patched_check_pending(self):
    try:
        _original_check_pending(self)
    except pluggy._manager.PluginValidationError as e:
        if "launch" in str(e).lower():
            pass  # Ignore ROS launch_testing plugin validation
        else:
            raise


pluggy._manager.PluginManager.check_pending = _patched_check_pending
