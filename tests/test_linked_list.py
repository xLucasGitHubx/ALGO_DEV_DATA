"""Tests pour la structure de donnees LinkedList."""

import pytest
from meteo_toulouse.data_structures.linked_list import ListNode, LinkedList


class TestListNode:
    def test_creation(self):
        node = ListNode(42)
        assert node.value == 42
        assert node.next is None

    def test_repr(self):
        node = ListNode("hello")
        assert repr(node) == "ListNode('hello')"


class TestLinkedListEmpty:
    def test_new_list_is_empty(self):
        ll = LinkedList()
        assert ll.is_empty()
        assert len(ll) == 0
        assert ll.head is None

    def test_to_list_empty(self):
        ll = LinkedList()
        assert ll.to_list() == []

    def test_get_on_empty(self):
        ll = LinkedList()
        assert ll.get(0) is None

    def test_find_on_empty(self):
        ll = LinkedList()
        assert ll.find(lambda x: True) is None

    def test_remove_on_empty(self):
        ll = LinkedList()
        assert ll.remove(1) is False


class TestLinkedListAppend:
    def test_append_single(self):
        ll = LinkedList()
        ll.append(1)
        assert len(ll) == 1
        assert ll.get(0) == 1
        assert not ll.is_empty()

    def test_append_multiple(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        assert len(ll) == 3
        assert ll.to_list() == [1, 2, 3]

    def test_append_preserves_order(self):
        ll = LinkedList()
        for i in range(5):
            ll.append(i)
        assert ll.to_list() == [0, 1, 2, 3, 4]


class TestLinkedListPrepend:
    def test_prepend_single(self):
        ll = LinkedList()
        ll.prepend(1)
        assert len(ll) == 1
        assert ll.get(0) == 1

    def test_prepend_puts_at_head(self):
        ll = LinkedList()
        ll.append(2)
        ll.prepend(1)
        assert ll.to_list() == [1, 2]

    def test_prepend_multiple(self):
        ll = LinkedList()
        ll.prepend(3)
        ll.prepend(2)
        ll.prepend(1)
        assert ll.to_list() == [1, 2, 3]


class TestLinkedListRemove:
    def test_remove_head(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        assert ll.remove(1) is True
        assert ll.to_list() == [2]
        assert len(ll) == 1

    def test_remove_middle(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        assert ll.remove(2) is True
        assert ll.to_list() == [1, 3]

    def test_remove_tail(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        assert ll.remove(3) is True
        assert ll.to_list() == [1, 2]

    def test_remove_nonexistent(self):
        ll = LinkedList()
        ll.append(1)
        assert ll.remove(99) is False
        assert len(ll) == 1

    def test_remove_only_first_occurrence(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(1)
        ll.remove(1)
        assert ll.to_list() == [2, 1]


class TestLinkedListGet:
    def test_get_valid_indices(self):
        ll = LinkedList()
        ll.append("a")
        ll.append("b")
        ll.append("c")
        assert ll.get(0) == "a"
        assert ll.get(1) == "b"
        assert ll.get(2) == "c"

    def test_get_negative_index(self):
        ll = LinkedList()
        ll.append(1)
        assert ll.get(-1) is None

    def test_get_out_of_range(self):
        ll = LinkedList()
        ll.append(1)
        assert ll.get(5) is None


class TestLinkedListFind:
    def test_find_match(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        result = ll.find(lambda x: x > 1)
        assert result == 2

    def test_find_no_match(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        assert ll.find(lambda x: x > 10) is None


class TestLinkedListContains:
    def test_contains_present(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        assert 1 in ll
        assert 2 in ll

    def test_contains_absent(self):
        ll = LinkedList()
        ll.append(1)
        assert 99 not in ll


class TestLinkedListIter:
    def test_iter(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        result = [x for x in ll]
        assert result == [1, 2, 3]

    def test_iter_empty(self):
        ll = LinkedList()
        assert list(ll) == []


class TestLinkedListRepr:
    def test_repr_empty(self):
        ll = LinkedList()
        assert repr(ll) == "LinkedList([])"

    def test_repr_with_elements(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        assert repr(ll) == "LinkedList([1, 2])"
