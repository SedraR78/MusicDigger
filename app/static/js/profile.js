/*
 * Boutons du profil : Follow, Message, et l'édition sur son propre profil.
 *
 * Leur état dépend du VISITEUR, pas de la page. Jinja2 ne peut donc pas les
 * rendre : le token est dans localStorage, côté navigateur. C'est le JS qui
 * interroge l'API et ajuste l'affichage après le chargement.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const followBtn  = document.getElementById('followBtn');
  const messageBtn = document.getElementById('messageBtn');
  const editBtn    = document.getElementById('editBtn');
  const editModal  = document.getElementById('editModal');

  if (!followBtn) return;

  const username = followBtn.dataset.username;

  // Un visiteur non connecté ne voit aucun bouton
  if (!Auth.isLoggedIn) return;

  const isMyProfile = Auth.user?.username === username;

  /* ==================== SON PROPRE PROFIL ==================== */

  if (isMyProfile) {
    wireEdit();
    return;   // pas de Follow ni de Message sur soi-même
  }

  /* ==================== PROFIL DE QUELQU'UN D'AUTRE ==================== */

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


  /* ==================== ÉDITION DU PROFIL ==================== */

  function wireEdit() {
    if (!editBtn || !editModal) return;

    editBtn.classList.remove('hidden');

    editBtn.addEventListener('click', () => {
      editModal.classList.remove('hidden');
      editModal.classList.add('flex');
    });

    const close = () => {
      editModal.classList.add('hidden');
      editModal.classList.remove('flex');
    };

    document.getElementById('closeEdit')?.addEventListener('click', close);
    editModal.addEventListener('click', (e) => {
      if (e.target === editModal) close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !editModal.classList.contains('hidden')) close();
    });

    /* ---------- Sauvegarde ---------- */

    document.getElementById('saveProfile')?.addEventListener('click', async () => {
      const newUsername = document.getElementById('editUsername').value.trim();
      const bio = document.getElementById('editBio').value.trim();

      if (newUsername.length < 3) {
        showToast('Username must be at least 3 characters');
        return;
      }

      try {
        const { user } = await API.put('/api/auth/me', {
          username: newUsername,
          bio: bio,
        });

        // Le pseudo est stocké localement pour la navbar : il faut le mettre
        // à jour, sinon l'avatar garde l'ancienne initiale.
        Auth.save(Auth.token, localStorage.getItem('md_refresh'), user);

        showToast('Profile updated', 'info');
        window.location.href = `/u/${encodeURIComponent(user.username)}`;
      } catch (err) {
        // 409 si le pseudo est déjà pris
        showToast(err.message);
      }
    });

    /* ---------- Suppression de compte ---------- */

    document.getElementById('deleteAccount')?.addEventListener('click', async () => {
      // Le serveur exige le mot de passe : un token volé ne doit pas
      // suffire à détruire un compte. C'est de la ré-authentification
      // pour action sensible.
      const password = prompt(
        'This is permanent. Your posts stay under "RetiredDigger" but your ' +
        'personal data is erased.\n\nEnter your password to confirm:');

      if (!password) return;

      try {
        await API.delete('/api/auth/account', { password });
        Auth.clear();
        window.location.href = '/trending';
      } catch (err) {
        // 403 si le mot de passe est faux
        showToast(err.message);
      }
    });
  }
});
