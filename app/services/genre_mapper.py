"""Liste canonique des genres + réduction des genres granulaires.

Utilisée pour : les tags cliquables de DigsCover, le seed de la table Genre,
et le mapping des libellés externes s'ils reviennent un jour.

⚠️ L'ORDRE COMPTE dans GENRE_MAP : le premier mot-clé trouvé gagne.
   "reggaeton" contient "reggae"     → Reggaeton avant Reggae
   "hyperpop" contient "pop"         → Hyperpop avant Pop
   "melodic drill" contient "drill"  → Drill avant Hip-Hop
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

    ('Pop',         ['pop']),   # en dernier : attrape le reste
]

CANONICAL_GENRES = [name for name, _ in GENRE_MAP] + ['Other']

# Tags affichés en dur sur DigsCover, le reste derrière le bouton "..."
FEATURED_GENRES = ['Hip-Hop', 'Drill', 'Boom Bap', 'Trap', 'R&B', 'Soul',
                   'Afrobeats', 'Grime', 'Jazz', 'Indie', 'Electro', 'Pop']


def map_genre(raw_genres):
    """['melodic drill', 'uk rap'] → 'Drill'"""
    if not raw_genres:
        return 'Other'

    for raw in raw_genres:
        raw = raw.lower()
        for canonical, keywords in GENRE_MAP:
            if any(keyword in raw for keyword in keywords):
                return canonical

    return 'Other'
