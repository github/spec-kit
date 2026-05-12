"""Tests for StepTracker class."""


from infrakit_cli import StepTracker


class TestStepTracker:
    """Test suite for StepTracker class."""

    def test_step_tracker_initialization(self):
        """Test StepTracker initializes with title."""
        tracker = StepTracker("Test Title")
        assert tracker.title == "Test Title"
        assert tracker.steps == []
        assert len(tracker.steps) == 0

    def test_step_tracker_add_step(self):
        """Test adding a step to the tracker."""
        tracker = StepTracker("Test")
        tracker.add("step1", "Test Step 1")

        assert len(tracker.steps) == 1
        assert tracker.steps[0]["key"] == "step1"
        assert tracker.steps[0]["label"] == "Test Step 1"
        assert tracker.steps[0]["status"] == "pending"
        assert tracker.steps[0]["detail"] == ""

    def test_step_tracker_add_multiple_steps(self):
        """Test adding multiple steps."""
        tracker = StepTracker("Test")
        tracker.add("step1", "First Step")
        tracker.add("step2", "Second Step")
        tracker.add("step3", "Third Step")

        assert len(tracker.steps) == 3
        assert tracker.steps[0]["key"] == "step1"
        assert tracker.steps[1]["key"] == "step2"
        assert tracker.steps[2]["key"] == "step3"

    def test_step_tracker_start_step(self):
        """Test starting a step."""
        tracker = StepTracker("Test")
        tracker.add("step1", "Test Step")
        tracker.start("step1", "Starting...")

        assert tracker.steps[0]["status"] == "running"
        assert tracker.steps[0]["detail"] == "Starting..."

    def test_step_tracker_complete_step(self):
        """Test completing a step."""
        tracker = StepTracker("Test")
        tracker.add("step1", "Test Step")
        tracker.complete("step1", "Done!")

        assert tracker.steps[0]["status"] == "done"
        assert tracker.steps[0]["detail"] == "Done!"

    def test_step_tracker_error_step(self):
        """Test marking a step as error."""
        tracker = StepTracker("Test")
        tracker.add("step1", "Test Step")
        tracker.error("step1", "Error occurred")

        assert tracker.steps[0]["status"] == "error"
        assert tracker.steps[0]["detail"] == "Error occurred"

    def test_step_tracker_skip_step(self):
        """Test skipping a step."""
        tracker = StepTracker("Test")
        tracker.add("step1", "Test Step")
        tracker.skip("step1", "Skipped")

        assert tracker.steps[0]["status"] == "skipped"
        assert tracker.steps[0]["detail"] == "Skipped"

    def test_step_tracker_update_nonexistent_step(self):
        """Test updating a non-existent step creates it."""
        tracker = StepTracker("Test")
        tracker.add("step1", "Test Step")

        # Should create a new step when updating non-existent key
        tracker.complete("nonexistent", "Completed")

        assert len(tracker.steps) == 2
        assert tracker.steps[1]["key"] == "nonexistent"
        assert tracker.steps[1]["status"] == "done"

    def test_step_tracker_mixed_statuses(self):
        """Test tracker with mixed step statuses."""
        tracker = StepTracker("Test")
        tracker.add("step1", "First Step")
        tracker.add("step2", "Second Step")
        tracker.add("step3", "Third Step")
        tracker.add("step4", "Fourth Step")

        tracker.complete("step1")
        tracker.error("step2")
        tracker.skip("step3")
        tracker.start("step4")

        assert tracker.steps[0]["status"] == "done"
        assert tracker.steps[1]["status"] == "error"
        assert tracker.steps[2]["status"] == "skipped"
        assert tracker.steps[3]["status"] == "running"

    def test_step_tracker_all_success(self):
        """Test tracker when all steps succeed."""
        tracker = StepTracker("Test")
        tracker.add("step1", "First Step")
        tracker.add("step2", "Second Step")

        tracker.complete("step1")
        tracker.complete("step2")

        assert all(step["status"] == "done" for step in tracker.steps)

    def test_step_tracker_all_error(self):
        """Test tracker when all steps error."""
        tracker = StepTracker("Test")
        tracker.add("step1", "First Step")
        tracker.add("step2", "Second Step")

        tracker.error("step1")
        tracker.error("step2")

        assert all(step["status"] == "error" for step in tracker.steps)

    def test_step_tracker_step_structure(self):
        """Test that step has correct structure."""
        tracker = StepTracker("Test")
        tracker.add("my-step", "My Step Description")

        step = tracker.steps[0]
        assert "key" in step
        assert "label" in step
        assert "status" in step
        assert "detail" in step
        assert step["key"] == "my-step"
        assert step["label"] == "My Step Description"
        assert step["status"] == "pending"
        assert step["detail"] == ""

    def test_step_tracker_no_duplicate_keys(self):
        """Test that adding duplicate keys doesn't create duplicates."""
        tracker = StepTracker("Test")
        tracker.add("step1", "First Step")
        tracker.add("step1", "Duplicate Step")

        assert len(tracker.steps) == 1
        assert tracker.steps[0]["label"] == "First Step"

    def test_step_tracker_status_order(self):
        """Test that status order is defined correctly."""
        tracker = StepTracker("Test")

        assert tracker.status_order["pending"] == 0
        assert tracker.status_order["running"] == 1
        assert tracker.status_order["done"] == 2
        assert tracker.status_order["error"] == 3
        assert tracker.status_order["skipped"] == 4

    def test_step_tracker_attach_refresh(self):
        """Test attaching refresh callback."""
        tracker = StepTracker("Test")
        callback = lambda: None

        tracker.attach_refresh(callback)
        assert tracker._refresh_cb == callback
