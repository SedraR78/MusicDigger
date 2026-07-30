/*
 * Interactions sur les cartes DIG : upvote, redig, partage.
 *
 * Technique : DÉLÉGATION D'ÉVÉNEMENTS. On écoute un seul clic sur document
 * plutôt que d'attacher un écouteur à chaque bouton.
 *
 * Pourquoi c'est important : sur une page avec 20 digs, ça fait 60 boutons.
 * Un seul écouteur au lieu de 60, et ça fonctionne aussi pour les cartes
 * ajoutées après le chargement (infinite scroll, nouveau dig posté).
 */

document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-action]');
  if (!button) return;

  const action = button.dataset.action;
  const digId = button.dataset.dig;

  if (action === 'share') return shareDig(digId);

  // Les autres actions exigent d'être connecté
  if (!Auth.isLoggedIn) {
    showToast('Log in to interact with DIGs');
    return;
  }

  if (action === 'upvote') return toggleUpvote(button, digId);
  if (action === 'redig')  return toggleRedig(button, digId);
});


async function toggleUpvote(button, digId) {
  try {
    const { is_upvoted, upvotes_count } = await API.post(`/api/digs/${digId}/upvote`);

    button.querySelector('[data-count="upvotes"]').textContent = upvotes_count;
    button.classList.toggle('text-dig', is_upvoted);
    button.classList.toggle('text-neutral-400', !is_upvoted);
  } catch (err) {
    showToast(err.message);
  }
}


async function toggleRedig(button, digId) {
  try {
    const { is_rediged, redigs_count } = await API.post(`/api/digs/${digId}/redig`);

    button.querySelector('[data-count="redigs"]').textContent = redigs_count;
    button.classList.toggle('text-dig', is_rediged);
    button.classList.toggle('text-neutral-400', !is_rediged);
  } catch (err) {
    // Le serveur refuse de rediger son propre dig : on affiche son message
    showToast(err.message);
  }
}

/*
 * Partage : l'URL publique du DIG est /digs/<id>. Aucune table ni endpoint
 * dédié — l'identifiant EST le lien.
 *
 * Deux destinations possibles : l'extérieur (presse-papier) ou un autre
 * utilisateur de la plateforme (message privé avec la carte intégrée).
 */
function shareDig(digId) {
  if (!Auth.isLoggedIn) return copyLink(digId);
  openShareSheet(digId);
}


async function copyLink(digId) {
  const url = `${window.location.origin}/digs/${digId}`;

  if (navigator.share) {
    try {
      await navigator.share({ title: 'MusicDigger', url });
      return;
    } catch (err) { /* annulé par l'utilisateur */ }
  }

  await navigator.clipboard.writeText(url);
  showToast('Link copied', 'info');
}


/*
 * Feuille de partage. Construite à la volée plutôt qu'incluse dans chaque
 * page : elle n'existe que le temps de l'interaction.
 */
function openShareSheet(digId) {
  const sheet = document.createElement('div');
  sheet.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4';
  sheet.innerHTML = `
    <div class="w-full max-w-sm rounded-2xl border border-edge bg-panel p-4">
      <header class="mb-4 flex items-center justify-between">
        <h3 class="font-semibold">Share this DIG</h3>
        <button data-close class="rounded px-2 text-neutral-500 hover:text-white">✕</button>
      </header>

      <button data-copy
              class="mb-4 w-full rounded-xl border border-edge px-4 py-2.5 text-sm
                     text-neutral-300 hover:bg-edge hover:text-white">
        🔗 Copy link
      </button>

      <p class="mb-1.5 text-xs text-neutral-500">Or send it to someone</p>

      <textarea data-message rows="2"
                placeholder="Say something about it… (optional)"
                class="mb-3 w-full resize-none rounded-xl border border-edge bg-ink
                       px-3 py-2 text-sm placeholder-neutral-500 outline-none
                       focus:border-neutral-600"></textarea>

      <div class="relative">
        <input data-user-search type="text" autocomplete="off"
               placeholder="Search a user…"
               class="w-full rounded-xl border border-edge bg-ink px-3 py-2 text-sm
                      placeholder-neutral-500 outline-none focus:border-neutral-600">
        <div data-user-results
             class="absolute inset-x-0 top-full z-10 mt-1 hidden max-h-48
                    overflow-y-auto rounded-xl border border-edge bg-panel shadow-2xl"></div>
      </div>
    </div>`;

  document.body.appendChild(sheet);

  const close = () => sheet.remove();
  sheet.querySelector('[data-close]').addEventListener('click', close);
  sheet.addEventListener('click', (e) => { if (e.target === sheet) close(); });

  sheet.querySelector('[data-copy]').addEventListener('click', () => {
    copyLink(digId);
    close();
  });

  wireUserSearch(sheet, digId, close);
}

function wireUserSearch(sheet, digId, close) {
  const input   = sheet.querySelector('[data-user-search]');
  const results = sheet.querySelector('[data-user-results]');
  const message = sheet.querySelector('[data-message]');
  let timer = null;

  input.addEventListener('input', () => {
    clearTimeout(timer);
    const query = input.value.trim();

    if (query.length < 2) {
      results.classList.add('hidden');
      return;
    }

    timer = setTimeout(async () => {
      try {
        const { suggestions } = await API.get(
          `/api/search/suggest?q=${encodeURIComponent(query)}`);

        const users = suggestions.filter(
          s => s.type === 'user' && s.label !== Auth.user?.username);

        if (!users.length) {
          results.innerHTML = `
            <p class="px-3 py-2 text-xs text-neutral-500">No user found.</p>`;
          results.classList.remove('hidden');
          return;
        }

        results.innerHTML = users.map(u => `
          <button data-send-to="${escapeHtml(u.label)}"
                  class="block w-full px-3 py-2 text-left text-sm hover:bg-edge">
            ${escapeHtml(u.label)}
          </button>`).join('');
        results.classList.remove('hidden');

        results.querySelectorAll('[data-send-to]').forEach(btn => {
          btn.addEventListener('click',
            () => send(btn.dataset.sendTo, message.value.trim(), digId, close));
        });

      } catch (err) {
        results.classList.add('hidden');
      }
    }, 250);
  });
}


/*
 * Deux appels : on ouvre (ou retrouve) la conversation, puis on envoie le
 * message avec le dig_id. L'endpoint de conversation est idempotent, donc
 * appeler deux fois ne crée pas de doublon.
 */
async function send(username, text, digId, close) {
  try {
    const { conversation } = await API.post('/api/conversations', { username });

    await API.post('/api/messages', {
      conversation_id: conversation.id,
      content: text || 'Check this out',   // le serveur exige un contenu
      dig_id: digId,
    });

    close();
    showToast(`Sent to ${username}`, 'info');
  } catch (err) {
    showToast(err.message);
  }
}
