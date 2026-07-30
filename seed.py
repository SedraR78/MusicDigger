"""Script de peuplement de la base pour la démonstration.

Lancement :
    python seed.py

Il appelle les MÊMES services que l'application (DigService, Upvote.toggle...)
plutôt que d'insérer directement en base. Deux avantages : les données créées
sont forcément cohérentes (compteurs, cache, genres), et le script teste le
code métier en même temps qu'il remplit la base.

⚠️ Les DIGs sont volontairement CROISÉS entre comptes : plusieurs personnes
digent les mêmes morceaux. C'est indispensable pour que le filtrage
collaboratif de DigsCover ait des voisins et puisse sortir "Fans also dig this".
"""

from app import create_app, db
from app.models import User, Dig, Upvote, Redig, Comment, Follow, Conversation
from app.services.dig_service import DigService
from app.services.message_service import MessageService
from app.services.genre_mapper import CANONICAL_GENRES
from app.models import Genre

app = create_app()

# ============================================================
# LES COMPTES
# ============================================================

USERS = [
    ('alexwaves',   'alex@musicdigger.test',   'Digging since the tape era. UK rap mostly.'),
    ('juliemoon',   'julie@musicdigger.test',  'Boom bap purist. If it ain\'t sampled I don\'t trust it.'),
    ('samecho',     'sam@musicdigger.test',    'Drill, trap, and everything loud.'),
    ('beatlover',   'beat@musicdigger.test',   'Producer. I listen for the drums.'),
    ('melodymind',  'melody@musicdigger.test', 'R&B, soul, and late night tunes.'),
    ('lostinmusic', 'lost@musicdigger.test',   'No genre, just good music.'),
]

PASSWORD = 'password123'

# ============================================================
# LES DIGS : (username, requête de recherche, avis)
# ============================================================
# Les mêmes morceaux reviennent chez plusieurs users : c'est ce qui crée
# les voisinages pour le filtrage collaboratif.

DIGS = [
    ('alexwaves', 'You Cant Stop The Reign Shaq Notorious BIG',
     'Shaq on a Biggie track and it actually goes. People slept on this way too hard.'),

    ('juliemoon', 'Party And Bullshit Notorious BIG',
     'The energy on this is untouchable. You can hear the whole era in one track.'),

    ('samecho', 'Left Right YG',
     'West coast bounce, nothing else needed. This one clears a room in two seconds.'),

    ('beatlover', 'Dog Food 42 Dugg',
     'The drums on this are filthy. Dugg does more with less than anyone right now.'),

    ('alexwaves', 'Woi Digga D',
     'Digga D writes bars that stick in your head for days. UK at its sharpest.'),

    ('melodymind', 'Cosa Nostra Youngs Teflon',
     'Teflon never misses. Cold delivery, cold beat, cold everything.'),

    ('lostinmusic', 'Halftime Nas',
     'Illmatic era Nas is a different animal. Every line lands.'),

    ('juliemoon', 'Shook Ones Part II Mobb Deep',
     'Nothing has ever sounded this cold. The piano loop alone is a whole mood.'),

    ('samecho', 'Money Trees Kendrick Lamar',
     'That beat flip is criminal. Kendrick and Jay Rock trading bars, no notes.'),

    ('beatlover', 'Whos Real Jadakiss',
     'Jada punchline after punchline. Underrated by people who never listened.'),

    ('melodymind', 'Breathe Fabolous',
     'Fab on Just Blaze production is a formula that never failed.'),

    ('alexwaves', 'Talkin Da Hardest Giggs',
     'Giggs changed how UK rap sounded. Voice like a bassline.'),

    # --- Croisements pour la co-occurrence ---
    ('samecho', 'Party And Bullshit Notorious BIG',
     'Julie put me onto this one. Instant classic, no argument.'),

    ('lostinmusic', 'Left Right YG',
     'Found this through the feed. Been on repeat all week.'),

    ('beatlover', 'Halftime Nas',
     'The Large Professor beat is the real story here. Perfect drums.'),

    ('juliemoon', 'Woi Digga D',
     'Not my usual thing but the writing is undeniable.'),
]

