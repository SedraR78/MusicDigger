"""Peuplement étendu de la base pour la démonstration.

Lancement :
    python seed_big.py

À lancer APRÈS seed.py (ou à la place). Le script est ré-exécutable sans
risque : il saute les utilisateurs déjà créés, et il saute un DIG si la même
personne a déjà digé le même morceau.

⚠️ Chaque DIG déclenche un appel à Spotify. Sur ~170 entrées, comptez
plusieurs minutes. Les échecs sont affichés mais n'interrompent pas le script.

Les DIGs sont volontairement CROISÉS entre comptes : plusieurs personnes
digent les mêmes morceaux, ce qui donne des voisins au filtrage collaboratif
de DigsCover et fait apparaître le label "Fans also dig this".
"""

import random

from app import create_app, db
from app.models import (User, Dig, Track, Upvote, Redig, Comment,
                        Follow, Conversation, Genre)
from app.services.dig_service import DigService
from app.services.message_service import MessageService
from app.services.genre_mapper import CANONICAL_GENRES

app = create_app()

PASSWORD = 'password123'

# ============================================================
# LES COMPTES
# ============================================================

USERS = [
    ('alexwaves',    'alex@musicdigger.test',    'Digging since the tape era. UK rap mostly.'),
    ('juliemoon',    'julie@musicdigger.test',   "Boom bap purist. If it ain't sampled I don't trust it."),
    ('samecho',      'sam@musicdigger.test',     'Drill, trap, and everything loud.'),
    ('beatlover',    'beat@musicdigger.test',    'Producer. I listen for the drums.'),
    ('melodymind',   'melody@musicdigger.test',  'R&B, soul, and late night tunes.'),
    ('lostinmusic',  'lost@musicdigger.test',    'No genre, just good music.'),
    ('crateking',    'crate@musicdigger.test',   'Sample hunter. I find the loop before the loop finds you.'),
    ('barsonly',     'bars@musicdigger.test',    'Here for the writing. Beat is a bonus.'),
    ('lowendtheory', 'lowend@musicdigger.test',  '808s, basslines, and rooms that shake.'),
    ('parisdigger',  'paris@musicdigger.test',   'Rap FR, du 95 au 13. Et un peu de tout le reste.'),
    ('nightshift',   'night@musicdigger.test',   'Music for 3am. Nothing before midnight.'),
    ('vinylcurse',   'vinyl@musicdigger.test',   'Jazz, funk, soul. The stuff everything else is built on.'),
    ('roadrap',      'road@musicdigger.test',    'UK road rap and drill. From Peckham to Tottenham.'),
    ('sunsetdrive',  'sunset@musicdigger.test',  'West coast, g-funk, and anything with a whine on it.'),
]

# ============================================================
# LES DIGS : (username, requête Spotify, avis)
# ============================================================

