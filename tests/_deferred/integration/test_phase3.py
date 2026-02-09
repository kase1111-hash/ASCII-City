"""
Phase 3 Integration Tests

Tests the integration between Phase 3 systems:
- Render systems (colors, particles, atmosphere)
- Narrative systems (shades, twists, spine)
- Replay systems (seeds, statistics, achievements)
- UI systems (help, history, tutorial)
- Cross-system integration
"""

import pytest
import random

# Render systems
from src.shadowengine.render import (
    ColorManager, THEMES, ParticleSystem, ParticleType,
    AtmosphereManager, Mood, TensionMeter, weather_to_particles,
    get_tension_for_event
)

# Narrative systems
from src.shadowengine.narrative import (
    NarrativeSpine, SpineGenerator, ConflictType,
    MoralShade, ShadeProfile, ShadeNarrator, MoralDecision,
    EndingDeterminator, ENDINGS,
    TwistType, Twist, TwistManager, TwistGenerator, TwistCondition
)

# Replay systems
from src.shadowengine.replay import (
    GameSeed, SeedGenerator, DailyChallenge, SeedCollection,
    GameStatistics, AggregateStatistics,
    Achievement, AchievementManager
)

# UI systems
from src.shadowengine.ui import (
    HelpSystem, HintSystem, ContextualHint, create_standard_hints,
    CommandHistory, UndoStack, UndoableAction,
    Tutorial, TutorialPrompt
)


class TestRenderSystemsIntegration:
    """Tests for render systems working together."""

    def test_atmosphere_affects_colors(self):
        """Atmosphere mood should work with color theming."""
        atmosphere = AtmosphereManager()
        colors = ColorManager(force_color=True)

        # Set tense mood
        atmosphere.tension.set_tension(0.7)
        atmosphere.update()

        # Mood should be dangerous
        assert atmosphere.current_mood == Mood.DANGEROUS

        # Colors should still work with any theme
        colors.set_theme("noir")
        text = colors.tension("Warning!", atmosphere.tension.current)
        assert "Warning!" in text

    def test_particles_respond_to_weather(self):
        """Particle system should respond to weather types."""
        system = ParticleSystem(width=80, height=24)

        # Enable rain particles
        rain_particles = weather_to_particles("light_rain")
        for particle_type in rain_particles:
            system.enable_effect(particle_type)

        # Update several times
        for _ in range(10):
            system.update()

        # Should have spawned particles
        assert len(system.particles) > 0

    def test_tension_triggers_atmosphere_changes(self):
        """Tension changes should affect atmosphere config."""
        atmosphere = AtmosphereManager()

        # Low tension
        atmosphere.tension.set_tension(0.1)
        atmosphere.update()
        low_config = atmosphere.config

        # High tension
        atmosphere.tension.set_tension(0.9)
        atmosphere.update()
        high_config = atmosphere.config

        # Configs should differ
        assert low_config.pulse_enabled != high_config.pulse_enabled or \
               low_config.shake_intensity != high_config.shake_intensity

    def test_color_themes_with_tension_levels(self):
        """All color themes should work with all tension levels."""
        colors = ColorManager(force_color=True)

        for theme_name in THEMES:
            colors.set_theme(theme_name)

            for tension_level in [0.0, 0.3, 0.5, 0.7, 1.0]:
                result = colors.tension("test", tension_level)
                assert "test" in result

    def test_particle_overlay_generation(self):
        """Particle system should generate usable overlay."""
        system = ParticleSystem(width=40, height=20)
        system.enable_effect(ParticleType.RAIN)

        # Run updates
        for _ in range(20):
            system.update()

        # Get overlay
        overlay = system.render_overlay()

        # Should have positions mapped to characters
        assert isinstance(overlay, dict)
        for pos, char in overlay.items():
            assert isinstance(pos, tuple)
            assert len(pos) == 2
            assert isinstance(char, str)

    def test_atmosphere_border_chars_by_mood(self):
        """Each mood should produce valid border characters."""
        atmosphere = AtmosphereManager()

        for mood in Mood:
            atmosphere.set_mood(mood)
            chars = atmosphere.get_border_chars()

            assert 'vertical' in chars
            assert 'horizontal' in chars
            assert 'top_left' in chars
            assert len(chars['vertical']) > 0


