/*
 * Page DigsCover.
 *
 * Rappel du choix produit : on recommande des TRACKS du catalogue, pas des
 * DIGs existants. Sinon on ne pourrait faire découvrir que des sons déjà
 * postés — et personne ne pourrait jamais être le premier à diguer un morceau.
 *
 * D'où le bouton "Dig about this track" sur chaque carte : la découverte
 * devient une source de contenu.
 */

const selectedGenres  = new Set();
const selectedArtists = new Set();   // noms d'artistes choisis
const selectedSongs   = new Set();   // titres de morceaux choisis

document.addEventListener('DOMContentLoaded', () => {
  wireGenreTags();
  wireCriteriaInputs();
  wireStartDigging();
  wireRandomDig();
  readUrlParams();
  loadRecommendations();
});


/* ---------- Les tags de genre ---------- */

function wireGenreTags() {
  document.querySelectorAll('[data-genre]').forEach(btn => {
    btn.addEventListener('click', () => {
      const genre = btn.dataset.genre;

      if (selectedGenres.has(genre)) {
        selectedGenres.delete(genre);
        btn.classList.remove('border-dig', 'text-dig');
        btn.classList.add('border-edge', 'text-neutral-400');
      } else {
        selectedGenres.add(genre);
        btn.classList.add('border-dig', 'text-dig');
        btn.classList.remove('border-edge', 'text-neutral-400');
      }
    });
  });

  document.getElementById('showAllGenres')?.addEventListener('click', () => {
    const panel = document.getElementById('allGenres');
    panel.classList.toggle('hidden');
    panel.classList.toggle('flex');
  });
}


/* ---------- Champs de critères avec suggestions ---------- */

/*
 * On suggère depuis NOTRE base (/api/search/suggest), pas depuis Spotify.
 *
 * Pourquoi : DigsCover recommande des morceaux du catalogue local. Proposer
 * un artiste absent de la base ne donnerait aucun résultat — autant ne
 * suggérer que ce qui existe réellement.
 *
 * Bénéfice secondaire : plus de fautes d'orthographe, l'utilisateur clique
 * au lieu de taper.
 */
function wireCriteriaInputs() {
  setupSuggestField({
    inputId:     'criteriaArtists',
    panelId:     'artistSuggestions',
    chipsId:     'artistChips',
    wantedType:  'artist',
    selectedSet: selectedArtists,
  });

  setupSuggestField({
    inputId:     'criteriaSongs',
    panelId:     'songSuggestions',
    chipsId:     'songChips',
    wantedType:  'track',
    selectedSet: selectedSongs,
  });
}


function setupSuggestField({ inputId, panelId, chipsId, wantedType, selectedSet }) {
  const input = document.getElementById(inputId);
  const panel = document.getElementById(panelId);
  const chips = document.getElementById(chipsId);
  if (!input || !panel || !chips) return;

  let timer = null;

  input.addEventListener('input', () => {
    clearTimeout(timer);
    const query = input.value.trim();

    if (query.length < 2) {
      panel.classList.add('hidden');
      return;
    }

    // Debounce : sans lui, chaque frappe déclencherait une requête
    timer = setTimeout(async () => {
      try {
        const { suggestions } = await API.get(
          `/api/search/suggest?q=${encodeURIComponent(query)}`);

        // On ne garde que le type qui concerne ce champ
        const filtered = suggestions.filter(s => s.type === wantedType);

        if (!filtered.length) {
          panel.innerHTML = `
            <p class="px-3 py-2 text-xs text-neutral-500">
              Nothing in the catalog yet.
            </p>`;
          panel.classList.remove('hidden');
          return;
        }

        panel.innerHTML = filtered.map(s => `
          <button data-value="${escapeHtml(cleanLabel(s.label, wantedType))}"
                  class="block w-full px-3 py-2 text-left text-sm hover:bg-edge">
            ${escapeHtml(s.label)}
          </button>
        `).join('');
        panel.classList.remove('hidden');

        panel.querySelectorAll('button').forEach(btn => {
          btn.addEventListener('click', () => {
            selectedSet.add(btn.dataset.value);
            renderChips(chips, selectedSet);
            input.value = '';
            panel.classList.add('hidden');
          });
        });

      } catch (err) {
        panel.classList.add('hidden');
      }
    }, 250);
  });

  // Entrée : on accepte aussi la saisie libre, au cas où
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && input.value.trim()) {
      e.preventDefault();
      selectedSet.add(input.value.trim());
      renderChips(chips, selectedSet);
      input.value = '';
      panel.classList.add('hidden');
    }
  });

  document.addEventListener('click', (e) => {
    if (!panel.contains(e.target) && e.target !== input) {
      panel.classList.add('hidden');
    }
  });
}