DIGS = [

    # ---------------- BOOM BAP / 90s NY ----------------

    ('juliemoon', 'NY State of Mind Nas',
     'The piano loop comes in and you already know what kind of record this is. '
     '"I never sleep, cause sleep is the cousin of death" — he opens with that and never lets go. '
     'Premier gave him a beat that sounds like a stairwell in winter and Nas wrote a documentary over it.'),

    ('crateking', 'The World Is Yours Nas',
     'Pete Rock flipped Ahmad Jamal and made the most hopeful sounding beat on a very bleak album. '
     'That contrast is the whole point of Illmatic.'),

    ('barsonly', 'Ten Crack Commandments Notorious BIG',
     'Ten rules, ten bars each, no wasted syllables. Most rappers need a whole album to be this clear. '
     'The DJ Premier count-in is iconic for a reason.'),

    ('juliemoon', 'Juicy Notorious BIG',
     'Every rags to riches song since 1994 is trying to be this one. '
     '"Birthdays was the worst days, now we sip champagne when we thirsty" — that is the entire genre in one line.'),

    ('lostinmusic', 'Warning Notorious BIG',
     'A whole home invasion movie in three minutes. He plays both characters and you follow every beat of it.'),

    ('crateking', 'CREAM Wu-Tang Clan',
     'RZA sped up a Charmels sample and built a monument. Raekwon and Inspectah Deck both turn in career verses.'),

    ('barsonly', 'Liquid Swords GZA',
     'GZA raps like a chess player. Nothing is wasted, everything sets up the next move. '
     'And RZA gave him the coldest, dustiest beats he ever made.'),

    ('juliemoon', 'Shook Ones Pt II Mobb Deep',
     'Nothing has ever sounded this cold. The piano loop alone is a whole mood, '
     'and Prodigy was 19 writing "I got you stuck off the realness".'),

    ('crateking', 'They Reminisce Over You Pete Rock CL Smooth',
     'A eulogy that makes you want to dance. That sax loop is one of the most recognisable four seconds in rap.'),

    ('barsonly', 'Mass Appeal Gang Starr',
     'Guru had the most unbothered delivery in rap history. He never raised his voice and never needed to.'),

    ('lostinmusic', 'Electric Relaxation A Tribe Called Quest',
     'The most relaxed a rap song has ever sounded. Ronnie Foster loop, Q-Tip and Phife just floating on it.'),

    ('juliemoon', 'Put It On Big L',
     'Big L was punchline rap before punchline rap had a name. '
     'The difference is his punchlines actually landed. Gone way too early.'),

    ('crateking', 'Dead Presidents II Jay-Z',
     'Jay took a Nas vocal for the hook and then spent a decade proving he deserved it. '
     'Ski Beatz on the boards, Lonnie Liston Smith on the loop.'),

    ('barsonly', 'Incarcerated Scarfaces Raekwon',
     'Purple tape era Rae is the most quotable rapper of the decade. '
     'The imagery is so specific you can see the room.'),

    # ---------------- WEST COAST ----------------

    ('sunsetdrive', 'Ambitionz Az A Ridah 2Pac',
     'The intro alone changes the temperature of a room. All Eyez On Me opens like a threat and never softens.'),

    ('sunsetdrive', 'California Love 2Pac Dr Dre',
     'Roger Troutman on the talkbox, Dre on the beat, Pac fresh out. '
     'Some records are just a moment in time captured perfectly.'),

    ('lostinmusic', 'Hail Mary 2Pac',
     'The most haunted rap song ever recorded. That organ line sounds like a church that has seen things.'),

    ('sunsetdrive', 'Nuthin But A G Thang Dr Dre',
     'The blueprint for an entire coast. Snoop sounds like he was born on this beat.'),

    ('sunsetdrive', 'Gin and Juice Snoop Dogg',
     'Nobody has ever sounded more comfortable on a record. Snoop is barely trying and it is perfect.'),

    ('samecho', 'Money Trees Kendrick Lamar',
     'That beat flip is criminal. Kendrick and Jay Rock trading bars, no notes. '
     'The Beach House sample played backwards is why it sounds like a memory.'),

    ('barsonly', 'm.A.A.d city Kendrick Lamar',
     'Two beats, two Kendricks. The switch halfway through is one of the best structural decisions in modern rap.'),

    ('lostinmusic', 'Alright Kendrick Lamar',
     'A protest song that people actually sang in the street. Very few records earn that.'),

    ('samecho', 'DNA Kendrick Lamar',
     'The beat switch at "I got, I got, I got" is the single hardest moment on DAMN. Mike Will earned that one.'),

    ('samecho', 'Left Right YG',
     'West coast bounce, nothing else needed. This one clears a room in two seconds.'),

    ('sunsetdrive', 'Big Bank YG',
     'Nicki takes the whole song and nobody minds because the beat is that fun.'),

    ('sunsetdrive', "Last Time That I Checc'd Nipsey Hussle",
     'Nipsey never sounded rushed. Every bar arrives exactly when it should. Still hurts.'),

    ('lowendtheory', 'Collard Greens ScHoolboy Q',
     'The bassline does all the work and Q just rides it. Kendrick shows up speaking Spanish for no reason. Perfect.'),

    # ---------------- SOUTH / TRAP ----------------

    ('lostinmusic', 'Ms Jackson Outkast',
     'A breakup song, an apology to a mother-in-law, and a pop hit at the same time. '
     'Outkast were operating on a level nobody else reached.'),

    ('crateking', 'BOB Outkast',
     'Drum and bass, gospel choir, guitar solo, and rapping at double time. In 2000. On a rap album.'),

    ('barsonly', "Int'l Players Anthem UGK Outkast",
     'Andre 3000 raps the first verse with no drums and it is still the best verse on the song. '
     'Pimp C comes in on the beat drop and the whole thing takes off.'),

    ('samecho', 'Mask Off Future',
     'That flute is one of the most recognisable four bars of the decade. Metro turned a Tommy Butler sample into a stadium.'),

    ('samecho', 'March Madness Future',
     'DS2 era Future is a whole mood. Codeine sadness over triumphant drums, which should not work and completely does.'),

    ('lowendtheory', 'Best Friend Young Thug',
     'Thug uses his voice like an instrument. Nobody was doing melody like this in 2015.'),

    ('samecho', 'Lemonade Gucci Mane',
     'Everything in the song is yellow. It should be a gimmick and instead it is one of his best.'),

    ('barsonly', 'a lot 21 Savage',
     'The most restrained he has ever sounded, and the most affecting. J Cole verse is genuinely great too.'),

    ('lowendtheory', 'Drip Too Hard Lil Baby Gunna',
     'Two rappers who sound like the same person, on a beat built entirely out of one hook. And it works.'),

    ('beatlover', 'Dog Food 42 Dugg',
     'The drums on this are filthy. Dugg does more with less than anyone right now, '
     'and that voice cuts through a mix like nothing else.'),

    ('samecho', 'We Paid Lil Baby 42 Dugg',
     'Dugg whistling into the beat is the best ad-lib of the decade, I will not be taking questions.'),

    ('samecho', 'Bad and Boujee Migos',
     'Say what you want, the Offset verse changed the flow of an entire generation of rappers.'),

    ('lowendtheory', 'Magnolia Playboi Carti',
     'Pi\'erre Bourne made a beat out of pure sugar and Carti barely says anything. Still undeniable.'),

    ('samecho', 'SICKO MODE Travis Scott',
     'Three songs in one, and all three are good. The transition into the Swae Lee part is the best moment on ASTROWORLD.'),

    ('nightshift', 'goosebumps Travis Scott',
     'The most nocturnal song in his catalogue. Kendrick shows up at the end like a plot twist.'),

    # ---------------- UK DRILL / ROAD RAP ----------------

    ('alexwaves', 'Woi Digga D',
     'Digga D writes bars that stick in your head for days. UK at its sharpest.'),

    ('roadrap', "Chingy It's Whatever Digga D",
     'The flow switches three times and never loses the beat. He makes it sound easy, it is not.'),

    ('roadrap', 'Doja Central Cee',
     'A whole hit built on a Eve sample and one line. Cench understood the internet better than anyone.'),

    ('roadrap', 'Sprinter Central Cee Dave',
     'Two of the biggest in the country trading bars and actually trying. The Dave verse is the better one.'),

    ('roadrap', 'Both Headie One',
     'Headie has the most distinctive cadence in UK drill. He raps slightly behind the beat and it makes everything hit harder.'),

    ('samecho', 'Homerton B Unknown T',
     'The song that made drill go pop in the UK without losing anything. That bassline is enormous.'),

    ('roadrap', 'Body Russ Millions Tion Wayne',
     'Number one in the UK with a drill record. Whatever you think of it, that mattered.'),

    ('alexwaves', 'Talkin the Hardest Giggs',
     'Giggs changed how UK rap sounded. Voice like a bassline, and he never rushes a single bar.'),

    ('alexwaves', 'Whippin Excursion Giggs',
     'That laugh in the middle of the verse is more menacing than most rappers shouting.'),

    ('roadrap', 'Yeah Yeah Nines',
     'Nines writes like a novelist. Every song on Crop Circle is a chapter of the same story.'),

    ('roadrap', 'Gangsteritus Potter Payper',
     'Potter is the most honest writer in UK rap. No posturing, just consequences.'),

    ('alexwaves', 'Titanium Dave',
     'Dave over a piano is the most reliable formula in British music right now.'),

    ('alexwaves', 'Starlight Dave',
     'A summer song from someone who mostly does not make summer songs. Still sounds like him.'),

    ('crateking', 'Los Pollos Hermanos Knucks',
     'Knucks produces and raps and neither suffers. That jazz loop over drill drums should not work.'),

    ('alexwaves', 'Shutdown Skepta',
     'The moment grime came back. Minimal beat, maximum presence.'),

    ('alexwaves', "That's Not Me Skepta JME",
     'Two brothers on a beat that costs about eight pounds to make, and it reset the entire scene.'),

    ('roadrap', 'Shut Up Stormzy',
     'Recorded over an old instrumental in a park. Went to number eight. The scene needed that reminder.'),

    ('alexwaves', 'Skengman Ghetts',
     'Ghetts has the most aggressive pen in the country. He sounds like he is arguing with the beat.'),

    ('alexwaves', 'Did You See J Hus',
     'Nobody else sounds like Hus. Afrobeats, road rap, and pure charisma in the same three minutes.'),

    ('alexwaves', 'Common Sense J Hus',
     'The whole album is a genre nobody had named yet. This is the thesis statement.'),

    ('roadrap', 'Warm K-Trap',
     'The most underrated writer in London. Cold voice, colder observations.'),

    # ---------------- RAP FR ----------------

    ('parisdigger', 'Pitbull Booba',
     'Booba a inventé une manière de rapper que tout le monde a copiée ensuite. '
     'La voix, les images, la construction des punchlines — tout vient de là.'),

    ('parisdigger', 'DKR Booba',
     'Le beat est glacial et il pose dessus comme si de rien n\'était. Un classique instantané.'),

    ('parisdigger', 'Lettre à une femme Ninho',
     'Ninho écrit mieux quand il ralentit. Ce morceau prouve qu\'il peut faire autre chose que des hits.'),

    ('parisdigger', 'Jefe Ninho',
     'La technique est ridicule de facilité. Il change de flow trois fois sans jamais forcer.'),

    ('parisdigger', 'Otto SCH',
     'SCH a une ambiance que personne d\'autre n\'a. Cinématographique, un peu sale, toujours élégant.'),

    ('parisdigger', 'Macarena Damso',
     'Damso construit ses morceaux comme des scènes. Il y a un avant et un après dans chaque couplet.'),

    ('parisdigger', 'Au DD PNL',
     'PNL ont créé une esthétique complète — le son, les clips, le silence entre les projets. '
     'Ce morceau est le sommet de tout ça.'),

    ('parisdigger', 'Blanka PNL',
     'La mélancolie de PNL est unique en France. Personne ne fait sonner la tristesse comme ça.'),

    ('parisdigger', 'On verra Nekfeu',
     'Le refrain est tellement simple qu\'on oublie à quel point le premier couplet est écrit.'),

    ('parisdigger', 'Basique Orelsan',
     'Un morceau construit uniquement sur une contrainte, et c\'est devenu un phénomène. '
     'Orelsan comprend le format mieux que personne.'),

    ('parisdigger', 'La quête Orelsan',
     'Le morceau le plus honnête de son catalogue. Il parle de doute sans jamais s\'apitoyer.'),

    ('parisdigger', 'Yeux disent Lomepal',
     'Lomepal écrit comme quelqu\'un qui a lu. La métaphore tient sur tout le morceau sans jamais lâcher.'),

    ('parisdigger', 'Tchikita Jul',
     'On peut dire ce qu\'on veut sur Jul, ce morceau est increvable. La mélodie est imparable.'),

    ('parisdigger', 'Drill FR 4 Gazo',
     'Gazo a importé la drill en France et l\'a rendue immédiatement identifiable. La voix fait la moitié du travail.'),

    ('parisdigger', 'Freeze Raël Freeze Corleone',
     'Les références s\'empilent tellement vite qu\'il faut trois écoutes pour tout attraper. Le flow ne bouge jamais.'),

    ('parisdigger', 'Petit frère IAM',
     'Un morceau de 1997 qui n\'a pas pris une ride. Akhenaton écrivait des chroniques sociales sur des beats de soul.'),

    ('parisdigger', 'Demain c\'est loin IAM',
     'Neuf minutes, deux couplets, aucun refrain. Le morceau le plus ambitieux du rap français.'),

    ('parisdigger', 'Laisse pas traîner ton fils NTM',
     'Le refrain est un avertissement et le morceau entier est une lettre. NTM au sommet de leur écriture.'),

    ('parisdigger', 'Caroline MC Solaar',
     'Solaar a rendu le rap français radiophonique sans jamais le simplifier. Les jeux de mots tiennent encore.'),

    ('parisdigger', '365 jours Oxmo Puccino',
     'Oxmo est le meilleur styliste du rap FR. Chaque phrase est tournée deux fois avant d\'être posée.'),

    ('parisdigger', 'Zoo Kaaris',
     'Le beat de Therapy et cette voix. Kaaris a ouvert une porte que beaucoup ont franchie ensuite.'),

    ('parisdigger', 'Megatron Laylow',
     'Laylow fait de la science-fiction avec du rap. L\'univers est complet, du son à l\'image.'),

    ('parisdigger', 'Helsinki Dinos',
     'Dinos écrit sur la solitude mieux que quiconque en France. Ce morceau est un huis clos.'),

    ('parisdigger', 'Mélo Tiakola',
     'Tiakola a la voix la plus mélodique de sa génération. Il chante en rappant sans jamais choisir.'),

    # ---------------- R&B / SOUL / NEO-SOUL ----------------

    ('melodymind', 'Nights Frank Ocean',
     'Le beat switch au milieu est le meilleur moment de Blonde. '
     'La première moitié c\'est le jour, la deuxième c\'est trois heures du matin. Littéralement.'),

    ('melodymind', 'Pink + White Frank Ocean',
     'Pharrell sur la production, Beyoncé dans les chœurs, et personne ne s\'en aperçoit. '
     'C\'est ça la maîtrise.'),

    ('nightshift', 'Ivy Frank Ocean',
     'La guitare est désaccordée exprès. Tout le morceau sonne comme un souvenir qu\'on essaie de reconstituer.'),

    ('melodymind', 'Good Days SZA',
     'La voix flotte au-dessus du beat sans jamais s\'y poser. C\'est ce qui rend le morceau aussi aérien.'),

    ('melodymind', 'Snooze SZA',
     'La chanson d\'amour la plus adulte de son catalogue. Pas de drame, juste de la présence.'),

    ('nightshift', 'The Weekend SZA',
     'Un des sujets les plus casse-gueule en R&B, traité sans jugement et avec une mélodie imparable.'),

    ('melodymind', 'Trust Brent Faiyaz',
     'Brent a la voix la plus reconnaissable du R&B actuel. Et il l\'utilise pour dire des choses désagréables. J\'adore.'),

    ('nightshift', 'Girls Need Love Summer Walker',
     'Une production minimale et une voix qui ne force jamais. Le remix Drake est bien, l\'original est meilleur.'),

    ('vinylcurse', 'Untitled How Does It Feel D\'Angelo',
     'Enregistré presque entièrement par une seule personne. La basse et la voix respirent ensemble sur tout le morceau.'),

    ('vinylcurse', 'On & On Erykah Badu',
     'Baduizm a inventé un son. Cette basse et cette voix ont défini le neo-soul en un morceau.'),

    ('vinylcurse', 'Doo Wop That Thing Lauryn Hill',
     'Elle rappe le premier couplet, chante le second, et les deux sont au niveau. '
     'Cet album est un des rares parfaits.'),

    ('vinylcurse', "What's Going On Marvin Gaye",
     'Motown ne voulait pas le sortir. C\'est devenu un des disques les plus importants du siècle.'),

    ('vinylcurse', 'Move On Up Curtis Mayfield',
     'Neuf minutes de cuivres et d\'optimisme. Sample par tout le monde, égalé par personne.'),

    ('vinylcurse', "Let's Stay Together Al Green",
     'Al Green chantait comme s\'il ne voulait déranger personne, et c\'est pour ça que ça touche autant.'),

    ('vinylcurse', 'Superstition Stevie Wonder',
     'Le clavinet fait tout. Un des meilleurs riffs jamais enregistrés, tous genres confondus.'),

    ('lostinmusic', 'Billie Jean Michael Jackson',
     'La ligne de basse est jouée en boucle sans variation pendant six minutes et personne ne s\'ennuie. '
     'C\'est de l\'ingénierie autant que de la musique.'),

    ('melodymind', 'Rock With You Michael Jackson',
     'Quincy Jones à la production. Tout est à sa place et rien ne dépasse.'),

    ('melodymind', 'Are You That Somebody Aaliyah',
     'Timbaland a mis un bébé qui pleure dans le beat et en a fait un hit. Aaliyah rend tout facile.'),

    ('melodymind', "U Don't Have to Call Usher",
     'Neptunes production. Le beat est presque vide et c\'est exactement ce qu\'il fallait.'),

    ('nightshift', 'Back to Black Amy Winehouse',
     'Un disque de soul des années 60 enregistré en 2006 par quelqu\'un qui vivait vraiment les paroles.'),

    # ---------------- AFROBEATS ----------------

    ('lostinmusic', 'Last Last Burna Boy',
     'Burna a samplé Toni Braxton et en a fait un hymne de rupture pour tout un continent.'),

    ('lostinmusic', 'Ye Burna Boy',
     'Le morceau qui l\'a fait passer d\'artiste nigérian à artiste mondial, sans changer une virgule à son son.'),

    ('melodymind', 'Essence Wizkid Tems',
     'La chanson la plus douce de la décennie. Tems n\'a besoin que de huit mesures pour voler le morceau.'),

    ('lostinmusic', 'Calm Down Rema',
     'Une mélodie si simple qu\'elle a fait le tour du monde en six mois.'),

    ('lostinmusic', 'Lonely At The Top Asake',
     'Asake mélange amapiano, fuji et rap. Personne ne sonne comme lui en ce moment.'),

    ('melodymind', 'Free Mind Tems',
     'Cette voix ne ressemble à aucune autre. Grave, un peu voilée, et complètement à elle.'),

    ('vinylcurse', 'Water No Get Enemy Fela Kuti',
     'Tout l\'afrobeat vient de là. Le groove tient sur douze minutes sans jamais faiblir.'),

    # ---------------- JAZZ / FUNK ----------------

    ('vinylcurse', 'So What Miles Davis',
     'Deux accords sur tout le morceau. C\'est tout ce qu\'il fallait. Kind of Blue reste imbattable.'),

    ('vinylcurse', 'Naima John Coltrane',
     'Une ballade écrite pour sa femme. La plus belle chose qu\'il ait enregistrée.'),

    ('crateking', 'Cantaloupe Island Herbie Hancock',
     'Sample par Us3 et redécouvert par une génération entière. L\'original reste supérieur.'),

    ('vinylcurse', 'The Payback James Brown',
     'Sept minutes de menace sur un seul groove. Le sample le plus utilisé de l\'histoire du rap.'),

    ('crateking', 'Flash Light Parliament',
     'Bernie Worrell a joué la ligne de basse sur un synthé Moog. Ça a changé le funk pour toujours.'),

    ('crateking', 'Walk On By Isaac Hayes',
     'Douze minutes là où Dionne Warwick en faisait trois. Et chaque minute se justifie.'),

    # ---------------- ELECTRO ----------------

    ('nightshift', 'Around the World Daft Punk',
     'Une seule phrase répétée 144 fois. Et pourtant on ne s\'en lasse pas, parce que tout bouge autour.'),

    ('nightshift', 'One More Time Daft Punk',
     'La compression sur les cuivres est volontairement excessive. C\'est ce qui fait tout le morceau.'),

    ('nightshift', 'Genesis Justice',
     'Le disque qui a rendu la French touch agressive. Ça sonne encore comme le futur.'),

    ('nightshift', 'Xtal Aphex Twin',
     'Selected Ambient Works a trente ans et sonne toujours plus moderne que la moitié de ce qui sort.'),

    ('nightshift', 'Archangel Burial',
     'Du garage joué au ralenti sous la pluie. Personne n\'a réussi à copier cette ambiance.'),

    ('nightshift', 'Two Thousand and Seventeen Four Tet',
     'Une harpe, une boucle, et beaucoup de patience. Le morceau se construit sans qu\'on s\'en aperçoive.'),

    ('nightshift', 'Delilah Fred again',
     'Fred again transforme des enregistrements du quotidien en morceaux de club. Personne d\'autre ne fait ça.'),

    ('lowendtheory', 'Gosh Jamie xx',
     'Une intro de six minutes qui aurait pu durer vingt. Le drop arrive exactement quand il faut.'),

    # ---------------- REGGAE / DANCEHALL ----------------

    ('lostinmusic', 'Could You Be Loved Bob Marley',
     'Le reggae le plus dansant jamais écrit, avec un des textes les plus durs de son catalogue. '
     'Ce contraste est très Marley.'),

    ('lostinmusic', 'Fever Vybz Kartel',
     'Kartel a écrit la moitié de ses classiques depuis une cellule. Celui-ci en fait partie.'),

    ('lostinmusic', 'Family Popcaan',
     'Popcaan chante la loyauté sur un riddim solaire. Simple et imparable.'),

    ('lostinmusic', 'Toast Koffee',
     'Dix-neuf ans, un Grammy, et une énergie que personne ne peut simuler.'),

    ('lostinmusic', 'Skankin Sweet Chronixx',
     'Le reggae roots remis au goût du jour sans en trahir un seul principe.'),

    # ---------------- ROCK / INDIE ----------------

    ('lostinmusic', 'Karma Police Radiohead',
     'Le morceau bascule complètement dans les vingt dernières secondes et devient autre chose. '
     'Peu de groupes osent ça sur un single.'),

    ('nightshift', '505 Arctic Monkeys',
     'Un orgue, une montée, et une explosion à la fin. La structure la plus simple possible, parfaitement exécutée.'),

    ('lostinmusic', 'The Less I Know The Better Tame Impala',
     'Cette basse est une des meilleures lignes de la décennie, tous genres confondus.'),

    ('lostinmusic', 'Reptilia The Strokes',
     'Deux guitares qui jouent des choses différentes et qui s\'emboîtent parfaitement. Room on Fire est sous-estimé.'),

    ('lostinmusic', 'Smells Like Teen Spirit Nirvana',
     'Le riff a été écrit comme une blague sur les Pixies. Il a fini par redéfinir une décennie.'),

    ('lostinmusic', 'Where Is My Mind Pixies',
     'Utilisé partout, usé nulle part. Le morceau résiste à tous les mauvais usages qu\'on en a fait.'),

    # ---------------- POP ----------------

    ('melodymind', 'Needed Me Rihanna',
     'La production est presque vide et Rihanna ne force jamais. C\'est ce qui rend le morceau menaçant.'),

    ('melodymind', 'Blinding Lights The Weeknd',
     'Du synthpop des années 80 fait sans ironie et sans clin d\'œil. C\'est pour ça que ça marche.'),

    ('melodymind', 'Formation Beyoncé',
     'Un morceau de club, un manifeste, et un moment culturel. Les trois à la fois, sans compromis.'),

    # ---------------- CROISEMENTS (pour la co-occurrence) ----------------

    ('samecho', 'Juicy Notorious BIG',
     'Julie m\'a mis dessus. Impossible de faire un morceau plus définitif sur le sujet.'),

    ('alexwaves', 'Shook Ones Pt II Mobb Deep',
     'Le mètre-étalon. Tout ce que j\'écoute en drill descend de ce morceau d\'une manière ou d\'une autre.'),

    ('beatlover', 'NY State of Mind Nas',
     'Je reviens toujours à ce beat. Premier a mis quatre éléments dans le mix et pas un de plus.'),

    ('lowendtheory', 'Money Trees Kendrick Lamar',
     'La basse sur ce morceau est plus mélodique que la plupart des lignes de chant.'),

    ('crateking', 'Nights Frank Ocean',
     'Le switch tombe exactement au milieu de l\'album, à la seconde près. Ce genre de détail change tout.'),

    ('roadrap', 'Talkin the Hardest Giggs',
     'Le morceau qui a rendu possible tout ce que j\'écoute aujourd\'hui.'),

    ('parisdigger', 'Woi Digga D',
     'La drill UK a une énergie que la version française n\'a jamais tout à fait attrapée.'),

    ('melodymind', 'Billie Jean Michael Jackson',
     'On l\'a tellement entendu qu\'on oublie à quel point la production est étrange et audacieuse.'),

    ('juliemoon', 'Ms Jackson Outkast',
     'Le pont est une des plus belles choses jamais enregistrées sur un disque de rap.'),

    ('barsonly', 'Demain c\'est loin IAM',
     'Je ne parle pas français couramment et j\'écoute ce morceau depuis des années. Le flow transcende la langue.'),

    ('nightshift', 'Archangel Burial',
     'Je le remets tous les hivers. Il n\'a pas bougé d\'un millimètre en quinze ans.'),

    ('vinylcurse', 'The Payback James Brown',
     'Si vous voulez comprendre le rap, commencez par comprendre ce groove.'),

    ('sunsetdrive', 'Alright Kendrick Lamar',
     'Entendre une foule chanter ce refrain en vrai, c\'est autre chose que de l\'écouter au casque.'),

    ('beatlover', 'Mask Off Future',
     'Metro a laissé de la place partout. C\'est le vide dans ce beat qui le rend énorme.'),

    ('barsonly', 'Liquid Swords GZA',
     'Le meilleur album Wu en solo, et ce n\'est pas un débat que j\'accepte de perdre.'),
]

