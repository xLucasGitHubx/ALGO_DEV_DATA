"""
Structure de donnees: Table de Hachage (HashMap) avec Chainage.

Implementation d'un dictionnaire utilisant une table de hachage
avec gestion des collisions par chainage (listes chainees).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Generic

from meteo_toulouse.config import K, V
from meteo_toulouse.data_structures.linked_list import LinkedList, ListNode


@dataclass
class HashEntry(Generic[K, V]):
    """
    Entree d'une table de hachage (paire cle-valeur).

    Attributes:
        key: La cle de l'entree.
        value: La valeur associee a la cle.
    """
    key: K
    value: V


class HashMap(Generic[K, V]):
    """
    Structure de donnees: Table de Hachage (HashMap) avec Chainage

    Implementation d'un dictionnaire utilisant une table de hachage
    avec gestion des collisions par chainage (listes chainees).

    Chaque bucket contient une LinkedList d'entrees (HashEntry).
    Quand deux cles ont le meme hash, elles sont stockees dans
    la meme liste chainee.

    Complexite (cas moyen):
        - put: O(1)
        - get: O(1)
        - remove: O(1)
        - contains: O(1)

    Complexite (pire cas avec beaucoup de collisions):
        - Toutes operations: O(n)

    Attributes:
        _buckets: Tableau de listes chainees (buckets).
        _capacity: Nombre de buckets.
        _size: Nombre total d'entrees.
        _load_factor_threshold: Seuil pour le redimensionnement.
    """

    DEFAULT_CAPACITY = 16
    LOAD_FACTOR_THRESHOLD = 0.75

    def __init__(self, capacity: int = DEFAULT_CAPACITY) -> None:
        """
        Initialise une table de hachage vide.

        Args:
            capacity: Nombre initial de buckets.
        """
        self._capacity = max(1, capacity)
        self._buckets: list[LinkedList[HashEntry[K, V]]] = [
            LinkedList() for _ in range(self._capacity)
        ]
        self._size = 0

    def _hash(self, key: K) -> int:
        """
        Calcule l'index du bucket pour une cle.

        Args:
            key: La cle a hacher.

        Returns:
            L'index du bucket (0 <= index < capacity).
        """
        return hash(key) % self._capacity

    def _resize(self) -> None:
        """
        Redimensionne la table quand le facteur de charge depasse le seuil.
        Double la capacite et rehache toutes les entrees.
        """
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [LinkedList() for _ in range(self._capacity)]
        self._size = 0

        for bucket in old_buckets:
            for entry in bucket:
                self.put(entry.key, entry.value)

    def put(self, key: K, value: V) -> None:
        """
        Insere ou met a jour une paire cle-valeur.

        Args:
            key: La cle.
            value: La valeur a associer.
        """
        # Verifier si redimensionnement necessaire
        if self._size / self._capacity > self.LOAD_FACTOR_THRESHOLD:
            self._resize()

        index = self._hash(key)
        bucket = self._buckets[index]

        # Chercher si la cle existe deja
        current = bucket.head
        while current is not None:
            if current.value.key == key:
                # Mise a jour de la valeur existante
                current.value.value = value
                return
            current = current.next

        # Nouvelle entree
        bucket.append(HashEntry(key, value))
        self._size += 1

    def get(self, key: K, default: V | None = None) -> V | None:
        """
        Recupere la valeur associee a une cle.

        Args:
            key: La cle a rechercher.
            default: Valeur par defaut si cle non trouvee.

        Returns:
            La valeur associee ou default si non trouvee.
        """
        index = self._hash(key)
        bucket = self._buckets[index]

        for entry in bucket:
            if entry.key == key:
                return entry.value

        return default

    def remove(self, key: K) -> bool:
        """
        Supprime une entree par sa cle.

        Args:
            key: La cle a supprimer.

        Returns:
            True si l'entree a ete trouvee et supprimee.
        """
        index = self._hash(key)
        bucket = self._buckets[index]

        # Trouver l'entree a supprimer
        current = bucket.head
        prev = None

        while current is not None:
            if current.value.key == key:
                if prev is None:
                    # Suppression de la tete
                    bucket._head = current.next
                else:
                    prev.next = current.next
                bucket._size -= 1
                self._size -= 1
                return True
            prev = current
            current = current.next

        return False

    def contains(self, key: K) -> bool:
        """
        Verifie si une cle existe dans la table.

        Args:
            key: La cle a rechercher.

        Returns:
            True si la cle existe.
        """
        return self.get(key) is not None

    def keys(self) -> list[K]:
        """Retourne toutes les cles de la table."""
        result: list[K] = []
        for bucket in self._buckets:
            for entry in bucket:
                result.append(entry.key)
        return result

    def values(self) -> list[V]:
        """Retourne toutes les valeurs de la table."""
        result: list[V] = []
        for bucket in self._buckets:
            for entry in bucket:
                result.append(entry.value)
        return result

    def items(self) -> list[tuple[K, V]]:
        """Retourne toutes les paires cle-valeur."""
        result: list[tuple[K, V]] = []
        for bucket in self._buckets:
            for entry in bucket:
                result.append((entry.key, entry.value))
        return result

    def setdefault(self, key: K, default: V) -> V:
        """
        Retourne la valeur de la cle si elle existe,
        sinon insere default et le retourne.

        Args:
            key: La cle a rechercher/inserer.
            default: Valeur par defaut a inserer si cle absente.

        Returns:
            La valeur existante ou default.
        """
        existing = self.get(key)
        if existing is not None:
            return existing
        self.put(key, default)
        return default

    def __len__(self) -> int:
        """Retourne le nombre d'entrees dans la table."""
        return self._size

    def __contains__(self, key: K) -> bool:
        """Verifie si une cle existe (operateur 'in')."""
        return self.contains(key)

    def __getitem__(self, key: K) -> V:
        """Acces par cle avec crochets (operateur [])."""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V) -> None:
        """Affectation par cle avec crochets (operateur []=)."""
        self.put(key, value)

    def __iter__(self) -> Iterator[K]:
        """Iterateur sur les cles."""
        for bucket in self._buckets:
            for entry in bucket:
                yield entry.key

    def __repr__(self) -> str:
        items = [f"{k!r}: {v!r}" for k, v in self.items()]
        return f"HashMap({{{', '.join(items)}}})"