/*
 * L'API renvoie les morceaux sous la forme "Titre — Artiste".
 * On ne garde que le titre pour le critère.
 */
function cleanLabel(label, type) {
  if (type === 'track' && label.includes(' — ')) {
    return label.split(' — ')[0];
  }
  return label;
}


function renderChips(container, selectedSet) {
  if (!selectedSet.size) {
    container.classList.add('hidden');
    container.classList.remove('flex');
    return;
  }

  container.classList.remove('hidden');
  container.classList.add('flex');

  container.innerHTML = [...selectedSet].map(value => `
    <span class="flex items-center gap-1 rounded-full border border-dig
                 px-2.5 py-1 text-xs text-dig">
      ${escapeHtml(value)}
      <button data-remove="${escapeHtml(value)}"
              class="hover:text-white">✕</button>
    </span>
  `).join('');

  container.querySelectorAll('[data-remove]').forEach(btn => {
    btn.addEventListener('click', () => {
      selectedSet.delete(btn.dataset.remove);
      renderChips(container, selectedSet);
    });
  });
}


/* ---------- Lecture des paramètres d'URL ---------- */

/*
 * Permet d'arriver ici depuis un lien : /digscover?artists=Nas
 * C'est ce que font les suggestions de la recherche globale.
 */
function readUrlParams() {
  const params = new URLSearchParams(window.location.search);

  const artists = params.get('artists');
  const songs   = params.get('songs');
  const genres  = params.get('genres');

  if (artists) {
    artists.split(',').forEach(a => selectedArtists.add(a.trim()));
    renderChips(document.getElementById('artistChips'), selectedArtists);
  }

  if (songs) {
    songs.split(',').forEach(s => selectedSongs.add(s.trim()));
    renderChips(document.getElementById('songChips'), selectedSongs);
  }

  if (genres) {
    genres.split(',').forEach(g => {
      document.querySelector(`[data-genre="${g.trim()}"]`)?.click();
    });
  }
}


/* ---------- Chargement ---------- */

function wireStartDigging() {
  document.getElementById('startDigging')?.addEventListener('click', () => {
    loadRecommendations();
  });
}


async function loadRecommendations() {
  const grid = document.getElementById('trackGrid');
  grid.innerHTML = `<p class="text-sm text-neutral-500">Digging…</p>`;

  // Les critères viennent des chips, plus des champs texte
  const artists = [...selectedArtists].join(',');
  const songs   = [...selectedSongs].join(',');
  const genres  = [...selectedGenres].join(',');

  const params = new URLSearchParams();
  if (artists) params.set('artists', artists);
  if (songs)   params.set('songs', songs);
  if (genres)  params.set('genres', genres);

  try {
    const data = await API.get(`/api/digscover?${params.toString()}`);
    renderResults(data);
  } catch (err) {
    grid.innerHTML = `<p class="text-sm text-red-400">${err.message}</p>`;
  }
}


function renderResults(data) {
  const grid     = document.getElementById('trackGrid');
  const title    = document.getElementById('resultsTitle');
  const hint     = document.getElementById('resultsHint');
  const banner   = document.getElementById('signupBanner');
  const subtitle = document.getElementById('digscoverSubtitle');

  // Le champ `mode` indique COMMENT afficher : sans lui, une liste vide
  // serait ambiguë (rien trouvé, ou rien demandé ?).
  if (data.mode === 'empty') {
    title.textContent = '';
    hint.textContent = '';
    grid.innerHTML = `
      <div class="col-span-full rounded-2xl border border-edge bg-panel p-10 text-center">
        <p class="text-3xl">⛏</p>
        <p class="mt-3 font-medium">${data.prompt || 'Tell us what you like'}</p>
        <p class="mt-1 text-sm text-neutral-400">
          Pick some artists, songs or genres above to start digging.
        </p>
      </div>`;
    banner.classList.remove('hidden');
    banner.classList.add('flex');
    return;
  }

  if (data.mode === 'personalized') {
    title.textContent = 'Recommended for you';
    hint.textContent = 'Based on your activity and the community';
    subtitle.textContent = 'Tracks picked from what you dig — and from what people like you dig.';
    banner.classList.add('hidden');
  } else {
    title.textContent = 'Tracks for you';
    hint.textContent = 'Based on the criteria you chose';
    if (!Auth.isLoggedIn) {
      banner.classList.remove('hidden');
      banner.classList.add('flex');
    }
  }

  if (!data.tracks.length) {
    grid.innerHTML = `
      <div class="col-span-full rounded-2xl border border-edge bg-panel p-8 text-center">
        <p class="text-sm text-neutral-400">
          Nothing matched. Try different criteria.
        </p>
      </div>`;
    return;
  }

  grid.innerHTML = data.tracks.map(track => trackCard(track)).join('');
  wireTrackActions();
}


