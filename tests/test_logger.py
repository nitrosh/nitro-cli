"""Tests for utils/logger.py spinner fallback."""

import threading
from unittest.mock import patch

from nitro.utils.logger import spinner


class TestSpinnerFallback:
    """Tests for spinner() Rich compatibility fallback."""

    def test_spinner_yields_callable(self):
        """spinner() should yield an update function."""
        with spinner("Working...") as update:
            assert callable(update)

    def test_spinner_update_does_not_crash(self):
        """Calling the update function should not raise."""
        with spinner("Working...") as update:
            update("Step 1...")
            update("Step 2...")

    def test_spinner_fallback_on_progress_error(self):
        """spinner() should fall back to info() when Progress raises."""
        with patch(
            "nitro.utils.logger.Progress",
            side_effect=Exception("Rich render failure"),
        ):
            with spinner("Working...") as update:
                assert callable(update)
                update("Still works")

    def test_spinner_fallback_in_thread(self):
        """spinner() should not crash when used in a background thread."""
        result = {"error": None}

        def run():
            try:
                with spinner("Working...") as update:
                    update("From thread")
            except Exception as e:
                result["error"] = e

        thread = threading.Thread(target=run)
        thread.start()
        thread.join(timeout=5)

        assert result["error"] is None, f"Error in thread: {result['error']}"
