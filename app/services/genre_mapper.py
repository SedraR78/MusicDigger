
"""Réduit les genres ultra-granulaires de Spotify à une liste canonique.

⚠️ L'ORDRE COMPTE : le premier mot-clé trouvé gagne.
Exemples de pièges évités par l'ordre ci-dessous :
  - "reggaeton" contient "reggae"      → Reggaeton doit passer AVANT Reggae
  - "hyperpop" et "k-pop" contiennent "pop" → avant Pop
  - "lo-fi hip hop" contient "hip hop" → Lo-Fi avant Hip-Hop
  - "melodic drill" contient "drill"   → Drill avant Hip-Hop
  - "dancehall" contient "dance"       → Dancehall avant Electro
"""

GENRE_MAP = [
    # --- Sous-genres rap : les plus spécifiques en premier ---
    ('Boom Bap',   ['boom bap', 'golden age hip hop', 'east coast hip hop']),
    ('Drill',      ['drill']),
    ('Phonk',      ['phonk', 'memphis']),
    ('Cloud Rap',  ['cloud rap', 'emo rap', 'sad rap']),
    ('Trap',       ['trap']),
    ('Grime',      ['grime', 'uk garage rap']),
    ('Lo-Fi',      ['lo-fi', 'lofi', 'chillhop']),

    # --- Rap générique (après ses sous-genres) ---
    ('Hip-Hop',    ['hip hop', 'hiphop', 'rap', 'conscious', 'g funk']),

    # --- Afro / Caraïbes / Latin ---
    ('Amapiano',   ['amapiano']),
    ('Afrobeats',  ['afrobeat', 'afroswing', 'afro pop', 'afropop', 'naija']),
    ('Reggaeton',  ['reggaeton', 'latin trap', 'perreo']),
    ('Dancehall',  ['dancehall', 'bashment']),
    ('Reggae',     ['reggae', 'dub', 'roots', 'ska']),
    ('Zouk',       ['zouk', 'kompa', 'kizomba', 'coupe decale']),
    ('Latin',      ['latin', 'salsa', 'bachata', 'cumbia', 'bossa', 'samba']),

    # --- Soul / R&B / Funk ---
    ('Gospel',     ['gospel', 'worship', 'spiritual']),
    ('Neo-Soul',   ['neo soul', 'neo-soul', 'alternative r&b']),
    ('R&B',        ['r&b', 'rnb', 'contemporary r&b', 'new jack']),
    ('Soul',       ['soul', 'motown', 'northern soul']),
    ('Funk',       ['funk', 'disco', 'boogie', 'p funk']),

    # --- Jazz / Blues ---
    ('Jazz',       ['jazz', 'bebop', 'hard bop', 'swing', 'fusion']),
    ('Blues',      ['blues', 'delta', 'boogie woogie']),

    # --- Électronique : sous-genres avant Electro ---
    ('Jersey Club',['jersey club', 'baltimore club', 'baile funk']),
    ('Drum & Bass',['drum and bass', 'drum n bass', 'dnb', 'jungle', 'breakcore']),
    ('Garage',     ['uk garage', 'speed garage', '2-step']),
    ('House',      ['house', 'deep house', 'tech house', 'gqom']),
    ('Techno',     ['techno', 'minimal', 'acid']),
    ('Ambient',    ['ambient', 'drone', 'new age']),
    ('Electro',    ['electro', 'edm', 'dubstep', 'synthwave', 'idm', 'dance']),

    # --- Pop : sous-genres avant Pop ---
    ('Hyperpop',   ['hyperpop', 'glitch pop', 'digicore']),
    ('K-Pop',      ['k-pop', 'kpop', 'j-pop', 'jpop']),
    ('Bedroom Pop',['bedroom', 'dream pop']),

    # --- Rock / Indie ---
    ('Shoegaze',   ['shoegaze', 'noise pop']),
    ('Punk',       ['punk', 'hardcore', 'emo']),
    ('Metal',      ['metal', 'doom', 'sludge', 'grindcore']),
    ('Indie',      ['indie', 'alternative', 'lo-fi rock']),
    ('Rock',       ['rock', 'grunge', 'psychedelic', 'garage rock']),

    # --- Autres ---
    ('Afro-Trap',  ['afro trap', 'afrotrap']),
    ('Raï',        ['rai', 'chaabi', 'gnawa']),
    ('Français',   ['chanson', 'variete francaise', 'french pop']),
    ('Country',    ['country', 'americana', 'bluegrass', 'folk']),
    ('Classique',  ['classical', 'baroque', 'opera', 'orchestra']),
    ('Soundtrack', ['soundtrack', 'score', 'anime', 'video game']),

    # --- Pop générique en dernier (attrape tout ce qui reste) ---
    ('Pop',        ['pop']),
]

CANONICAL_GENRES = [name for name, _ in GENRE_MAP] + ['Other']


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
