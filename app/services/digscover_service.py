"""Moteur de recommandation DigsCover.

Recommande des TRACKS du catalogue, pas des DIGs existants : sinon on ne
pourrait faire découvrir que des sons déjà postés, et personne ne pourrait
jamais être le premier à diguer un morceau.

Spotify ne fournissant plus les genres, le signal principal est le
COMPORTEMENT COMMUNAUTAIRE (co-occurrence de digs) plutôt que le contenu.
C'est du filtrage collaboratif : deux personnes qui digent les mêmes sons ont
probablement des goûts proches. Aucune dépendance à une API externe, et la
qualité s'améliore avec l'usage de la plateforme.
"""

import random

from app import db
from app.models import Track, Artist, Genre, Dig, UserHistory

# Pondération des signaux
W_ARTIST = 30        # même artiste que tes favoris ou tes digs
W_COOCCURRENCE = 25  # "fans also dig this"
W_ALBUM = 20         # même album qu'un de tes morceaux favoris
W_GENRE = 10         # bonus, seulement si le genre est renseigné
W_WILDCARD = 15      # part de hasard : évite d'enfermer dans la bulle


class DigsCoverService:

    # ==================== Chemin visiteur ====================

    @staticmethod
    def by_criteria(artists=None, songs=None, genres=None, limit=20):
        """Aucun compte : on ne travaille que sur les critères saisis."""
        query = Track.query
        filters = []

        if artists:
            names = [a.strip() for a in artists.split(',') if a.strip()]
            if names:
                ids = [a.id for a in Artist.query.filter(Artist.name.in_(names)).all()]
                if ids:
                    filters.append(Track.artist_id.in_(ids))

        if genres:
            names = [g.strip() for g in genres.split(',') if g.strip()]
            if names:
                ids = [g.id for g in Genre.query.filter(Genre.name.in_(names)).all()]
                if ids:
                    filters.append(Track.genre_id.in_(ids))

        if songs:
            for title in [s.strip() for s in songs.split(',') if s.strip()]:
                filters.append(Track.title.ilike(f'%{title}%'))

        if filters:
            query = query.filter(db.or_(*filters))

        tracks = query.limit(limit * 3).all()
        random.shuffle(tracks)
        return [(t, DigsCoverService._criteria_label(t)) for t in tracks[:limit]]

    # ==================== Chemin connecté ====================

    @staticmethod
    def for_user(user, limit=20):
        """Recommandations personnalisées, avec exclusion de l'historique."""

        artist_ids = DigsCoverService._artist_signals(user)
        album_ids = {t.album_id for t in user.favorite_tracks if t.album_id}
        genre_ids = {g.id for g in user.favorite_genres}
        cooccurrence = DigsCoverService._cooccurrence(user)

        seen_ids = UserHistory.seen_track_ids(user.id)
        query = Track.query
        if seen_ids:
            query = query.filter(~Track.id.in_(seen_ids))
        candidates = query.limit(300).all()

        scored = []
        for track in candidates:
            score, label = DigsCoverService._score(
                track, artist_ids, album_ids, genre_ids, cooccurrence)
            if score > 0:
                scored.append((score, track, label))

        scored.sort(key=lambda row: row[0], reverse=True)
        top = scored[:limit]
        random.shuffle(top)   # évite un ordre figé à chaque rechargement

        results = [(track, label) for _, track, label in top]
        UserHistory.mark_as_seen(user.id, [t for t, _ in results])
        return results

    # ==================== Les signaux ====================

    @staticmethod
    def _artist_signals(user):
        """Artistes que l'utilisateur apprécie, explicitement ou non.

        Quatre sources : ses favoris d'onboarding, les artistes de ses DIGs,
        de ses ReDigs, et des DIGs qu'il a upvotés.

        C'est ce qui rend un bouton "like" inutile : upvoter un DIG à propos
        d'un morceau est déjà un signal de goût sur ce morceau.
        """
        ids = {a.id for a in user.favorite_artists}

        for dig in user.digs:
            if dig.track and dig.track.artist_id:
                ids.add(dig.track.artist_id)

        for redig in user.redigs:
            if redig.dig and redig.dig.track and redig.dig.track.artist_id:
                ids.add(redig.dig.track.artist_id)

        for upvote in user.upvotes:
            if upvote.dig and upvote.dig.track and upvote.dig.track.artist_id:
                ids.add(upvote.dig.track.artist_id)

        return ids

    @staticmethod
    def _cooccurrence(user):
        """Filtrage collaboratif : « les fans de tes sons digent aussi ça ».

        Trois étapes :
            1. quels morceaux l'utilisateur a-t-il digés ou upvotés ?
            2. qui d'autre a digé ces mêmes morceaux ? (ses « voisins »)
            3. qu'ont digé ces voisins, en dehors de ce qu'il connaît déjà ?

        Retourne {track_id: nombre de voisins qui l'ont digé}. Plus le nombre
        est élevé, plus le signal est fort.

        Limite connue : le « cold start ». Un nouvel utilisateur sans activité
        n'a pas de voisins — d'où l'onboarding obligatoire qui fournit un
        premier signal de goût.
        """
        my_track_ids = set()
        for dig in user.digs:
            if dig.track_id:
                my_track_ids.add(dig.track_id)
        for upvote in user.upvotes:
            if upvote.dig and upvote.dig.track_id:
                my_track_ids.add(upvote.dig.track_id)

        if not my_track_ids:
            return {}

        neighbour_ids = {
            dig.user_id
            for dig in Dig.query.filter(Dig.track_id.in_(my_track_ids)).all()
            if dig.user_id != user.id
        }
        if not neighbour_ids:
            return {}

        counts = {}
        for dig in Dig.query.filter(Dig.user_id.in_(neighbour_ids)).all():
            if dig.track_id and dig.track_id not in my_track_ids:
                counts[dig.track_id] = counts.get(dig.track_id, 0) + 1

        return counts

    # ==================== Le scoring ====================

    @staticmethod
    def _score(track, artist_ids, album_ids, genre_ids, cooccurrence):
        """Additionne les signaux et retient le label du plus fort.

        Le label explique POURQUOI le morceau est recommandé. La reco est
        explicable, pas une boîte noire — l'inverse du problème que le
        produit dénonce.
        """
        score = 0
        best_weight = 0
        label = 'Fresh pick'

        if track.artist_id and track.artist_id in artist_ids:
            score += W_ARTIST
            if W_ARTIST > best_weight:
                best_weight = W_ARTIST
                name = track.artist.name if track.artist else 'this artist'
                label = f'Because you dig {name}'

        neighbours = cooccurrence.get(track.id, 0)
        if neighbours:
            # Plafonné pour qu'un morceau très populaire n'écrase pas tout
            weight = min(W_COOCCURRENCE, neighbours * 8)
            score += weight
            if weight > best_weight:
                best_weight = weight
                label = 'Fans also dig this'

        if track.album_id and track.album_id in album_ids:
            score += W_ALBUM
            if W_ALBUM > best_weight:
                best_weight = W_ALBUM
                label = 'From an album you like'

        if track.genre_id and track.genre_id in genre_ids:
            score += W_GENRE
            if W_GENRE > best_weight:
                best_weight = W_GENRE
                name = track.genre.name if track.genre else 'your taste'
                label = f'Matches your genre: {name}'

        score += random.randint(0, W_WILDCARD)
        return score, label

    # ==================== Divers ====================

    @staticmethod
    def _criteria_label(track):
        if track.genre:
            return f'Matches your genre: {track.genre.name}'
        if track.artist:
            return f'Because you like {track.artist.name}'
        return 'Fresh pick'

    @staticmethod
    def random_dig():
        """Un DIG au hasard, hors de toute personnalisation."""
        count = Dig.query.count()
        if count == 0:
            return None
        return Dig.query.offset(random.randrange(count)).first()
