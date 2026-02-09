"""
Tests for Animation system.
"""

import pytest
import time
from src.shadowengine.studio.animation import (
    Animation, AnimationFrame, AnimationTrigger, AnimationPlayer
)


class TestAnimationTrigger:
    """Tests for AnimationTrigger enum."""

    def test_triggers_exist(self):
        """All triggers exist."""
        expected = [
            "ALWAYS", "ON_IDLE", "ON_MOVE", "ON_ACTION",
            "ON_INTERACT", "ON_DAMAGE", "ON_STATE",
            "ON_WEATHER", "ON_TIME", "MANUAL"
        ]
        for name in expected:
            assert hasattr(AnimationTrigger, name)


class TestAnimationFrame:
    """Tests for AnimationFrame class."""

    def test_create_frame(self, simple_frame):
        """Can create animation frame."""
        assert simple_frame.tiles == [["*"]]
        assert simple_frame.duration == 0.5
        assert simple_frame.offset == (0, 0)
        assert simple_frame.sound is None

    def test_frame_dimensions(self, simple_frame):
        """Frame reports correct dimensions."""
        assert simple_frame.width == 1
        assert simple_frame.height == 1

    def test_frame_with_offset(self):
        """Frame can have offset."""
        frame = AnimationFrame(
            tiles=[["X"]],
            duration=0.2,
            offset=(5, 3)
        )
        assert frame.offset == (5, 3)

    def test_frame_with_sound(self):
        """Frame can have sound."""
        frame = AnimationFrame(
            tiles=[["!"]],
            duration=0.1,
            sound="explosion"
        )
        assert frame.sound == "explosion"

    def test_frame_render(self):
        """Frame can be rendered."""
        frame = AnimationFrame(tiles=[["A", "B"], ["C", "D"]])
        rendered = frame.render()
        assert rendered == "AB\nCD"

    def test_frame_serialization(self, simple_frame):
        """Frame can be serialized and deserialized."""
        data = simple_frame.to_dict()
        restored = AnimationFrame.from_dict(data)

        assert restored.tiles == simple_frame.tiles
        assert restored.duration == simple_frame.duration
        assert restored.offset == simple_frame.offset

    def test_frame_from_string(self):
        """Frame can be created from string."""
        frame = AnimationFrame.from_string("AB\nCD", duration=0.3)

        assert frame.tiles == [["A", "B"], ["C", "D"]]
        assert frame.duration == 0.3

    def test_empty_frame_dimensions(self):
        """Empty frame has zero dimensions."""
        frame = AnimationFrame(tiles=[])
        assert frame.width == 0
        assert frame.height == 0


class TestAnimation:
    """Tests for Animation class."""

    def test_create_animation(self, idle_animation):
        """Can create animation."""
        assert idle_animation.name == "idle"
        assert idle_animation.frame_count == 4
        assert idle_animation.loop is True
        assert idle_animation.trigger == AnimationTrigger.ON_IDLE

    def test_animation_duration(self, idle_animation):
        """Animation calculates total duration."""
        # 0.5 + 0.5 + 0.5 + 1.0 = 2.5
        assert idle_animation.duration == 2.5

    def test_animation_requires_frames(self):
        """Animation requires at least one frame."""
        with pytest.raises(ValueError):
            Animation(name="empty", frames=[])

    def test_get_frame_at_time(self, idle_animation):
        """Can get frame at specific time."""
        # Time 0 -> first frame
        frame = idle_animation.get_frame_at_time(0)
        assert frame.tiles == [["O"]]

        # Time 0.6 -> second frame
        frame = idle_animation.get_frame_at_time(0.6)
        assert frame.tiles == [["o"]]

        # Time 1.2 -> third frame
        frame = idle_animation.get_frame_at_time(1.2)
        assert frame.tiles == [["O"]]

    def test_get_frame_at_time_looping(self, idle_animation):
        """Looping animation wraps around."""
        # At time 2.5 (full duration), wraps to start
        frame = idle_animation.get_frame_at_time(2.5)
        assert frame.tiles == [["O"]]

        # At time 3.0 (2.5 + 0.5), second frame
        frame = idle_animation.get_frame_at_time(3.0)
        assert frame.tiles == [["o"]]

    def test_get_frame_at_time_non_looping(self, attack_animation):
        """Non-looping animation stays at last frame."""
        # Total duration is 0.1 + 0.1 + 0.1 + 0.2 = 0.5
        frame = attack_animation.get_frame_at_time(10.0)  # Way past end
        assert frame.tiles == [["\\O/"]]  # Last frame

    def test_get_frame_index_at_time(self, idle_animation):
        """Can get frame index at time."""
        assert idle_animation.get_frame_index_at_time(0) == 0
        assert idle_animation.get_frame_index_at_time(0.6) == 1
        assert idle_animation.get_frame_index_at_time(1.2) == 2

    def test_should_play_always(self):
        """ALWAYS trigger always plays."""
        frame = AnimationFrame(tiles=[["X"]])
        animation = Animation(
            name="always",
            frames=[frame],
            trigger=AnimationTrigger.ALWAYS
        )
        assert animation.should_play("any_state") is True
        assert animation.should_play("idle") is True

    def test_should_play_on_idle(self, idle_animation):
        """ON_IDLE trigger plays in idle state."""
        assert idle_animation.should_play("idle") is True
        assert idle_animation.should_play("moving") is False

    def test_should_play_on_move(self):
        """ON_MOVE trigger plays while moving."""
        frame = AnimationFrame(tiles=[["X"]])
        animation = Animation(
            name="walk",
            frames=[frame],
            trigger=AnimationTrigger.ON_MOVE
        )
        assert animation.should_play("moving") is True
        assert animation.should_play("walking") is True
        assert animation.should_play("running") is True
        assert animation.should_play("idle") is False

    def test_should_play_on_action(self, attack_animation):
        """ON_ACTION trigger plays on action event."""
        assert attack_animation.should_play("any", "action") is True
        assert attack_animation.should_play("any", "damage") is False

    def test_should_play_on_state(self):
        """ON_STATE trigger plays in specific state."""
        frame = AnimationFrame(tiles=[["X"]])
        animation = Animation(
            name="sleeping",
            frames=[frame],
            trigger=AnimationTrigger.ON_STATE,
            state_condition="asleep"
        )
        assert animation.should_play("asleep") is True
        assert animation.should_play("awake") is False

    def test_animation_serialization(self, idle_animation):
        """Animation can be serialized and deserialized."""
        data = idle_animation.to_dict()
        restored = Animation.from_dict(data)

        assert restored.name == idle_animation.name
        assert restored.frame_count == idle_animation.frame_count
        assert restored.loop == idle_animation.loop
        assert restored.trigger == idle_animation.trigger


