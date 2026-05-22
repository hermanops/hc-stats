"""Card and Deck representations using integer encoding.

Cards are encoded as integers 0-51:
    rank = card // 4   (0=2 ... 12=Ace)
    suit = card %  4   (0=c, 1=d, 2=h, 3=s)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

RANKS = "23456789TJQKA"
SUITS = "cdhs"

# Face-card ranks (Jack, Queen, King, Ace)
FACE_RANKS: frozenset[int] = frozenset([9, 10, 11, 12])  # T=8 not a face card; J=9,Q=10,K=11,A=12

# Rank names
RANK_NAMES = {i: r for i, r in enumerate(RANKS)}
SUIT_NAMES = {i: s for i, s in enumerate(SUITS)}


@dataclass(frozen=True)
class Card:
    code: int  # 0-51

    @classmethod
    def from_str(cls, s: str) -> "Card":
        """Parse e.g. 'Ah', 'Tc', '2d'."""
        rank = RANKS.index(s[0].upper())
        suit = SUITS.index(s[1].lower())
        return cls(rank * 4 + suit)

    @property
    def rank(self) -> int:
        return self.code // 4

    @property
    def suit(self) -> int:
        return self.code % 4

    @property
    def is_face(self) -> bool:
        return self.rank in FACE_RANKS

    def __str__(self) -> str:
        return f"{RANKS[self.rank]}{SUITS[self.suit]}"

    def __repr__(self) -> str:
        return f"Card('{self}')"


@dataclass
class Deck:
    _cards: list[int] = field(default_factory=lambda: list(range(52)))
    _pos: int = field(default=0, init=False)

    def shuffle(self) -> None:
        random.shuffle(self._cards)
        self._pos = 0

    def deal(self) -> Card:
        c = Card(self._cards[self._pos])
        self._pos += 1
        return c

    def deal_n(self, n: int) -> list[Card]:
        return [self.deal() for _ in range(n)]

    def reset(self) -> None:
        self._pos = 0
