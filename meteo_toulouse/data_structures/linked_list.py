"""
Structure de donnees: Liste Chainee (Linked List).

Implementation d'une liste chainee simple generique avec operations
de base. Utilisee pour stocker les stations meteo et comme base
pour le HashMap (chainage des collisions).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Generic, Callable

from meteo_toulouse.config import T


class ListNode(Generic[T]):
    """
    Noeud d'une liste chainee.

    Attributes:
        value: La valeur stockee dans le noeud.
        next: Reference vers le noeud suivant (ou None si dernier).
    """

    def __init__(self, value: T) -> None:
        self.value: T = value
        self.next: ListNode[T] | None = None

    def __repr__(self) -> str:
        return f"ListNode({self.value!r})"


class LinkedList(Generic[T]):
    """
    Structure de donnees: Liste Chainee (Linked List)

    Implementation d'une liste chainee simple avec operations de base.
    Utilisee pour stocker les stations meteo et comme base pour la Queue
    et le HashMap (chainage pour collisions).

    Complexite:
        - append: O(n) - parcours jusqu'a la fin
        - prepend: O(1) - insertion en tete
        - remove: O(n) - recherche + suppression
        - __contains__: O(n) - recherche lineaire
        - __len__: O(n) - comptage des noeuds
        - __iter__: O(n) - parcours complet

    Attributes:
        head: Premier noeud de la liste (ou None si vide).
    """

    def __init__(self) -> None:
        """Initialise une liste chainee vide."""
        self._head: ListNode[T] | None = None
        self._size: int = 0

    @property
    def head(self) -> ListNode[T] | None:
        """Retourne le premier noeud de la liste."""
        return self._head

    def is_empty(self) -> bool:
        """Verifie si la liste est vide."""
        return self._head is None

    def append(self, value: T) -> None:
        """
        Ajoute un element a la fin de la liste.

        Args:
            value: Valeur a ajouter.
        """
        new_node = ListNode(value)
        if self._head is None:
            self._head = new_node
        else:
            current = self._head
            while current.next is not None:
                current = current.next
            current.next = new_node
        self._size += 1

    def prepend(self, value: T) -> None:
        """
        Ajoute un element au debut de la liste.

        Args:
            value: Valeur a ajouter.
        """
        new_node = ListNode(value)
        new_node.next = self._head
        self._head = new_node
        self._size += 1

    def remove(self, value: T) -> bool:
        """
        Supprime la premiere occurrence d'une valeur.

        Args:
            value: Valeur a supprimer.

        Returns:
            True si l'element a ete trouve et supprime, False sinon.
        """
        if self._head is None:
            return False

        # Cas special: suppression de la tete
        if self._head.value == value:
            self._head = self._head.next
            self._size -= 1
            return True

        # Recherche dans le reste de la liste
        current = self._head
        while current.next is not None:
            if current.next.value == value:
                current.next = current.next.next
                self._size -= 1
                return True
            current = current.next

        return False

    def get(self, index: int) -> T | None:
        """
        Recupere l'element a l'index donne.

        Args:
            index: Index de l'element (0-based).

        Returns:
            La valeur a l'index ou None si index invalide.
        """
        if index < 0 or index >= self._size:
            return None

        current = self._head
        for _ in range(index):
            if current is None:
                return None
            current = current.next

        return current.value if current else None

    def find(self, predicate: Callable[[T], bool]) -> T | None:
        """
        Trouve le premier element satisfaisant le predicat.

        Args:
            predicate: Fonction de test retournant True si l'element correspond.

        Returns:
            Le premier element correspondant ou None.
        """
        for item in self:
            if predicate(item):
                return item
        return None

    def to_list(self) -> list[T]:
        """Convertit la liste chainee en liste Python standard."""
        return list(self)

    def __contains__(self, value: T) -> bool:
        """Verifie si une valeur est presente dans la liste."""
        for item in self:
            if item == value:
                return True
        return False

    def __len__(self) -> int:
        """Retourne le nombre d'elements dans la liste."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Iterateur pour parcourir la liste."""
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __repr__(self) -> str:
        elements = [repr(item) for item in self]
        return f"LinkedList([{', '.join(elements)}])"
