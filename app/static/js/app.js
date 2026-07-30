/* Comportements présents sur toutes les pages. */

document.addEventListener('DOMContentLoaded', () => {
  renderAuthZone();
  wireGlobalSearch();
});


/*
 * Bascule entre "Login / Sign up" et le menu utilisateur.
 *
 * Note : les pages sont rendues par Jinja2 côté serveur, qui ne connaît PAS
 * le token (il est dans localStorage, côté navigateur). C'est donc le JS qui
 * ajuste la navbar après le chargement.
 */
function renderAuthZone() {
  const buttons     = document.getElementById('authButtons');
  const menu        = document.getElementById('userMenu');
  const avatarBtn   = document.getElementById('avatarBtn');
  const dropdown    = document.getElementById('avatarDropdown');
  const initial     = document.getElementById('avatarInitial');
  const logoutBtn   = document.getElementById('logoutBtn');
  const profileLink = document.getElementById('myProfileLink');

  if (Auth.isLoggedIn) {
    // On retire flex ET sm:flex : une variante responsive de Tailwind
    // l'emporte sur hidden, donc l'ajouter seul ne suffit pas.
    buttons?.classList.remove('flex', 'sm:flex');
    buttons?.classList.add('hidden');
    menu?.classList.remove('hidden');

    if (initial && Auth.user) {
      initial.textContent = Auth.user.username.charAt(0).toUpperCase();
    }
    if (profileLink && Auth.user) {
      profileLink.href = `/u/${encodeURIComponent(Auth.user.username)}`;
    }

    // Menu déroulant : stopPropagation évite que le clic remonte au document
    // et referme immédiatement ce qu'on vient d'ouvrir.
    avatarBtn?.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown?.classList.toggle('hidden');
    });
    document.addEventListener('click', () => dropdown?.classList.add('hidden'));

    logoutBtn?.addEventListener('click', () => {
      // Déconnexion = effacer le token local. Le JWT reste techniquement
      // valide jusqu'à son expiration (on ne peut pas le révoquer), d'où
      // sa durée de vie courte d'une heure.
      Auth.clear();
      window.location.href = '/trending';
    });

  } else {
    buttons?.classList.remove('hidden');
    buttons?.classList.add('flex');
    menu?.classList.add('hidden');
  }
}


/*
 * Suggestions de recherche en direct.
 *
 * Le debounce est essentiel : sans lui, chaque frappe déclenche une requête.
 * Taper "kendrick" ferait 8 appels au serveur au lieu d'un.
 */
function wireGlobalSearch() {
  const input = document.getElementById('globalSearch');
  const panel = document.getElementById('searchResults');
  if (!input || !panel) return;

  let timer = null;

  input.addEventListener('input', () => {
    clearTimeout(timer);
    const query = input.value.trim();

    if (query.length < 2) {
      panel.classList.add('hidden');
      return;
    }

    timer = setTimeout(async () => {
      try {
        const { suggestions } = await API.get(
          `/api/search/suggest?q=${encodeURIComponent(query)}`);

        if (!suggestions.length) {
          panel.classList.add('hidden');
          return;
        }

        panel.innerHTML = suggestions.map(s => `
          <a href="${suggestionUrl(s)}"
             class="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-edge">
            <span class="text-xs uppercase tracking-wide text-neutral-500">${s.type}</span>
            <span class="truncate">${escapeHtml(s.label)}</span>
          </a>
        `).join('');
        panel.classList.remove('hidden');
      } catch (err) {
        panel.classList.add('hidden');
      }
    }, 250);   // 250 ms après la dernière frappe
  });

  // Fermer la dropdown au clic extérieur
  document.addEventListener('click', (e) => {
    if (!panel.contains(e.target) && e.target !== input) {
      panel.classList.add('hidden');
    }
  });
}


function suggestionUrl(s) {
  if (s.type === 'user')  return `/u/${encodeURIComponent(s.label)}`;
  if (s.type === 'track') return `/digscover?songs=${encodeURIComponent(s.label)}`;
  return `/digscover?artists=${encodeURIComponent(s.label)}`;
}


/*
 * Échappement HTML : indispensable dès qu'on injecte du contenu utilisateur
 * dans innerHTML. Sans ça, un pseudo contenant du HTML pourrait exécuter du
 * script — c'est une faille XSS.
 */
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
