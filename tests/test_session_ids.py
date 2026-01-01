"""Tests for session ID generation."""

from event_bus.session_ids import ADJECTIVES, ANIMALS, generate_session_id


class TestGenerateSessionId:
    """Tests for generate_session_id function."""

    def test_format_adjective_animal(self):
        """Test that generated ID follows adjective-animal format."""
        session_id = generate_session_id()

        parts = session_id.split("-")
        assert len(parts) == 2, f"Expected 'adjective-animal' format, got: {session_id}"
        adjective, animal = parts

        assert adjective in ADJECTIVES, f"Unknown adjective: {adjective}"
        assert animal in ANIMALS, f"Unknown animal: {animal}"

    def test_uniqueness_over_multiple_generations(self):
        """Test that generating many IDs produces variety (not always the same)."""
        ids = {generate_session_id() for _ in range(50)}

        # With 32 adjectives * 33 animals = 1056 combinations,
        # 50 samples should produce at least 10 unique IDs
        assert len(ids) >= 10, f"Expected variety in IDs, but got only {len(ids)} unique"

    def test_valid_identifier_format(self):
        """Test that generated IDs are valid identifiers (lowercase, hyphen-separated)."""
        for _ in range(20):
            session_id = generate_session_id()

            # Should be lowercase
            assert session_id == session_id.lower()
            # Should contain exactly one hyphen
            assert session_id.count("-") == 1
            # Should not contain spaces or special characters
            assert " " not in session_id
            assert "\n" not in session_id
            assert "\t" not in session_id

    def test_wordlist_contents(self):
        """Test that wordlists contain expected values."""
        # Verify some known words exist
        assert "brave" in ADJECTIVES
        assert "tiger" in ANIMALS
        assert "clever" in ADJECTIVES
        assert "falcon" in ANIMALS

        # Verify reasonable size
        assert len(ADJECTIVES) >= 20
        assert len(ANIMALS) >= 20

    def test_all_words_are_lowercase(self):
        """Test that all words in wordlists are lowercase."""
        for adj in ADJECTIVES:
            assert adj == adj.lower(), f"Adjective not lowercase: {adj}"
        for animal in ANIMALS:
            assert animal == animal.lower(), f"Animal not lowercase: {animal}"

    def test_no_hyphen_in_words(self):
        """Test that individual words don't contain hyphens."""
        for adj in ADJECTIVES:
            assert "-" not in adj, f"Adjective contains hyphen: {adj}"
        for animal in ANIMALS:
            assert "-" not in animal, f"Animal contains hyphen: {animal}"
