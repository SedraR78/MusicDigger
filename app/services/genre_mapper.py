"""Réduit les genres granulaires de Spotify à une liste canonique.

Spotify renvoie "melodic drill", "cali rap", "escape room" — utilisable pour
un algorithme, illisible pour des tags cliquables. On mappe donc sur une liste
courte qui correspond aux tags de vibe des wireframes DigsCover.

⚠️ L'ORDRE COMPTE : le premier mot-clé trouvé gagne.
   "reggaeton" contient "reggae"  → Reggaeton avant Reggae
   "hyperpop" contient "pop"      → Hyperpop avant Pop
   "melodic drill" contient "drill" → Drill avant Hip-Hop
"""

GENRE_MAP = [
    ('Boom Bap',    ['boom bap', 'golden age hip hop', 'east coast hip hop']),
    ('Drill',       ['drill']),
    ('Phonk',       ['phonk', 'memphis']),
    ('Cloud Rap',   ['cloud rap', 'emo rap', 'sad rap']),
    ('Trap',        ['trap']),
    ('Grime',       ['grime']),
    ('Lo-Fi',       ['lo-fi', 'lofi', 'chillhop']),
    ('Hip-Hop',     ['hip hop', 'hiphop', 'rap', 'conscious', 'g funk']),

    ('Amapiano',    ['amapiano']),
    ('Afrobeats',   ['afrobeat', 'afroswing', 'afro pop', 'afropop', 'naija']),
    ('Reggaeton',   ['reggaeton', 'latin trap', 'perreo']),
    ('Dancehall',   ['dancehall', 'bashment']),
    ('Reggae',      ['reggae', 'dub', 'roots', 'ska']),
    ('Zouk',        ['zouk', 'kompa', 'kizomba', 'coupe decale']),
    ('Latin',       ['latin', 'salsa', 'bachata', 'cumbia', 'bossa', 'samba']),

    ('Gospel',      ['gospel', 'worship']),
    ('Neo-Soul',    ['neo soul', 'neo-soul', 'alternative r&b']),
    ('R&B',         ['r&b', 'rnb', 'new jack']),
    ('Soul',        ['soul', 'motown']),
    ('Funk',        ['funk', 'disco', 'boogie']),

    ('Jazz',        ['jazz', 'bebop', 'swing', 'fusion']),
    ('Blues',       ['blues', 'delta']),

    ('Jersey Club', ['jersey club', 'baltimore club', 'baile funk']),
    ('Drum & Bass', ['drum and bass', 'drum n bass', 'dnb', 'jungle', 'breakcore']),
    ('Garage',      ['uk garage', 'speed garage', '2-step']),
    ('House',       ['house', 'gqom']),
    ('Techno',      ['techno', 'minimal', 'acid']),
    ('Ambient',     ['ambient', 'drone']),
    ('Electro',     ['electro', 'edm', 'dubstep', 'synthwave', 'idm', 'dance']),

    ('Hyperpop',    ['hyperpop', 'glitch pop', 'digicore']),
    ('K-Pop',       ['k-pop', 'kpop', 'j-pop', 'jpop']),
    ('Bedroom Pop', ['bedroom', 'dream pop']),

    ('Shoegaze',    ['shoegaze', 'noise pop']),
    ('Punk',        ['punk', 'hardcore', 'emo']),
    ('Metal',       ['metal', 'doom', 'sludge']),
    ('Indie',       ['indie', 'alternative']),
    ('Rock',        ['rock', 'grunge', 'psychedelic']),

    ('Raï',         ['rai', 'chaabi', 'gnawa']),
    ('Français',    ['chanson', 'variete francaise', 'french pop']),
    ('Country',     ['country', 'americana', 'bluegrass', 'folk']),
    ('Classique',   ['classical', 'baroque', 'opera', 'orchestra']),
    ('Soundtrack',  ['soundtrack', 'score', 'anime', 'video game']),

    ('Pop',         ['pop']),   # en dernier : attrape tout ce qui reste
]

CANONICAL_GENRES = [name for name, _ in GENRE_MAP] + ['Other']

# Les tags affichés en dur sur DigsCover ; le reste derrière le bouton "..."
FEATURED_GENRES = ['Hip-Hop', 'R&B', 'Drill', 'Trap', 'Boom Bap', 'Afrobeats',
                   'Jazz', 'Soul', 'Indie', 'Electro', 'Pop', 'Reggae']


def map_genre(spotify_genres):
    """['melodic drill', 'uk rap'] → 'Drill'"""
    if not spotify_genres:
        return 'Other'

    for raw in spotify_genres:
        raw = raw.lower()
        for canonical, keywords in GENRE_MAP:
            if any(keyword in raw for keyword in keywords):
                return canonical

    return 'Other'
