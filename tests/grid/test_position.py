"""
Comprehensive tests for the Position class.
"""

import pytest
import math
from shadowengine.grid import Position


class TestPositionCreation:
    """Position creation and initialization tests."""

    @pytest.mark.unit
    def test_create_position_basic(self):
        """Can create a basic position."""
        pos = Position(5, 10, 0)
        assert pos.x == 5
        assert pos.y == 10
        assert pos.z == 0

    @pytest.mark.unit
    def test_create_position_with_z(self):
        """Can create position with z-level."""
        pos = Position(1, 2, 3)
        assert pos.z == 3

    @pytest.mark.unit
    def test_create_position_default_z(self):
        """Z defaults to 0 when not specified."""
        pos = Position(5, 10)
        assert pos.z == 0

    @pytest.mark.unit
    def test_create_position_negative_coordinates(self):
        """Can create position with negative coordinates."""
        pos = Position(-5, -10, -2)
        assert pos.x == -5
        assert pos.y == -10
        assert pos.z == -2

    @pytest.mark.unit
    def test_position_immutable(self):
        """Position is immutable (frozen dataclass)."""
        pos = Position(5, 10, 0)
        with pytest.raises(AttributeError):
            pos.x = 20

    @pytest.mark.unit
    def test_position_requires_integers(self):
        """Position coordinates must be integers."""
        with pytest.raises(TypeError):
            Position(1.5, 2, 0)

        with pytest.raises(TypeError):
            Position(1, 2.5, 0)

        with pytest.raises(TypeError):
            Position(1, 2, 0.5)

    @pytest.mark.unit
    def test_origin_factory(self):
        """Can create origin position using factory."""
        pos = Position.origin()
        assert pos.x == 0
        assert pos.y == 0
        assert pos.z == 0


class TestPositionArithmetic:
    """Position arithmetic operations tests."""

    @pytest.mark.unit
    def test_add_positions(self):
        """Can add two positions."""
        pos1 = Position(5, 10, 1)
        pos2 = Position(3, 2, 1)
        result = pos1 + pos2
        assert result == Position(8, 12, 2)

    @pytest.mark.unit
    def test_subtract_positions(self):
        """Can subtract positions."""
        pos1 = Position(10, 20, 5)
        pos2 = Position(3, 5, 2)
        result = pos1 - pos2
        assert result == Position(7, 15, 3)

    @pytest.mark.unit
    def test_negate_position(self):
        """Can negate a position."""
        pos = Position(5, -3, 2)
        result = -pos
        assert result == Position(-5, 3, -2)

    @pytest.mark.unit
    def test_add_invalid_type(self):
        """Adding non-Position raises TypeError."""
        pos = Position(5, 10, 0)
        with pytest.raises(TypeError):
            pos + (1, 2, 3)

    @pytest.mark.unit
    def test_subtract_invalid_type(self):
        """Subtracting non-Position raises TypeError."""
        pos = Position(5, 10, 0)
        with pytest.raises(TypeError):
            pos - (1, 2, 3)