# ============================================================
# FOLLOWS
# ============================================================

FOLLOWS = [
    ('alexwaves', 'roadrap'), ('alexwaves', 'juliemoon'), ('alexwaves', 'samecho'),
    ('alexwaves', 'barsonly'), ('alexwaves', 'beatlover'),
    ('juliemoon', 'crateking'), ('juliemoon', 'barsonly'), ('juliemoon', 'vinylcurse'),
    ('juliemoon', 'alexwaves'),
    ('samecho', 'lowendtheory'), ('samecho', 'alexwaves'), ('samecho', 'roadrap'),
    ('samecho', 'sunsetdrive'),
    ('beatlover', 'crateking'), ('beatlover', 'vinylcurse'), ('beatlover', 'lowendtheory'),
    ('melodymind', 'nightshift'), ('melodymind', 'vinylcurse'), ('melodymind', 'lostinmusic'),
    ('lostinmusic', 'melodymind'), ('lostinmusic', 'nightshift'), ('lostinmusic', 'alexwaves'),
    ('crateking', 'vinylcurse'), ('crateking', 'juliemoon'), ('crateking', 'beatlover'),
    ('barsonly', 'juliemoon'), ('barsonly', 'parisdigger'), ('barsonly', 'crateking'),
    ('lowendtheory', 'beatlover'), ('lowendtheory', 'samecho'), ('lowendtheory', 'nightshift'),
    ('parisdigger', 'alexwaves'), ('parisdigger', 'barsonly'), ('parisdigger', 'roadrap'),
    ('nightshift', 'melodymind'), ('nightshift', 'lostinmusic'), ('nightshift', 'lowendtheory'),
    ('vinylcurse', 'crateking'), ('vinylcurse', 'juliemoon'), ('vinylcurse', 'melodymind'),
    ('roadrap', 'alexwaves'), ('roadrap', 'samecho'), ('roadrap', 'parisdigger'),
    ('sunsetdrive', 'samecho'), ('sunsetdrive', 'lowendtheory'), ('sunsetdrive', 'juliemoon'),
]

