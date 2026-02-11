"""Tests pour la structure de donnees HashMap."""

import pytest
from meteo_toulouse.data_structures.hash_map import HashEntry, HashMap


class TestHashEntry:
    def test_creation(self):
        entry = HashEntry("key", "value")
        assert entry.key == "key"
        assert entry.value == "value"


class TestHashMapEmpty:
    def test_new_map_is_empty(self):
        hm = HashMap()
        assert len(hm) == 0

    def test_get_nonexistent(self):
        hm = HashMap()
        assert hm.get("missing") is None

    def test_get_with_default(self):
        hm = HashMap()
        assert hm.get("missing", "default") == "default"

    def test_contains_empty(self):
        hm = HashMap()
        assert hm.contains("key") is False
        assert ("key" in hm) is False

    def test_remove_nonexistent(self):
        hm = HashMap()
        assert hm.remove("key") is False


class TestHashMapPutGet:
    def test_put_and_get(self):
        hm = HashMap()
        hm.put("a", 1)
        assert hm.get("a") == 1

    def test_put_overwrite(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("a", 2)
        assert hm.get("a") == 2
        assert len(hm) == 1

    def test_put_multiple(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("b", 2)
        hm.put("c", 3)
        assert hm.get("a") == 1
        assert hm.get("b") == 2
        assert hm.get("c") == 3
        assert len(hm) == 3

    def test_bracket_get(self):
        hm = HashMap()
        hm.put("key", "value")
        assert hm["key"] == "value"

    def test_bracket_get_keyerror(self):
        hm = HashMap()
        with pytest.raises(KeyError):
            _ = hm["missing"]

    def test_bracket_set(self):
        hm = HashMap()
        hm["key"] = "value"
        assert hm.get("key") == "value"


class TestHashMapRemove:
    def test_remove_existing(self):
        hm = HashMap()
        hm.put("a", 1)
        assert hm.remove("a") is True
        assert hm.get("a") is None
        assert len(hm) == 0

    def test_remove_nonexistent(self):
        hm = HashMap()
        hm.put("a", 1)
        assert hm.remove("b") is False
        assert len(hm) == 1


class TestHashMapContains:
    def test_contains_present(self):
        hm = HashMap()
        hm.put("key", "val")
        assert hm.contains("key") is True
        assert "key" in hm

    def test_contains_absent(self):
        hm = HashMap()
        assert hm.contains("key") is False


class TestHashMapKeysValuesItems:
    def test_keys(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("b", 2)
        keys = hm.keys()
        assert set(keys) == {"a", "b"}

    def test_values(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("b", 2)
        values = hm.values()
        assert set(values) == {1, 2}

    def test_items(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("b", 2)
        items = hm.items()
        assert set(items) == {("a", 1), ("b", 2)}

    def test_empty_keys_values_items(self):
        hm = HashMap()
        assert hm.keys() == []
        assert hm.values() == []
        assert hm.items() == []


class TestHashMapSetdefault:
    def test_setdefault_new_key(self):
        hm = HashMap()
        result = hm.setdefault("a", 10)
        assert result == 10
        assert hm.get("a") == 10

    def test_setdefault_existing_key(self):
        hm = HashMap()
        hm.put("a", 5)
        result = hm.setdefault("a", 10)
        assert result == 5


class TestHashMapResize:
    def test_resize_preserves_data(self):
        hm = HashMap(capacity=4)
        # Inserer assez d'elements pour declencher un resize
        for i in range(20):
            hm.put(f"key_{i}", i)
        assert len(hm) == 20
        # Verifier que toutes les valeurs sont accessibles
        for i in range(20):
            assert hm.get(f"key_{i}") == i


class TestHashMapCollisions:
    def test_collision_handling(self):
        # Avec une capacite de 1, toutes les cles vont dans le meme bucket
        hm = HashMap(capacity=1)
        hm.put("a", 1)
        hm.put("b", 2)
        hm.put("c", 3)
        assert hm.get("a") == 1
        assert hm.get("b") == 2
        assert hm.get("c") == 3


class TestHashMapIter:
    def test_iter_keys(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("b", 2)
        keys = list(hm)
        assert set(keys) == {"a", "b"}


class TestHashMapRepr:
    def test_repr_empty(self):
        hm = HashMap()
        assert repr(hm) == "HashMap({})"

    def test_repr_with_entries(self):
        hm = HashMap()
        hm.put("a", 1)
        r = repr(hm)
        assert "HashMap(" in r
        assert "'a': 1" in r