# ============================================================
# LES FOLLOWS : (qui suit, qui est suivi)
# ============================================================

FOLLOWS = [
    ('alexwaves', 'juliemoon'),
    ('alexwaves', 'samecho'),
    ('alexwaves', 'beatlover'),
    ('juliemoon', 'alexwaves'),
    ('juliemoon', 'lostinmusic'),
    ('samecho', 'alexwaves'),
    ('samecho', 'beatlover'),
    ('beatlover', 'melodymind'),
    ('beatlover', 'juliemoon'),
    ('melodymind', 'lostinmusic'),
    ('lostinmusic', 'alexwaves'),
    ('lostinmusic', 'samecho'),
]

# ============================================================
# LES COMMENTAIRES : (username, index du dig, contenu)
# ============================================================

COMMENTS = [
    ('samecho', 0, 'Never expected Shaq to hold his own on this.'),
    ('juliemoon', 0, 'Production is what carries it honestly.'),
    ('beatlover', 2, 'That bassline is the whole track.'),
    ('alexwaves', 3, 'Dugg is the most consistent right now, no debate.'),
    ('melodymind', 7, 'Cold is the only word for it.'),
    ('lostinmusic', 8, 'Best beat switch of the decade.'),
]

# ============================================================
# LES UPVOTES : (username, index du dig)
# ============================================================

UPVOTES = [
    ('samecho', 0), ('juliemoon', 0), ('beatlover', 0), ('melodymind', 0), ('lostinmusic', 0),
    ('alexwaves', 1), ('samecho', 1), ('beatlover', 1), ('lostinmusic', 1),
    ('alexwaves', 2), ('beatlover', 2), ('melodymind', 2),
    ('alexwaves', 3), ('juliemoon', 3), ('samecho', 3), ('lostinmusic', 3),
    ('juliemoon', 4), ('samecho', 4),
    ('alexwaves', 5), ('beatlover', 5),
    ('juliemoon', 6), ('beatlover', 6), ('melodymind', 6),
    ('alexwaves', 7), ('samecho', 7), ('beatlover', 7), ('lostinmusic', 7),
    ('alexwaves', 8), ('juliemoon', 8),
    ('melodymind', 9),
    ('alexwaves', 10),
    ('samecho', 11), ('juliemoon', 11),
]

# ============================================================
# LES REDIGS : (username, index du dig)
# ============================================================

REDIGS = [
    ('samecho', 0), ('lostinmusic', 0),
    ('alexwaves', 1), ('beatlover', 1),
    ('melodymind', 2),
    ('juliemoon', 3), ('samecho', 3),
    ('beatlover', 7), ('alexwaves', 7),
]

# ============================================================
# LES CONVERSATIONS : (expéditeur, destinataire, message, index du dig ou None)
# ============================================================

MESSAGES = [
    ('alexwaves', 'juliemoon', 'Yo you need to hear this one', 0),
    ('juliemoon', 'alexwaves', 'Already on it, been in my rotation', None),
    ('alexwaves', 'juliemoon', 'Told you Shaq had bars', None),
    ('juliemoon', 'alexwaves', 'The production carries it but yeah, fair', None),

    ('samecho', 'beatlover', 'Check the drums on this', 3),
    ('beatlover', 'samecho', 'Filthy. Who produced it?', None),

    ('melodymind', 'lostinmusic', 'This is your kind of thing', 5),
]


