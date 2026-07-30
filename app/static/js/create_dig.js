/*
 * Logique du modal de création.
 *
 * Point clé de sécurité : on n'envoie au serveur que la SOURCE et
 * l'IDENTIFIANT EXTERNE du morceau — jamais le titre, l'artiste ou la
 * pochette. Le serveur va les rechercher lui-même auprès de l'API.
 * Un utilisateur ne peut donc pas falsifier les infos d'un son.
 */

let selectedTrack = null;

document.addEventListener('DOMContentLoaded', () => {
  const modal         = document.getElementById('createDigModal');
  const openBtn       = document.getElementById('openCreateDig');
  const openBtnMobile = document.getElementById('openCreateDigMobile');
  const closeBtn      = document.getElementById('closeCreateDig');
  const search        = document.getElementById('trackSearch');
  const results       = document.getElementById('trackResults');
  const preview       = document.getElementById('trackPreview');
  const clearBtn      = document.getElementById('clearTrack');
  const content       = document.getElementById('digContent');
  const submitBtn     = document.getElementById('submitDig');
  const charCount     = document.getElementById('charCount');
  const genreStep     = document.getElementById('genreStep');

  if (!modal) return;   // le modal n'est pas sur cette page

  /* ---------- Ouvrir / fermer ---------- */

  function open(e) {
    // Un visiteur ne peut pas poster : on l'envoie sur la page de connexion
    if (!Auth.isLoggedIn) {
      window.location.href = '/login';
      return;
    }
    e.preventDefault();
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    search.focus();
  }

  openBtn?.addEventListener('click', open);
  openBtnMobile?.addEventListener('click', open);

  function close() {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    resetForm();
  }

  closeBtn?.addEventListener('click', close);

  // Fermer au clic sur le fond, mais pas sur le contenu du modal
  modal.addEventListener('click', (e) => {
    if (e.target === modal) close();
  });

  // Fermer avec Échap : réflexe attendu par les utilisateurs
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) close();
  });

  /* ---------- Recherche avec debounce ---------- */

  let timer = null;

  search?.addEventListener('input', () => {
    clearTimeout(timer);
    const query = search.value.trim();

    if (query.length < 2) {
      results.classList.add('hidden');
      return;
    }

    // 350 ms : sans ce délai, taper "kendrick" ferait 8 appels à Spotify
    timer = setTimeout(() => searchTracks(query), 350);
  });

  async function searchTracks(query) {
    results.innerHTML = `<p class="px-3 py-2 text-sm text-neutral-500">Searching...</p>`;
    results.classList.remove('hidden');

    try {
      const data = await API.get(`/api/digs/search?q=${encodeURIComponent(query)}`);

      if (!data.results.length) {
        results.innerHTML = `
          <p class="px-3 py-2 text-sm text-neutral-500">
            Nothing found on Spotify or YouTube.
          </p>`;
        return;
      }

      results.innerHTML = data.results.map((track, index) => `
        <button data-index="${index}"
                class="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left
                       hover:bg-edge">
          <img src="${track.cover_url || ''}" alt=""
               class="h-10 w-10 shrink-0 rounded bg-panel object-cover">
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-medium">${escapeHtml(track.title)}</span>
            <span class="block truncate text-xs text-neutral-400">${escapeHtml(track.artist_name || '')}</span>
          </span>
          <span class="shrink-0 rounded-full px-2 py-0.5 text-xs
                       ${track.source === 'spotify'
                         ? 'bg-green-950 text-green-400'
                         : 'bg-red-950 text-red-400'}">
            ${track.source}
          </span>
        </button>
      `).join('');

      // On garde les résultats en mémoire pour retrouver l'objet au clic
      results.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
          selectTrack(data.results[parseInt(btn.dataset.index, 10)]);
        });
      });

    } catch (err) {
      results.innerHTML = `<p class="px-3 py-2 text-sm text-red-400">${err.message}</p>`;
    }
  }

  /* ---------- Sélection ---------- */

  function selectTrack(track) {
    selectedTrack = track;

    document.getElementById('previewCover').src = track.cover_url || '';
    document.getElementById('previewTitle').textContent = track.title;
    document.getElementById('previewArtist').textContent = track.artist_name || '';
    document.getElementById('previewAlbum').textContent = track.album_title || '';

    // Le badge rend le fallback VISIBLE : c'est ce qui permet de le
    // démontrer en direct devant quelqu'un.
    const badge = document.getElementById('previewSource');
    badge.textContent = track.source === 'spotify' ? 'Spotify' : 'YouTube fallback';
    badge.className = `mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium
      ${track.source === 'spotify'
        ? 'bg-green-950 text-green-400'
        : 'bg-red-950 text-red-400'}`;

    results.classList.add('hidden');
    search.value = '';
    preview.classList.remove('hidden');
    genreStep.classList.remove('hidden');
    content.focus();
    updateSubmitState();
  }

  clearBtn?.addEventListener('click', () => {
    selectedTrack = null;
    preview.classList.add('hidden');
    genreStep.classList.add('hidden');
    updateSubmitState();
  });

  /* ---------- Validation en direct ---------- */

  content?.addEventListener('input', () => {
    charCount.textContent = `${content.value.length}/1000`;
    updateSubmitState();
  });

  function updateSubmitState() {
    // Les deux conditions du serveur, reproduites côté client pour le confort.
    // Le serveur revalide de toute façon : on ne fait jamais confiance au client.
    submitBtn.disabled = !(selectedTrack && content.value.trim().length > 0);
  }

  /* ---------- Envoi ---------- */

  submitBtn?.addEventListener('click', async () => {
    if (!selectedTrack) return;

    submitBtn.disabled = true;
    document.getElementById('submitLabel').textContent = 'Posting...';

    try {
      await API.post('/api/digs', {
        source: selectedTrack.source,           // spotify | youtube
        external_id: selectedTrack.external_id, // l'id, RIEN de plus
        content: content.value.trim(),
        genre: document.getElementById('digGenre').value || null,
      });

      showToast('DIG posted', 'info');
      close();
      // Rechargement : le nouveau dig doit apparaître dans la liste
      setTimeout(() => window.location.reload(), 600);

    } catch (err) {
      showToast(err.message);
      submitBtn.disabled = false;
      document.getElementById('submitLabel').textContent = 'Post your DIG';
    }
  });

  function resetForm() {
    selectedTrack = null;
    search.value = '';
    content.value = '';
    charCount.textContent = '0/1000';
    results.classList.add('hidden');
    preview.classList.add('hidden');
    genreStep.classList.add('hidden');
    document.getElementById('digGenre').value = '';
    submitBtn.disabled = true;
    document.getElementById('submitLabel').textContent = 'Post your DIG';
  }
});