# ============================================================
# COMMENTAIRES : (username, index du dig, contenu)
# ============================================================

COMMENTS = [
    ('samecho',     0,  'The "sleep is the cousin of death" line still gives me chills.'),
    ('beatlover',   0,  'Premier only used four elements on this beat. Four.'),
    ('crateking',   0,  'People forget he was 20 when he wrote this.'),
    ('juliemoon',   3,  'Best rags to riches song ever written, no contest.'),
    ('barsonly',    3,  'The specificity is what does it. Sardines for dinner, not "we were poor".'),
    ('alexwaves',   7,  'Prodigy at 19. Nineteen.'),
    ('lowendtheory',7,  'That bassline sits so low in the mix it feels like a room tone.'),
    ('sunsetdrive', 20, 'The switch is the best thing on the album and it is not close.'),
    ('barsonly',    20, 'Two beats, two characters. Structurally it is a short film.'),
    ('roadrap',     44, 'He makes the flow switches sound accidental. They are not.'),
    ('alexwaves',   46, 'Cench understood streaming better than the labels did.'),
    ('parisdigger', 65, 'Booba a vingt ans d\'avance sur tout le monde, encore aujourd\'hui.'),
    ('barsonly',    72, 'PNL created a whole world. The music is only part of it.'),
    ('melodymind',  90, 'The beat switch is the moment I understood what Blonde was doing.'),
    ('nightshift',  90, 'First half is daylight, second half is 3am. Exactly.'),
    ('crateking',   90, 'Down to the second, right in the middle of the album.'),
    ('vinylcurse', 104, 'One take, almost. That is the part people miss.'),
    ('lostinmusic',112, 'Toni Braxton clearing that sample was the best decision of her decade.'),
    ('beatlover',  126, 'One groove, seven minutes, and every rap producer since owes it money.'),
    ('nightshift', 133, 'I put this on every winter without fail.'),
]

