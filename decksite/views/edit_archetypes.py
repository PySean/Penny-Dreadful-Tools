from typing import List

from decksite.data import deck, rule
from decksite.data.archetype import Archetype
from decksite.view import View
from magic.models import Deck


# pylint: disable=no-self-use
class EditArchetypes(View):
    def __init__(self, archetypes: List[Archetype], search_results: List[Deck], q: str, notq: str) -> None:
        super().__init__()
        self.archetypes = archetypes
        self.roots = [a for a in self.archetypes if a.is_root]
        self.queue = deck.load_decks(where='NOT d.reviewed', order_by='updated_date DESC')
        deck.load_queue_similarity(self.queue)
        rule.apply_rules_to_decks(self.queue)
        for d in self.queue:
            self.prepare_deck(d)
        self.has_search_results = len(search_results) > 0
        self.search_results = search_results
        for d in self.search_results:
            self.prepare_deck(d)
        self.query = q
        self.notquery = notq

    def page_title(self):
        return 'Edit Archetypes'