class TestAnimationPlayer:
    """Tests for AnimationPlayer class."""

    def test_create_player(self):
        """Can create animation player."""
        player = AnimationPlayer()
        assert player.current_animation is None
        assert player.paused is False

    def test_add_animation(self, idle_animation):
        """Can add animations to player."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)
        assert "idle" in player.animations

    def test_remove_animation(self, idle_animation):
        """Can remove animations from player."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)

        assert player.remove_animation("idle") is True
        assert "idle" not in player.animations
        assert player.remove_animation("idle") is False  # Already removed

    def test_play_animation(self, idle_animation):
        """Can play an animation."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)

        assert player.play("idle") is True
        assert player.current_animation == "idle"
        assert player.paused is False

    def test_play_nonexistent_animation(self):
        """Playing nonexistent animation fails."""
        player = AnimationPlayer()
        assert player.play("nonexistent") is False

    def test_stop_animation(self, idle_animation):
        """Can stop animation."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)
        player.play("idle")

        player.stop()
        assert player.current_animation is None

    def test_pause_resume(self, idle_animation):
        """Can pause and resume animation."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)
        player.play("idle")

        player.pause()
        assert player.paused is True

        player.resume()
        assert player.paused is False

    def test_get_current_frame(self, idle_animation):
        """Can get current frame."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)
        player.play("idle")

        frame = player.get_current_frame()
        assert frame is not None
        # Should be first frame at start
        assert frame.tiles == [["O"]]

    def test_get_current_frame_no_animation(self):
        """No frame if no animation playing."""
        player = AnimationPlayer()
        assert player.get_current_frame() is None

    def test_is_finished_looping(self, idle_animation):
        """Looping animation never finishes."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)
        player.play("idle")

        # Wait some time (simulated)
        time.sleep(0.01)
        assert player.is_finished() is False

    def test_is_finished_non_looping(self, attack_animation):
        """Non-looping animation finishes."""
        player = AnimationPlayer()
        player.add_animation(attack_animation)
        player.play("attack")

        # Initially not finished
        assert player.is_finished() is False

        # Manually set start time to simulate time passing
        player.start_time = time.time() - 10  # 10 seconds ago
        assert player.is_finished() is True

    def test_update_for_state(self, idle_animation, attack_animation):
        """Player updates animation for state."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)
        player.add_animation(attack_animation)

        # Idle state should play idle animation
        player.update_for_state("idle")
        assert player.current_animation == "idle"

        # Action event should play attack animation
        player.update_for_state("any", "action")
        assert player.current_animation == "attack"

    def test_remove_current_animation(self, idle_animation):
        """Removing current animation clears it."""
        player = AnimationPlayer()
        player.add_animation(idle_animation)
        player.play("idle")

        player.remove_animation("idle")
        assert player.current_animation is None
