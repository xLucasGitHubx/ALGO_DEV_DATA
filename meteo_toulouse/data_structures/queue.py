"""
Structure de donnees: File (Queue) - First In, First Out.

Implementation d'une file basee sur une liste chainee.
Utilisee pour le carrousel de stations meteo (parcours cyclique).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Generic

from meteo_toulouse.config import T
from meteo_toulouse.data_structures.linked_list import ListNode


class Queue(Generic[T]):
    """
    Structure de donnees: File (Queue) - First In, First Out

    Implementation d'une file basee sur une liste chainee.
    Utilisee pour le carrousel de stations meteo (parcours cyclique).

    Principe FIFO: Le premier element ajoute est le premier retire.

    Complexite:
        - enqueue: O(1) - insertion en queue (avec pointeur tail)
        - dequeue: O(1) - suppression en tete
        - peek: O(1) - lecture de la tete
        - size: O(1) - compteur maintenu

    Attributes:
        _head: Premier element de la file (prochain a sortir).
        _tail: Dernier element de la file (dernier ajoute).
        _size: Nombre d'elements dans la file.
    """

    def __init__(self) -> None:
        """Initialise une file vide."""
        self._head: ListNode[T] | None = None
        self._tail: ListNode[T] | None = None
        self._size: int = 0

    def enqueue(self, value: T) -> None:
        """
        Ajoute un element a la fin de la file.

        Args:
            value: Valeur a ajouter.
        """
        new_node = ListNode(value)

        if self._tail is None:
            # File vide
            self._head = new_node
            self._tail = new_node
        else:
            # Ajout en fin
            self._tail.next = new_node
            self._tail = new_node

        self._size += 1

    def dequeue(self) -> T | None:
        """
        Retire et retourne l'element en tete de file.

        Returns:
            L'element retire ou None si la file est vide.
        """
        if self._head is None:
            return None

        value = self._head.value
        self._head = self._head.next

        if self._head is None:
            # La file est maintenant vide
            self._tail = None

        self._size -= 1
        return value

    def peek(self) -> T | None:
        """
        Retourne l'element en tete sans le retirer.

        Returns:
            L'element en tete ou None si la file est vide.
        """
        return self._head.value if self._head else None

    def is_empty(self) -> bool:
        """Verifie si la file est vide."""
        return self._head is None

    def size(self) -> int:
        """Retourne le nombre d'elements dans la file."""
        return self._size

    def rotate(self) -> None:
        """
        Rotation: deplace l'element de tete vers la queue.
        Utile pour le carrousel cyclique des stations.
        """
        if self._size <= 1:
            return

        # Deplace la tete vers la queue
        value = self.dequeue()
        if value is not None:
            self.enqueue(value)

    def to_list(self) -> list[T]:
        """Convertit la file en liste Python standard."""
        result: list[T] = []
        current = self._head
        while current is not None:
            result.append(current.value)
            current = current.next
        return result

    def __len__(self) -> int:
        """Retourne le nombre d'elements dans la file."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Iterateur pour parcourir la file."""
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __repr__(self) -> str:
        elements = [repr(item) for item in self]
        return f"Queue([{', '.join(elements)}])"
