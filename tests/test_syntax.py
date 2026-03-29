# tests/test_syntax.py
from wod_core.syntax import transform_line, parse_condition, validate_identifiers, clear_identifiers


class TestParseCondition:
    """Test parsing individual bracket conditions into gate/has calls."""

    def setup_method(self):
        clear_identifiers()

    def test_simple_gte(self):
        assert parse_condition("Forces >= 3") == 'wod_core.gate("Forces", ">=", 3)'

    def test_simple_eq(self):
        assert parse_condition("Forces == 3") == 'wod_core.gate("Forces", "==", 3)'

    def test_simple_lt(self):
        assert parse_condition("Forces < 3") == 'wod_core.gate("Forces", "<", 3)'

    def test_simple_lte(self):
        assert parse_condition("Forces <= 3") == 'wod_core.gate("Forces", "<=", 3)'

    def test_simple_gt(self):
        assert parse_condition("Forces > 3") == 'wod_core.gate("Forces", ">", 3)'

    def test_simple_neq(self):
        assert parse_condition("Forces != 3") == 'wod_core.gate("Forces", "!=", 3)'

    def test_multi_word_trait(self):
        assert parse_condition("Martial Arts >= 2") == 'wod_core.gate("Martial Arts", ">=", 2)'

    def test_boolean_merit(self):
        assert parse_condition("Avatar Companion") == 'wod_core.has("Avatar Companion")'

    def test_negated_flaw(self):
        assert parse_condition("!Blind") == 'not wod_core.has("Blind")'

    def test_resource_name(self):
        assert parse_condition("quintessence >= 5") == 'wod_core.gate("quintessence", ">=", 5)'


class TestTransformLine:
    """Test full line transformation from shorthand to native Ren'Py."""

    def setup_method(self):
        clear_identifiers()

    def test_single_condition(self):
        line = '    "Rewrite the ward" [Forces >= 3]:'
        expected = '    "Rewrite the ward" if wod_core.gate("Forces", ">=", 3):'
        assert transform_line(line) == expected

    def test_multiple_conditions(self):
        line = '    "Rewrite the ward" [Prime >= 3, Forces >= 2]:'
        expected = '    "Rewrite the ward" if wod_core.gate("Prime", ">=", 3) and wod_core.gate("Forces", ">=", 2):'
        assert transform_line(line) == expected

    def test_boolean_condition(self):
        line = '    "Use your familiar" [Avatar Companion]:'
        expected = '    "Use your familiar" if wod_core.has("Avatar Companion"):'
        assert transform_line(line) == expected

    def test_negated_condition(self):
        line = '    "See clearly" [!Blind]:'
        expected = '    "See clearly" if not wod_core.has("Blind"):'
        assert transform_line(line) == expected

    def test_no_brackets_unchanged(self):
        line = '    "Just a normal choice":'
        assert transform_line(line) == line

    def test_existing_if_unchanged(self):
        line = '    "Choice" if pc.gate("Forces", ">=", 3):'
        assert transform_line(line) == line

    def test_locked_annotation_preserved(self):
        line = '    "Rewrite the ward" [Forces >= 3] (locked="You lack the knowledge..."):'
        result = transform_line(line)
        assert 'wod_core.gate("Forces", ">=", 3)' in result

    def test_mixed_conditions_and_boolean(self):
        line = '    "Astral travel" [Mind >= 4, Avatar Companion]:'
        expected = '    "Astral travel" if wod_core.gate("Mind", ">=", 4) and wod_core.has("Avatar Companion"):'
        assert transform_line(line) == expected


class TestValidateIdentifiers:
    """Test Phase 2 validation — checking identifiers against loaded schema."""

    def setup_method(self):
        clear_identifiers()

    def test_valid_identifiers_pass(self, mage_schema_data):
        from wod_core.engine import Schema
        schema = Schema(mage_schema_data)

        transform_line('    "Cast spell" [Forces >= 3]:')
        transform_line('    "Check ward" [Prime >= 1]:')

        errors = validate_identifiers(schema, resource_names=["quintessence", "paradox", "willpower", "health"])
        assert errors == []

    def test_unknown_identifier_returns_error(self, mage_schema_data):
        from wod_core.engine import Schema
        schema = Schema(mage_schema_data)

        transform_line('    "Cast" [Forcs >= 3]:')

        errors = validate_identifiers(schema, resource_names=[])
        assert len(errors) >= 1
        assert "Forcs" in errors[0]

    def test_did_you_mean_suggestion(self, mage_schema_data):
        from wod_core.engine import Schema
        schema = Schema(mage_schema_data)

        transform_line('    "Cast" [Forcs >= 3]:')

        errors = validate_identifiers(schema, resource_names=[])
        assert "Forces" in errors[0]