def seed():
    with app.app_context():

        # ---------- 1. Les genres canoniques ----------
        # On les crée d'avance pour que le panneau de critères de DigsCover
        # ait des tags même avant qu'un morceau soit classé.
        print('Seeding genres...')
        for name in CANONICAL_GENRES:
            if Genre.query.filter_by(name=name).first() is None:
                db.session.add(Genre(name=name))
        db.session.commit()
        print(f'  {Genre.query.count()} genres')

        # ---------- 2. Les comptes ----------
        print('Seeding users...')
        users = {}
        for username, email, bio in USERS:
            user = User.query.filter_by(username=username).first()
            if user is None:
                user = User(username=username, email=email, bio=bio)
                user.set_password(PASSWORD)
                user.save()
                print(f'  + {username}')
            users[username] = user

        # ---------- 3. Les DIGs ----------
        # On passe par DigService, donc chaque dig déclenche la vraie chaîne :
        # recherche Spotify (ou YouTube), mise en cache du track, de l'artiste,
        # de l'album, et résolution du genre.
        print('Seeding digs (this calls Spotify, be patient)...')
        digs = []
        for username, query, content in DIGS:
            try:
                results = DigService.search_tracks(query, limit=1)
                if not results:
                    print(f'  ! not found: {query}')
                    digs.append(None)
                    continue

                track = results[0]
                dig = DigService.create_dig(
                    user_id=users[username].id,
                    content=content,
                    source=track['source'],
                    external_id=track['external_id'],
                )
                digs.append(dig)
                print(f'  + [{track["source"]}] {dig.display_title} - {dig.display_artist}')
            except Exception as exc:
                print(f'  ! failed on "{query}": {exc}')
                digs.append(None)

        # ---------- 4. Les follows ----------
        print('Seeding follows...')
        for follower, followed in FOLLOWS:
            try:
                Follow.toggle(users[follower].id, users[followed].id)
            except Exception:
                pass
        print(f'  {Follow.query.count()} follows')

        # ---------- 5. Les upvotes ----------
        print('Seeding upvotes...')
        for username, index in UPVOTES:
            if index < len(digs) and digs[index] is not None:
                Upvote.toggle(users[username].id, digs[index])
        print(f'  {Upvote.query.count()} upvotes')

        # ---------- 6. Les redigs ----------
        print('Seeding redigs...')
        for username, index in REDIGS:
            if index < len(digs) and digs[index] is not None:
                dig = digs[index]
                if dig.user_id != users[username].id:   # pas son propre dig
                    Redig.toggle(users[username].id, dig)
        print(f'  {Redig.query.count()} redigs')

        # ---------- 7. Les commentaires ----------
        print('Seeding comments...')
        for username, index, content in COMMENTS:
            if index < len(digs) and digs[index] is not None:
                dig = digs[index]
                comment = Comment(content=content,
                                  user_id=users[username].id,
                                  dig_id=dig.id)
                db.session.add(comment)
                dig.comments_count += 1
        db.session.commit()
        print(f'  {Comment.query.count()} comments')

        # ---------- 8. Les conversations ----------
        print('Seeding conversations...')
        for sender, recipient, content, dig_index in MESSAGES:
            try:
                conversation = MessageService.start_conversation(
                    users[sender].id, recipient)

                dig_id = None
                if dig_index is not None and dig_index < len(digs):
                    if digs[dig_index] is not None:
                        dig_id = digs[dig_index].id

                MessageService.send_message(
                    sender_id=users[sender].id,
                    conversation_id=conversation.id,
                    content=content,
                    dig_id=dig_id,
                )
            except Exception as exc:
                print(f'  ! message failed: {exc}')
        print(f'  {Conversation.query.count()} conversations')

        # ---------- Résumé ----------
        print('\n--- Seed complete ---')
        print(f'Users:         {User.query.count()}')
        print(f'Digs:          {Dig.query.count()}')
        print(f'Upvotes:       {Upvote.query.count()}')
        print(f'Redigs:        {Redig.query.count()}')
        print(f'Comments:      {Comment.query.count()}')
        print(f'Follows:       {Follow.query.count()}')
        print(f'Conversations: {Conversation.query.count()}')
        print(f'\nLogin with any username above, password: {PASSWORD}')

        # Le top 5 du trending, pour vérifier le classement
        print('\n--- Trending top 5 ---')
        for dig in DigService.trending(limit=5):
            print(f'  {dig.score():>3} pts  {dig.display_title} - {dig.display_artist}')


if __name__ == '__main__':
    seed()
