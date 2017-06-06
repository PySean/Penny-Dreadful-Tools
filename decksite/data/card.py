from munch import Munch

from magic import oracle, rotation
from shared.database import sqlescape

from decksite.data import deck, guarantee
from decksite.database import db

def played_cards(where_clause='1 = 1'):
    sql = """
        SELECT
            card AS name,
            COUNT(card) AS n_decks_all,
            SUM(CASE WHEN sideboard THEN 0 ELSE 1 END) AS n_maindecks_all,
            SUM(CASE WHEN sideboard THEN 1 ELSE 0 END) AS n_sideboards_all,
            SUM(n) AS count_decks_all,
            SUM(CASE WHEN sideboard THEN 0 ELSE n END) AS count_maindecks_all,
            SUM(CASE WHEN sideboard THEN n ELSE 0 END) AS count_sideboards_all,
            SUM(d.wins) AS wins_all,
            SUM(d.losses) AS losses_all,
            SUM(d.draws) AS draws_all,
            ROUND((SUM(d.wins) / SUM(d.wins + d.losses)) * 100, 1) AS win_percent_all,

            SUM(CASE WHEN created_date >= %s THEN 1 ELSE 0 END) AS n_decks_season,
            SUM(CASE WHEN NOT sideboard AND created_date >= %s THEN 1 ELSE 0 END) AS n_maindecks_season,
            SUM(CASE WHEN sideboard AND created_date >= %s THEN 1 ELSE 0 END) AS n_sideboards_season,
            SUM(CASE WHEN created_date >= %s THEN n ELSE 0 END) AS count_decks_season,
            SUM(CASE WHEN NOT sideboard AND created_date >= %s THEN n ELSE 0 END) AS count_maindecks_season,
            SUM(CASE WHEN sideboard AND created_date >= %s THEN n ELSE 0 END) AS count_sideboards_season,
            SUM(CASE WHEN created_date >= %s THEN d.wins ELSE 0 END) AS wins_season,
            SUM(CASE WHEN created_date >= %s THEN d.losses ELSE 0 END) AS losses_season,
            SUM(CASE WHEN created_date >= %s THEN d.draws ELSE 0 END) AS draws_season,
            ROUND((SUM(CASE WHEN created_date >= %s THEN d.wins ELSE 0 END) / (SUM(CASE WHEN created_date >= %s THEN d.wins ELSE 0 END) + SUM(CASE WHEN created_date >= %s THEN d.losses ELSE 0 END))) * 100, 1) AS win_percent_season

        FROM deck_card AS dc
        INNER JOIN deck AS d ON dc.deck_id = d.id
        WHERE {where_clause}
        GROUP BY card
        ORDER BY n_decks_season DESC, count_decks_season DESC, n_maindecks_season DESC, count_maindecks_season DESC
    """.format(where_clause=where_clause)
    cs = [Munch(r) for r in db().execute(sql, [rotation.last_rotation().timestamp()] * 12)]
    cards = {c.name: c for c in oracle.load_cards()}
    for c in cs:
        c.update(cards[c.name])
    return cs

def load_card(name):
    c = guarantee.exactly_one(oracle.load_cards([name]))
    c.decks = deck.load_decks('d.id IN (SELECT deck_id FROM deck_card WHERE card = {name})'.format(name=sqlescape(name)))
    c.wins = sum(filter(None, [d.wins for d in c.decks]))
    c.losses = sum(filter(None, [d.losses for d in c.decks]))
    c.draws = sum(filter(None, [d.draws for d in c.decks]))
    c.played_competitively = c.wins or c.losses or c.draws
    return c

def only_played_by(person_id):
    sql = """
        SELECT card AS name, p.id
        FROM deck_card AS dc
        INNER JOIN deck AS d ON d.id = dc.deck_id
        INNER JOIN person AS p ON p.id = d.person_id
        GROUP BY card
        HAVING COUNT(DISTINCT p.id) = 1 AND p.id = {person_id}
    """.format(person_id=sqlescape(person_id))
    cs = [Munch(r) for r in db().execute(sql)]
    cards = {c.name: c for c in oracle.load_cards()}
    for c in cs:
        c.update(cards[c.name])
    return cs