class TestNarrativeSystemsIntegration:
    """Tests for narrative systems working together."""

    def test_spine_with_twists(self):
        """Narrative spine should work with twist system."""
        # Generate spine
        generator = SpineGenerator(seed=42)
        spine = generator.generate(
            conflict_type=ConflictType.MURDER,
            characters=["alice", "bob", "charlie"],
            twist_chance=0.5
        )

        # Create twist manager
        twist_manager = TwistManager()
        twist_gen = TwistGenerator(seed=42)

        # Add character twist
        twist = twist_gen.generate_character_twist("bob", TwistType.BETRAYAL)
        twist_manager.add_twist(twist)

        # Simulate game progress
        game_state = {"progress": 0.7, "decisions": []}
        triggered = twist_manager.check_triggers(game_state)

        # Should have triggered the twist
        assert len(triggered) > 0

    def test_shades_affect_endings(self):
        """Moral shades should determine available endings."""
        profile = ShadeProfile()

        # Make several decisions
        decisions = [
            MoralDecision("d1", "Used threats", {MoralShade.RUTHLESS: 5}),
            MoralDecision("d2", "Showed no mercy", {MoralShade.RUTHLESS: 5}),
            MoralDecision("d3", "Justice above all", {MoralShade.RUTHLESS: 5}),
        ]
        for d in decisions:
            profile.apply_decision(d)

        # Should be ruthless dominant
        assert profile.get_dominant_shade() == MoralShade.RUTHLESS

        # Ending determinator should find ruthless ending
        determinator = EndingDeterminator()
        ending = determinator.determine_ending(profile, mystery_solved=True)

        assert ending.shade_requirement == MoralShade.RUTHLESS or ending.shade_requirement is None

    def test_narrator_adapts_to_shade(self):
        """Narrator should adapt text based on moral shade."""
        profiles = {}
        narrators = {}

        for shade in MoralShade:
            profile = ShadeProfile()
            profile.scores[shade] = 100
            profiles[shade] = profile
            narrators[shade] = ShadeNarrator(profile)

        # Each narrator should produce different text
        texts = {}
        for shade, narrator in narrators.items():
            texts[shade] = narrator.narrate_discovery("evidence")

        # Not all should be identical
        unique_texts = set(texts.values())
        assert len(unique_texts) > 1

    def test_twist_changes_culprit(self):
        """Twist that changes culprit should update story impact."""
        manager = TwistManager()

        twist = Twist(
            id="twist1",
            twist_type=TwistType.HIDDEN_IDENTITY,
            name="Hidden Identity",
            description="The real culprit",
            changes_culprit=True,
            new_culprit_id="secret_villain",
            trigger_conditions=[
                TwistCondition("progress", 0.5)
            ]
        )
        manager.add_twist(twist)

        # Trigger and reveal
        manager.check_triggers({"progress": 0.6})
        manager.reveal_twist("twist1")

        # Get story impact
        impact = manager.get_story_impact()
        assert impact["culprit_changed"] is True
        assert impact["current_culprit"] == "secret_villain"

    def test_spine_revelations_with_shade_tracking(self):
        """Revelations should be trackable alongside shade decisions."""
        generator = SpineGenerator(seed=123)
        spine = generator.generate(conflict_type=ConflictType.THEFT)
        profile = ShadeProfile()

        # Make revelation
        available = spine.get_available_revelations()
        if available:
            spine.make_revelation(available[0].id)

        # Make decision
        profile.apply_decision(MoralDecision(
            "found_evidence",
            "Reported all evidence",
            {MoralShade.IDEALISTIC: 2}
        ))

        # Both should track independently
        assert len(spine.revealed_facts) >= 1
        assert len(profile.decisions) == 1