class TestPositionDistance:
    """Position distance calculation tests."""

    @pytest.mark.unit
    def test_euclidean_distance_same_position(self):
        """Distance to same position is 0."""
        pos = Position(5, 10, 0)
        assert pos.distance_to(pos) == 0.0

    @pytest.mark.unit
    def test_euclidean_distance_horizontal(self):
        """Horizontal distance calculation."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 0, 0)
        assert pos1.distance_to(pos2) == 3.0

    @pytest.mark.unit
    def test_euclidean_distance_vertical(self):
        """Vertical distance calculation."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(0, 4, 0)
        assert pos1.distance_to(pos2) == 4.0

    @pytest.mark.unit
    def test_euclidean_distance_diagonal(self):
        """Diagonal distance calculation (Pythagorean)."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 0)
        assert pos1.distance_to(pos2) == 5.0  # 3-4-5 triangle

    @pytest.mark.unit
    def test_euclidean_distance_3d(self):
        """3D distance calculation."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(2, 2, 1)
        expected = math.sqrt(2*2 + 2*2 + 1*1)
        assert abs(pos1.distance_to(pos2) - expected) < 0.0001

    @pytest.mark.unit
    def test_distance_without_z(self):
        """Distance calculation ignoring z."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 10)
        assert pos1.distance_to(pos2, include_z=False) == 5.0

    @pytest.mark.unit
    def test_manhattan_distance_same_position(self):
        """Manhattan distance to same position is 0."""
        pos = Position(5, 10, 0)
        assert pos.manhattan_distance(pos) == 0

    @pytest.mark.unit
    def test_manhattan_distance_basic(self):
        """Basic Manhattan distance calculation."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 0)
        assert pos1.manhattan_distance(pos2) == 7

    @pytest.mark.unit
    def test_manhattan_distance_3d(self):
        """Manhattan distance with z-axis."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 2)
        assert pos1.manhattan_distance(pos2) == 9

    @pytest.mark.unit
    def test_manhattan_distance_without_z(self):
        """Manhattan distance ignoring z."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 10)
        assert pos1.manhattan_distance(pos2, include_z=False) == 7

    @pytest.mark.unit
    def test_chebyshev_distance_same_position(self):
        """Chebyshev distance to same position is 0."""
        pos = Position(5, 10, 0)
        assert pos.chebyshev_distance(pos) == 0

    @pytest.mark.unit
    def test_chebyshev_distance_basic(self):
        """Basic Chebyshev distance calculation."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 0)
        assert pos1.chebyshev_distance(pos2) == 4  # max(3, 4)

    @pytest.mark.unit
    def test_chebyshev_distance_3d(self):
        """Chebyshev distance with z-axis."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 6)
        assert pos1.chebyshev_distance(pos2) == 6  # max(3, 4, 6)


class TestPositionAdjacency:
    """Position adjacency tests."""

    @pytest.mark.unit
    def test_is_adjacent_cardinal(self, sample_position):
        """Cardinal neighbors are adjacent."""
        north = Position(5, 4, 0)
        south = Position(5, 6, 0)
        east = Position(6, 5, 0)
        west = Position(4, 5, 0)

        assert sample_position.is_adjacent_to(north)
        assert sample_position.is_adjacent_to(south)
        assert sample_position.is_adjacent_to(east)
        assert sample_position.is_adjacent_to(west)

    @pytest.mark.unit
    def test_is_adjacent_diagonal(self, sample_position):
        """Diagonal neighbors are adjacent when diagonals included."""
        northeast = Position(6, 4, 0)
        assert sample_position.is_adjacent_to(northeast, include_diagonals=True)

    @pytest.mark.unit
    def test_is_adjacent_diagonal_excluded(self, sample_position):
        """Diagonal neighbors not adjacent when diagonals excluded."""
        northeast = Position(6, 4, 0)
        assert not sample_position.is_adjacent_to(northeast, include_diagonals=False)

    @pytest.mark.unit
    def test_is_adjacent_not_adjacent(self, sample_position):
        """Far positions are not adjacent."""
        far = Position(20, 20, 0)
        assert not sample_position.is_adjacent_to(far)

    @pytest.mark.unit
    def test_is_adjacent_same_position(self, sample_position):
        """Same position is not adjacent to itself."""
        assert not sample_position.is_adjacent_to(sample_position)

    @pytest.mark.unit
    def test_is_adjacent_different_z(self, sample_position):
        """Different z-level not adjacent by default."""
        above = Position(5, 5, 1)
        assert not sample_position.is_adjacent_to(above)

    @pytest.mark.unit
    def test_is_adjacent_with_z(self, sample_position):
        """Can check adjacency including z-axis."""
        above = Position(5, 5, 1)
        assert sample_position.is_adjacent_to(above, include_z=True)

    @pytest.mark.unit
    def test_get_adjacent_positions_cardinal_only(self, sample_position):
        """Get cardinal adjacent positions only."""
        adjacent = sample_position.get_adjacent_positions(include_diagonals=False)
        assert len(adjacent) == 4

        positions = set(p.to_tuple() for p in adjacent)
        assert (4, 5, 0) in positions   # West
        assert (6, 5, 0) in positions   # East
        assert (5, 4, 0) in positions   # North
        assert (5, 6, 0) in positions   # South

    @pytest.mark.unit
    def test_get_adjacent_positions_with_diagonals(self, sample_position):
        """Get all adjacent positions including diagonals."""
        adjacent = sample_position.get_adjacent_positions(include_diagonals=True)
        assert len(adjacent) == 8

    @pytest.mark.unit
    def test_get_adjacent_positions_with_z(self, sample_position):
        """Get adjacent positions including z-levels."""
        adjacent = sample_position.get_adjacent_positions(include_diagonals=False, include_z=True)
        # 4 cardinal + 2 vertical = 6
        assert len(adjacent) == 6

        positions = set(p.to_tuple() for p in adjacent)
        assert (5, 5, 1) in positions  # Above
        assert (5, 5, -1) in positions  # Below

    @pytest.mark.unit
    def test_get_adjacent_positions_all(self, sample_position):
        """Get all adjacent positions including diagonals and z."""
        adjacent = sample_position.get_adjacent_positions(include_diagonals=True, include_z=True)
        # 8 planar + 2 vertical + 16 diagonal vertical = 26
        assert len(adjacent) == 26


