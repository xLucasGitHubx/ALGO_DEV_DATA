"""Tests pour la structure de donnees Queue."""

from meteo_toulouse.data_structures.queue import Queue


class TestQueueEmpty:
    def test_new_queue_is_empty(self):
        q = Queue()
        assert q.is_empty()
        assert q.size() == 0
        assert len(q) == 0

    def test_dequeue_empty(self):
        q = Queue()
        assert q.dequeue() is None

    def test_peek_empty(self):
        q = Queue()
        assert q.peek() is None

    def test_rotate_empty(self):
        q = Queue()
        q.rotate()  # ne doit pas lever d'exception
        assert q.is_empty()


class TestQueueEnqueueDequeue:
    def test_enqueue_single(self):
        q = Queue()
        q.enqueue(1)
        assert q.size() == 1
        assert not q.is_empty()

    def test_fifo_order(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        q.enqueue(3)
        assert q.dequeue() == 1
        assert q.dequeue() == 2
        assert q.dequeue() == 3

    def test_dequeue_makes_empty(self):
        q = Queue()
        q.enqueue(1)
        q.dequeue()
        assert q.is_empty()
        assert q.size() == 0

    def test_enqueue_after_empty(self):
        q = Queue()
        q.enqueue(1)
        q.dequeue()
        q.enqueue(2)
        assert q.dequeue() == 2


class TestQueuePeek:
    def test_peek_returns_head(self):
        q = Queue()
        q.enqueue("a")
        q.enqueue("b")
        assert q.peek() == "a"

    def test_peek_does_not_remove(self):
        q = Queue()
        q.enqueue(1)
        q.peek()
        assert q.size() == 1


class TestQueueRotate:
    def test_rotate_single(self):
        q = Queue()
        q.enqueue(1)
        q.rotate()
        assert q.peek() == 1
        assert q.size() == 1

    def test_rotate_moves_head_to_tail(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        q.enqueue(3)
        q.rotate()
        assert q.to_list() == [2, 3, 1]

    def test_rotate_twice(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        q.enqueue(3)
        q.rotate()
        q.rotate()
        assert q.to_list() == [3, 1, 2]


class TestQueueToList:
    def test_to_list_empty(self):
        q = Queue()
        assert q.to_list() == []

    def test_to_list_with_elements(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        assert q.to_list() == [1, 2]


class TestQueueIter:
    def test_iter(self):
        q = Queue()
        q.enqueue("a")
        q.enqueue("b")
        q.enqueue("c")
        assert list(q) == ["a", "b", "c"]


class TestQueueRepr:
    def test_repr(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        assert repr(q) == "Queue([1, 2])"


class TestQueueSize:
    def test_size_tracking(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        assert q.size() == 2
        q.dequeue()
        assert q.size() == 1
        q.dequeue()
        assert q.size() == 0