class TestReplaySystemsIntegration:
    """Tests for replay systems working together."""

    def test_seed_generates_consistent_game(self):
        """Same seed should generate same narrative spine."""
        seed = GameSeed(value=12345)

        # Generate two spines with same seed
        gen1 = SpineGenerator(seed=seed.value)
        spine1 = gen1.generate(conflict_type=ConflictType.MURDER)

        gen2 = SpineGenerator(seed=seed.value)
        spine2 = gen2.generate(conflict_type=ConflictType.MURDER)

        # Should be identical
        assert spine1.true_resolution.culprit_id == spine2.true_resolution.culprit_id

    def test_statistics_track_full_game(self):
        """Statistics should track all game metrics."""
        stats = GameStatistics(
            game_id="test_game",
            seed=42,
            locations_visited=5,
            locations_total=10,
            evidence_collected=3,
            evidence_total=5,
            characters_talked=2,
            characters_total=4,
            revelations_discovered=4,
            revelations_total=6,
            commands_entered=50,
            time_played_seconds=600,
            solved=True,
            ending_id="good_ending"
        )

        # Completion should be calculated
        completion = stats.completion_percentage()
        assert 0 < completion < 1

        # Efficiency should be calculated
        efficiency = stats.efficiency_score()
        assert efficiency > 0

    def test_achievements_unlock_from_stats(self):
        """Achievements should unlock based on game statistics."""
        manager = AchievementManager()
        aggregate = AggregateStatistics()

        # First solved game with no wrong accusations
        game_stats = GameStatistics(
            solved=True,
            wrong_accusations=0,
            time_played_seconds=300,
            hotspots_examined=10,
            hotspots_total=10
        )

        aggregate.update_from_game(game_stats)
        unlocked = manager.check_achievements(game_stats, aggregate)

        # Should unlock multiple achievements
        unlocked_ids = [a.id for a in unlocked]
        assert "first_solve" in unlocked_ids
        assert "perfect_solve" in unlocked_ids
        assert "speed_demon" in unlocked_ids
        assert "thorough" in unlocked_ids

    def test_daily_challenge_leaderboard(self):
        """Daily challenge should track scores properly."""
        challenge = DailyChallenge.for_today()

        # Add multiple scores
        challenge.add_score("player1", 600, solved=True)
        challenge.add_score("player2", 300, solved=True)
        challenge.add_score("player3", 200, solved=False)
        challenge.add_score("player4", 400, solved=True)

        # Ranks should be correct
        assert challenge.get_rank("player2") == 1  # Fastest solver
        assert challenge.get_rank("player4") == 2
        assert challenge.get_rank("player1") == 3
        assert challenge.get_rank("player3") == 4  # Unsolved last

    def test_seed_collection_with_favorites(self):
        """Seed collection should manage seeds and favorites."""
        collection = SeedCollection()
        generator = SeedGenerator(base_seed=42)

        # Add themed seeds
        for theme in ["noir", "horror", "mystery"]:
            seed = generator.generate_themed(theme)
            collection.add(seed)

        # Favorite one
        noir_seeds = collection.search("noir")
        if noir_seeds:
            collection.toggle_favorite(noir_seeds[0].value)

        # Check favorites
        favorites = collection.get_favorites()
        assert len(favorites) == 1

    def test_aggregate_stats_across_games(self):
        """Aggregate stats should accumulate across games."""
        aggregate = AggregateStatistics()

        games = [
            GameStatistics(solved=True, time_played_seconds=300, ending_id="good"),
            GameStatistics(solved=True, time_played_seconds=600, ending_id="neutral"),
            GameStatistics(solved=False, time_played_seconds=200, ending_id="bad"),
            GameStatistics(solved=True, time_played_seconds=400, ending_id="good"),
        ]

        for game in games:
            aggregate.update_from_game(game)

        assert aggregate.games_played == 4
        assert aggregate.games_solved == 3
        assert aggregate.fastest_solve_seconds == 300
        assert aggregate.endings_achieved.get("good") == 2