class TestPositionConversion:
    """Position conversion and serialization tests."""

    @pytest.mark.unit
    def test_to_tuple(self, sample_position):
        """Convert position to tuple."""
        assert sample_position.to_tuple() == (5, 5, 0)

    @pytest.mark.unit
    def test_to_2d_tuple(self, sample_position):
        """Convert position to 2D tuple."""
        pos = Position(5, 10, 3)
        assert pos.to_2d_tuple() == (5, 10)

    @pytest.mark.unit
    def test_from_tuple_2d(self):
        """Create position from 2D tuple."""
        pos = Position.from_tuple((5, 10))
        assert pos.x == 5
        assert pos.y == 10
        assert pos.z == 0

    @pytest.mark.unit
    def test_from_tuple_3d(self):
        """Create position from 3D tuple."""
        pos = Position.from_tuple((5, 10, 3))
        assert pos.x == 5
        assert pos.y == 10
        assert pos.z == 3

    @pytest.mark.unit
    def test_from_tuple_invalid_length(self):
        """Invalid tuple length raises error."""
        with pytest.raises(ValueError):
            Position.from_tuple((1,))

        with pytest.raises(ValueError):
            Position.from_tuple((1, 2, 3, 4))


class TestPositionEquality:
    """Position equality and hashing tests."""

    @pytest.mark.unit
    def test_equal_positions(self):
        """Equal positions are equal."""
        pos1 = Position(5, 10, 0)
        pos2 = Position(5, 10, 0)
        assert pos1 == pos2

    @pytest.mark.unit
    def test_different_positions(self):
        """Different positions are not equal."""
        pos1 = Position(5, 10, 0)
        pos2 = Position(5, 11, 0)
        assert pos1 != pos2

    @pytest.mark.unit
    def test_position_hash(self):
        """Equal positions have same hash."""
        pos1 = Position(5, 10, 0)
        pos2 = Position(5, 10, 0)
        assert hash(pos1) == hash(pos2)

    @pytest.mark.unit
    def test_position_in_set(self):
        """Positions can be used in sets."""
        positions = {Position(1, 1, 0), Position(2, 2, 0), Position(1, 1, 0)}
        assert len(positions) == 2

    @pytest.mark.unit
    def test_position_as_dict_key(self):
        """Positions can be used as dictionary keys."""
        data = {
            Position(1, 1, 0): "a",
            Position(2, 2, 0): "b"
        }
        assert data[Position(1, 1, 0)] == "a"


class TestPositionStringRepresentation:
    """Position string representation tests."""

    @pytest.mark.unit
    def test_repr(self):
        """Test repr output."""
        pos = Position(5, 10, 2)
        assert repr(pos) == "Position(5, 10, 2)"

    @pytest.mark.unit
    def test_str(self):
        """Test str output."""
        pos = Position(5, 10, 2)
        assert str(pos) == "(5, 10, 2)"
