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
 * Partage : l'URL publique du DIG est simplement /digs/<id>.
 * Aucune table ni endpoint dédié — l'identifiant EST le lien.
 */
async function shareDig(digId) {
  const url = `${window.location.origin}/digs/${digId}`;

  // API navigateur : partage natif sur mobile, presse-papier sinon
  if (navigator.share) {
    try {
      await navigator.share({ title: 'MusicDigger', url });
      return;
    } catch (err) { /* l'utilisateur a annulé */ }
  }

  await navigator.clipboard.writeText(url);
  showToast('Link copied', 'info');
}