class TestUISystemsIntegration:
    """Tests for UI systems working together."""

    def test_tutorial_with_command_history(self):
        """Tutorial should work with command history tracking."""
        tutorial = Tutorial()
        history = CommandHistory()

        tutorial.start()

        # Execute tutorial commands
        commands = ["look", "exits", "go north"]
        for cmd in commands:
            history.add(cmd)
            result = tutorial.process_command(cmd)
            if result:
                # Tutorial advanced
                pass

        # History should track all commands
        assert len(history) == 3

        # Tutorial should have progressed
        assert tutorial.get_progress() > 0

    def test_help_system_with_hints(self):
        """Help system should complement hint system."""
        help_system = HelpSystem()
        hint_system = HintSystem()

        # Add standard hints
        for hint in create_standard_hints():
            hint_system.add_hint(hint)

        # Simulate new player context
        context = {
            "commands_entered": 0,
            "hotspots_visible": 3,
            "examined_count": 0
        }

        # Should get a hint
        hint = hint_system.check_hints(context)
        assert hint is not None

        # Help should provide related topic
        topic = help_system.get_topic("look")
        assert topic is not None

    def test_undo_stack_with_history(self):
        """Undo stack should work with command history."""
        history = CommandHistory()
        undo_stack = UndoStack()

        # Simulate commands with undo support
        actions = [
            ("take key", UndoableAction("take", "Took key", {"item": "key"})),
            ("go north", UndoableAction("move", "Moved north", {"from": "room1"})),
            ("examine desk", UndoableAction("examine", "Examined desk", {})),
        ]

        for cmd, action in actions:
            history.add(cmd)
            undo_stack.push(action)

        # Should be able to undo
        assert undo_stack.can_undo()
        undone = undo_stack.pop_undo()
        assert undone.action_type == "examine"

        # History still has all commands
        assert len(history) == 3

    def test_tutorial_uses_help_topics(self):
        """Tutorial steps should correspond to help topics."""
        tutorial = Tutorial()
        help_system = HelpSystem()

        tutorial.start()

        # First step should be about 'look'
        step = tutorial.get_current_step()
        assert step is not None

        # Help should have matching topic
        if "look" in step.expected_action:
            topic = help_system.get_topic("look")
            assert topic is not None

    def test_contextual_hints_based_on_progress(self):
        """Hints should adapt to game progress."""
        hint_system = HintSystem()

        # Add progress-based hints
        hint_system.add_hint(ContextualHint(
            id="early_game",
            message="You're just getting started!",
            condition=lambda ctx: ctx.get("progress", 0) < 0.3,
            priority=5
        ))
        hint_system.add_hint(ContextualHint(
            id="mid_game",
            message="You're making progress!",
            condition=lambda ctx: 0.3 <= ctx.get("progress", 0) < 0.7,
            priority=5
        ))
        hint_system.add_hint(ContextualHint(
            id="late_game",
            message="Almost there!",
            condition=lambda ctx: ctx.get("progress", 0) >= 0.7,
            priority=5
        ))

        # Test different progress levels
        assert "started" in hint_system.check_hints({"progress": 0.1})
        hint_system.reset()
        assert "progress" in hint_system.check_hints({"progress": 0.5})
        hint_system.reset()
        assert "Almost" in hint_system.check_hints({"progress": 0.8})