# ============================================================
# CONVERSATIONS : (expéditeur, destinataire, message, index du dig ou None)
# ============================================================

MESSAGES = [
    ('alexwaves', 'roadrap',    'You need to hear this', 44),
    ('roadrap',   'alexwaves',  'Already know it, been in rotation since it dropped', None),
    ('alexwaves', 'roadrap',    'The second flow switch is the one', None),
    ('roadrap',   'alexwaves',  'Fair. Have you heard the K-Trap one I posted?', None),

    ('juliemoon', 'crateking',  'This is your kind of thing', 8),
    ('crateking', 'juliemoon',  'That sax loop is four seconds of perfection', None),

    ('melodymind','nightshift', 'For your 3am playlist', 92),
    ('nightshift','melodymind', 'The detuned guitar is doing all the work here', None),

    ('parisdigger','barsonly',  'Tu comprends pas les paroles mais écoute le flow', 82),
    ('barsonly',  'parisdigger','I have no idea what he is saying and it still hits', None),

    ('samecho',   'lowendtheory', 'The drums on this', 36),
    ('lowendtheory','samecho',  'Filthy. Who produced it?', None),

    ('vinylcurse','beatlover',  'The source. Start here', 126),
    ('beatlover', 'vinylcurse', 'Been sampling this for years without knowing the original', None),
]