/*
 * Carte de TRACK — volontairement différente d'une carte DIG :
 * pas de compteurs sociaux, pas d'avis. C'est un morceau du catalogue,
 * pas un post. Le bouton principal invite à le diguer.
 */
function trackCard(track) {
  return `
    <article class="rounded-2xl border border-edge bg-panel p-3">

      <span class="mb-2.5 inline-block rounded-full border border-edge px-2 py-0.5
                   text-xs text-neutral-400">
        ${escapeHtml(track.reason_label || 'Fresh pick')}
      </span>

      <div class="flex gap-3">
        ${track.cover_url
          ? `<img src="${track.cover_url}" alt=""
                  class="h-16 w-16 shrink-0 rounded-lg object-cover">`
          : `<div class="flex h-16 w-16 shrink-0 items-center justify-center
                        rounded-lg border border-edge bg-ink text-neutral-600">♪</div>`}

        <div class="min-w-0 flex-1">
          <p class="truncate font-semibold leading-tight">${escapeHtml(track.title)}</p>
          <p class="truncate text-sm text-neutral-400">${escapeHtml(track.artist || '')}</p>
          ${track.album ? `<p class="truncate text-xs text-neutral-500">${escapeHtml(track.album)}</p>` : ''}
          ${track.genre ? `<span class="mt-1 inline-block rounded-full border border-edge
                                        px-2 py-0.5 text-xs text-neutral-500">${escapeHtml(track.genre)}</span>` : ''}
        </div>
      </div>

      ${track.embed_url
        ? `<iframe src="${track.embed_url}" loading="lazy"
                   class="mt-3 h-20 w-full rounded-lg border-0"
                   allow="encrypted-media"></iframe>`
        : ''}

      <div class="mt-3 flex gap-2">
        <button data-dig-track="${track.id}"
                data-title="${escapeHtml(track.title)}"
                class="flex-1 rounded-lg bg-dig px-3 py-2 text-xs font-semibold
                       text-white transition hover:brightness-110">
          ⛏ Dig about this track
        </button>
        <button data-share-track="${escapeHtml(track.title)}"
                class="rounded-lg border border-edge px-3 py-2 text-xs
                       text-neutral-400 hover:bg-edge hover:text-white">
          🔗
        </button>
      </div>
    </article>`;
}


function wireTrackActions() {
  document.querySelectorAll('[data-dig-track]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!Auth.isLoggedIn) {
        window.location.href = '/login';
        return;
      }
      // On ouvre le modal de création avec le titre pré-rempli :
      // l'utilisateur n'a plus qu'à choisir le bon résultat et écrire son avis.
      const modal  = document.getElementById('createDigModal');
      const search = document.getElementById('trackSearch');
      modal.classList.remove('hidden');
      modal.classList.add('flex');
      search.value = btn.dataset.title;
      search.dispatchEvent(new Event('input'));   // déclenche la recherche
    });
  });

  document.querySelectorAll('[data-share-track]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const url = `${window.location.origin}/digscover?songs=${encodeURIComponent(btn.dataset.shareTrack)}`;
      await navigator.clipboard.writeText(url);
      showToast('Link copied', 'info');
    });
  });
}


/* ---------- Random DIG ---------- */

function wireRandomDig() {
  document.getElementById('randomDig')?.addEventListener('click', async () => {
    try {
      const { dig } = await API.get('/api/digscover/random');
      window.location.href = `/digs/${dig.id}`;
    } catch (err) {
      showToast(err.message);
    }
  });
}