class TestCrossSystemIntegration:
    """Tests for integration across different Phase 3 system categories."""

    def test_tension_from_game_events(self):
        """Game events should affect tension appropriately."""
        atmosphere = AtmosphereManager()

        # Simulate discovery events
        events = [
            "discovered_body",
            "found_evidence",
            "confrontation"
        ]

        for event in events:
            tension_change = get_tension_for_event(event)
            atmosphere.tension.add_tension(tension_change)

        # Tension builds gradually, so run multiple updates
        for _ in range(20):
            atmosphere.update()

        # Should have significant tension (target was ~0.8, after 20 updates should be high)
        assert atmosphere.tension.current > 0.3
        # Target should also be high
        assert atmosphere.tension.target > 0.5

    def test_shade_narrator_with_stats_tracking(self):
        """Shade-based narration should work with statistics."""
        profile = ShadeProfile()
        stats = GameStatistics()

        # Simulate game with compassionate choices
        decisions = [
            ("showed_empathy", {MoralShade.COMPASSIONATE: 2}),
            ("helped_suspect", {MoralShade.COMPASSIONATE: 3}),
            ("let_guilty_go", {MoralShade.COMPASSIONATE: 2, MoralShade.CORRUPT: 1}),
        ]

        for desc, effects in decisions:
            profile.apply_decision(MoralDecision(desc, desc, effects))

        # Update stats
        stats.moral_shade = profile.get_dominant_shade().value

        # Narrator should use compassionate style
        narrator = ShadeNarrator(profile)
        text = narrator.narrate_accusation("suspect", correct=False)

        # Track in stats
        assert stats.moral_shade == "compassionate"

    def test_seed_with_twist_generation(self):
        """Seed should make twist generation reproducible."""
        seed = GameSeed(value=99999)

        # Generate twists with same seed twice
        gen1 = TwistGenerator(seed=seed.value)
        twist1 = gen1.generate_character_twist("villain")

        gen2 = TwistGenerator(seed=seed.value)
        twist2 = gen2.generate_character_twist("villain")

        # Should be same type
        assert twist1.twist_type == twist2.twist_type

    def test_achievement_from_narrative_completion(self):
        """Achievements should unlock from narrative events."""
        manager = AchievementManager()

        # Simulate complete game
        stats = GameStatistics(
            solved=True,
            correct_accusation=True,
            wrong_accusations=0,
            evidence_collected=5,
            evidence_total=5,
            revelations_discovered=4,
            revelations_total=4,
            time_played_seconds=500
        )
        aggregate = AggregateStatistics()
        aggregate.update_from_game(stats)

        # Check achievements
        unlocked = manager.check_achievements(stats, aggregate)
        unlocked_ids = [a.id for a in unlocked]

        # Multiple achievements should unlock
        assert len(unlocked_ids) >= 3

    def test_full_game_simulation(self):
        """Simulate a complete game using all Phase 3 systems."""
        # Setup
        seed = GameSeed.generate(source="test_game")
        spine_gen = SpineGenerator(seed=seed.value)
        spine = spine_gen.generate(conflict_type=ConflictType.MURDER)

        atmosphere = AtmosphereManager()
        particles = ParticleSystem(width=80, height=24)
        colors = ColorManager(force_color=True)
        colors.set_theme("noir")

        profile = ShadeProfile()
        narrator = ShadeNarrator(profile)
        twist_manager = TwistManager()

        history = CommandHistory()
        stats = GameStatistics(game_id="sim_game", seed=seed.value)

        # Simulate gameplay
        commands = [
            ("look", None),
            ("examine 1", "found_evidence"),
            ("talk suspect", None),
            ("present evidence to suspect", "confrontation"),
            ("accuse suspect", None)
        ]

        for cmd, event in commands:
            history.add(cmd)
            stats.commands_entered += 1

            if event:
                tension_change = get_tension_for_event(event)
                atmosphere.tension.add_tension(tension_change)

            atmosphere.update()

        # Make some decisions
        profile.apply_decision(MoralDecision(
            "used_evidence",
            "Presented damning evidence",
            {MoralShade.PRAGMATIC: 2}
        ))

        # Complete game
        stats.solved = True
        stats.moral_shade = profile.get_dominant_shade().value
        stats.time_played_seconds = 600

        # Verify all systems worked
        assert len(history) == 5
        assert stats.commands_entered == 5
        assert atmosphere.tension.current > 0
        assert len(profile.decisions) == 1

    def test_particle_weather_with_atmosphere(self):
        """Weather particles should complement atmosphere mood."""
        atmosphere = AtmosphereManager()
        particles = ParticleSystem(width=80, height=24)

        # Dread mood with fog
        atmosphere.set_mood(Mood.DREAD)
        for ptype in weather_to_particles("fog"):
            particles.enable_effect(ptype)

        # Update systems
        for _ in range(10):
            atmosphere.update()
            particles.update()

        # Both should be active
        assert atmosphere.config.dim_background is True
        assert len(particles.particles) > 0

    def test_ending_determination_full_flow(self):
        """Test complete ending determination with all factors."""
        # Build up shade profile
        profile = ShadeProfile()
        for _ in range(5):
            profile.apply_decision(MoralDecision(
                "idealistic_choice",
                "Followed principles",
                {MoralShade.IDEALISTIC: 3}
            ))

        # Create spine and solve
        generator = SpineGenerator(seed=12345)
        spine = generator.generate(conflict_type=ConflictType.THEFT)

        # Make revelations
        for rev in spine.get_available_revelations():
            spine.make_revelation(rev.id)

        # Check solution
        culprit = spine.true_resolution.culprit_id
        evidence = set(spine.true_resolution.evidence_chain)
        solved, msg = spine.check_solution(culprit, evidence)

        # Determine ending
        determinator = EndingDeterminator()
        ending = determinator.determine_ending(profile, mystery_solved=solved)

        # Should get idealistic ending
        if solved:
            assert ending.shade_requirement == MoralShade.IDEALISTIC or ending.id == "neutral_solved"