def seed():
    with app.app_context():

        # ---------- 1. Les genres canoniques ----------
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
        print(f'Seeding {len(DIGS)} digs (this calls Spotify, be patient)...')
        digs = []
        created = skipped = failed = 0

        for index, (username, query, content) in enumerate(DIGS):
            try:
                results = DigService.search_tracks(query, limit=1)
                if not results:
                    print(f'  ! not found: {query}')
                    digs.append(None)
                    failed += 1
                    continue

                payload = results[0]

                # Le script est ré-exécutable : on saute si cette personne
                # a déjà digé ce morceau.
                field = 'spotify_id' if payload['source'] == 'spotify' else 'youtube_id'
                existing_track = Track.query.filter_by(
                    **{field: payload['external_id']}).first()

                if existing_track:
                    already = Dig.query.filter_by(
                        user_id=users[username].id,
                        track_id=existing_track.id).first()
                    if already:
                        digs.append(already)
                        skipped += 1
                        continue

                dig = DigService.create_dig(
                    user_id=users[username].id,
                    content=content,
                    source=payload['source'],
                    external_id=payload['external_id'],
                )
                digs.append(dig)
                created += 1

                if created % 20 == 0:
                    print(f'  ... {created} digs created')

            except Exception as exc:
                print(f'  ! failed on "{query}": {exc}')
                digs.append(None)
                failed += 1

        print(f'  created {created} | skipped {skipped} | failed {failed}')

        # ---------- 4. Les follows ----------
        print('Seeding follows...')
        for follower, followed in FOLLOWS:
            if follower in users and followed in users:
                exists = Follow.query.filter_by(
                    follower_id=users[follower].id,
                    followed_id=users[followed].id).first()
                if not exists:
                    try:
                        Follow.toggle(users[follower].id, users[followed].id)
                    except Exception:
                        pass
        print(f'  {Follow.query.count()} follows')

        # ---------- 5. Upvotes ----------
        # Générés aléatoirement mais de façon pondérée : certains digs
        # reçoivent beaucoup de votes, d'autres peu. Ça donne un Trending
        # avec un vrai classement plutôt qu'une égalité générale.
        print('Seeding upvotes...')
        usernames = list(users.keys())
        added = 0

        for dig in digs:
            if dig is None:
                continue

            # Entre 0 et 9 votants, avec une distribution qui favorise
            # quelques morceaux (sinon tout le monde est à égalité)
            voters = random.sample(usernames, k=random.choice([0, 1, 2, 2, 3, 3, 4, 5, 7, 9]))
            for username in voters:
                if users[username].id == dig.user_id:
                    continue
                exists = Upvote.query.filter_by(
                    user_id=users[username].id, dig_id=dig.id).first()
                if not exists:
                    Upvote.toggle(users[username].id, dig)
                    added += 1

        print(f'  {Upvote.query.count()} upvotes (+{added})')

        # ---------- 6. Redigs ----------
        print('Seeding redigs...')
        added = 0
        for dig in digs:
            if dig is None:
                continue
            # Un redig est plus rare qu'un upvote : c'est un engagement
            # plus fort, et il pèse deux fois plus dans le score.
            for username in random.sample(usernames, k=random.choice([0, 0, 0, 1, 1, 2, 3])):
                if users[username].id == dig.user_id:
                    continue
                exists = Redig.query.filter_by(
                    user_id=users[username].id, dig_id=dig.id).first()
                if not exists:
                    Redig.toggle(users[username].id, dig)
                    added += 1

        print(f'  {Redig.query.count()} redigs (+{added})')

        # ---------- 7. Commentaires ----------
        print('Seeding comments...')
        for username, index, content in COMMENTS:
            if index >= len(digs) or digs[index] is None:
                continue
            dig = digs[index]
            exists = Comment.query.filter_by(
                user_id=users[username].id, dig_id=dig.id, content=content).first()
            if exists:
                continue
            db.session.add(Comment(content=content,
                                   user_id=users[username].id,
                                   dig_id=dig.id))
            dig.comments_count += 1
        db.session.commit()
        print(f'  {Comment.query.count()} comments')

        # ---------- 8. Conversations ----------
        print('Seeding conversations...')
        for sender, recipient, content, dig_index in MESSAGES:
            if sender not in users or recipient not in users:
                continue
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
        print(f'Tracks:        {Track.query.count()}')
        print(f'Upvotes:       {Upvote.query.count()}')
        print(f'Redigs:        {Redig.query.count()}')
        print(f'Comments:      {Comment.query.count()}')
        print(f'Follows:       {Follow.query.count()}')
        print(f'Conversations: {Conversation.query.count()}')
        print(f'\nLogin with any username above, password: {PASSWORD}')

        print('\n--- Trending top 10 ---')
        for dig in DigService.trending(limit=10):
            print(f'  {dig.score():>3} pts  {dig.display_title} — {dig.display_artist}')


if __name__ == '__main__':
    seed()
