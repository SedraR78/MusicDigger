/*
 * Boutons Follow et Message du profil.
 *
 * Leur état dépend du VISITEUR, pas de la page. Jinja2 ne peut donc pas les
 * rendre : le token est dans localStorage, côté navigateur. C'est le JS qui
 * interroge l'API et ajuste l'affichage après le chargement.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const followBtn  = document.getElementById('followBtn');
  const messageBtn = document.getElementById('messageBtn');
  if (!followBtn) return;

  const username = followBtn.dataset.username;

  // Un visiteur non connecté ne voit aucun des deux boutons
  if (!Auth.isLoggedIn) return;

  // On ne se suit pas soi-même et on ne s'écrit pas à soi-même :
  // le serveur refuse les deux (400), autant ne rien afficher.
  if (Auth.user?.username === username) return;

  /* ---------- Follow ---------- */

  try {
    const { user } = await API.get(`/api/users/${encodeURIComponent(username)}`);
    renderFollow(user.is_following);
    followBtn.classList.remove('hidden');
  } catch (err) {
    return;
  }

  followBtn.addEventListener('click', async () => {
    followBtn.disabled = true;
    try {
      const data = await API.post(
        `/api/users/${encodeURIComponent(username)}/follow`);

      renderFollow(data.is_following);
      document.getElementById('followersCount').textContent = data.followers_count;
    } catch (err) {
      showToast(err.message);
    }
    followBtn.disabled = false;
  });

  function renderFollow(isFollowing) {
    followBtn.textContent = isFollowing ? 'Following' : 'Follow';
    followBtn.className = `rounded-full px-4 py-1.5 text-sm font-medium transition
      ${isFollowing
        ? 'border border-edge text-neutral-300 hover:border-red-800 hover:text-red-400'
        : 'bg-neutral-100 text-ink hover:bg-white'}`;
  }

  /* ---------- Message ---------- */

  messageBtn?.classList.remove('hidden');

  messageBtn?.addEventListener('click', async () => {
    messageBtn.disabled = true;
    try {
      // L'endpoint est idempotent : si la conversation existe déjà,
      // il la renvoie au lieu d'en créer une seconde.
      await API.post('/api/conversations', { username });
      window.location.href = '/messages';
    } catch (err) {
      showToast(err.message);
      messageBtn.disabled = false;
    }
  });
});