class TestSerializationRoundtrips:
    """Test serialization roundtrips for Phase 3 systems."""

    def test_atmosphere_serialization(self):
        """Atmosphere manager should serialize/deserialize correctly."""
        original = AtmosphereManager()
        original.tension.set_tension(0.7)
        original.set_mood(Mood.DANGEROUS)

        data = original.to_dict()
        restored = AtmosphereManager.from_dict(data)

        assert restored.tension.current == 0.7
        assert restored.override_mood == Mood.DANGEROUS

    def test_shade_profile_serialization(self):
        """Shade profile should preserve all data."""
        original = ShadeProfile()
        original.apply_decision(MoralDecision(
            "test", "Test decision", {MoralShade.CORRUPT: 5}
        ))
        original.apply_decision(MoralDecision(
            "test2", "Test 2", {MoralShade.RUTHLESS: 3}
        ))

        data = original.to_dict()
        restored = ShadeProfile.from_dict(data)

        assert restored.scores[MoralShade.CORRUPT] == 5
        assert restored.scores[MoralShade.RUTHLESS] == 3
        assert len(restored.decisions) == 2

    def test_twist_manager_serialization(self):
        """Twist manager should preserve twist states."""
        original = TwistManager()
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test twist"
        )
        twist.trigger()
        original.add_twist(twist)

        data = original.to_dict()
        restored = TwistManager.from_dict(data)

        assert len(restored.twists) == 1
        assert restored.twists[0].triggered is True

    def test_game_seed_share_code_roundtrip(self):
        """Seed share codes should preserve all settings."""
        original = GameSeed(
            value=123456,
            difficulty="nightmare",
            character_count=8,
            twist_enabled=True,
            conflict_type="conspiracy"
        )

        code = original.to_share_code()
        restored = GameSeed.from_share_code(code)

        assert restored.value == 123456
        assert restored.difficulty == "nightmare"
        assert restored.character_count == 8
        assert restored.twist_enabled is True
        assert restored.conflict_type == "conspiracy"

    def test_tutorial_state_serialization(self):
        """Tutorial state should persist across saves."""
        original = Tutorial()
        original.start()
        original.process_command("look")
        original.process_command("exits")

        data = original.to_dict()
        restored = Tutorial.from_dict(data)

        assert restored.active is True
        assert restored.current_step == original.current_step
        assert len(restored.completed_steps) == 2

    def test_command_history_serialization(self):
        """Command history should persist."""
        original = CommandHistory()
        original.add("look", "You see a room", True)
        original.add("examine desk", "A wooden desk", True)
        original.add("invalid", "Unknown command", False)

        data = original.to_dict()
        restored = CommandHistory.from_dict(data)

        assert len(restored) == 3
        assert restored.entries[0].command == "look"
        assert restored.entries[2].success is False
