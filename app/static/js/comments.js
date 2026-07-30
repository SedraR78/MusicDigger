/*
 * Commentaires d'un DIG.
 *
 * Choix technique : la liste est chargée en fetch après l'affichage de la page,
 * pas rendue par Jinja2. Pourquoi ? Parce qu'elle doit se rafraîchir après
 * l'ajout d'un commentaire sans recharger la page. Le rendu initial du DIG,
 * lui, reste côté serveur — c'est le principe hybride du Stage 3.
 */

document.addEventListener('DOMContentLoaded', () => {
  const list      = document.getElementById('commentList');
  const form      = document.getElementById('commentForm');
  const prompt    = document.getElementById('commentLoginPrompt');
  const input     = document.getElementById('commentInput');
  const postBtn   = document.getElementById('postComment');

  if (!list) return;

  const digId = postBtn?.dataset.dig || window.location.pathname.split('/').pop();

  // On affiche le formulaire ou l'invitation, selon l'état de connexion
  if (Auth.isLoggedIn) {
    form?.classList.remove('hidden');
  } else {
    prompt?.classList.remove('hidden');
  }

  loadComments();

  /* ---------- Chargement ---------- */

  async function loadComments() {
    try {
      const { comments } = await API.get(`/api/digs/${digId}/comments`);
      renderComments(comments);
    } catch (err) {
      list.innerHTML = `<p class="text-sm text-red-400">${err.message}</p>`;
    }
  }

  function renderComments(comments) {
    if (!comments.length) {
      list.innerHTML = `
        <p class="text-sm text-neutral-500">No comments yet. Be the first.</p>`;
      return;
    }

    const myId = Auth.user?.id;

    list.innerHTML = comments.map(c => `
      <article class="rounded-xl border border-edge bg-panel p-3.5">
        <header class="mb-1.5 flex items-center gap-2">
          <a href="/u/${encodeURIComponent(c.user.username)}"
             class="flex h-7 w-7 items-center justify-center rounded-full
                    border border-edge bg-ink text-xs font-medium">
            ${escapeHtml(c.user.username[0].toUpperCase())}
          </a>
          <a href="/u/${encodeURIComponent(c.user.username)}"
             class="text-sm font-medium hover:underline">${escapeHtml(c.user.username)}</a>
          <span class="text-xs text-neutral-500">${formatDate(c.created_at)}</span>

          ${c.user.id === myId ? `
            <button data-delete-comment="${c.id}"
                    class="ml-auto rounded px-1.5 text-xs text-neutral-500 hover:text-red-400">
              Delete
            </button>` : ''}
        </header>
        <p class="text-sm leading-relaxed text-neutral-200">${escapeHtml(c.content)}</p>
      </article>
    `).join('');

    // On ne montre le bouton Delete que sur ses propres commentaires.
    // Le serveur revérifie de toute façon (403 si ce n'est pas le tien) :
    // cacher un bouton n'est PAS une mesure de sécurité, juste du confort.
    list.querySelectorAll('[data-delete-comment]').forEach(btn => {
      btn.addEventListener('click', () => deleteComment(btn.dataset.deleteComment));
    });
  }

  /* ---------- Ajout ---------- */

  input?.addEventListener('input', () => {
    postBtn.disabled = input.value.trim().length === 0;
  });

  postBtn?.addEventListener('click', async () => {
    postBtn.disabled = true;

    try {
      const { comments_count } = await API.post(`/api/digs/${digId}/comments`, {
        content: input.value.trim(),
      });

      input.value = '';
      document.getElementById('commentTotal').textContent = comments_count;
      await loadComments();          // on recharge la liste
      showToast('Comment added', 'info');
    } catch (err) {
      showToast(err.message);
      postBtn.disabled = false;
    }
  });

  /* ---------- Suppression ---------- */

  async function deleteComment(commentId) {
    try {
      const { comments_count } = await API.delete(`/api/digs/comments/${commentId}`);
      document.getElementById('commentTotal').textContent = comments_count;
      await loadComments();
    } catch (err) {
      showToast(err.message);
    }
  }

  /* ---------- Utilitaire ---------- */

  function formatDate(iso) {
    const date = new Date(iso);
    const diffMin = Math.floor((Date.now() - date) / 60000);

    if (diffMin < 1)    return 'just now';
    if (diffMin < 60)   return `${diffMin}m`;
    if (diffMin < 1440) return `${Math.floor(diffMin / 60)}h`;
    return date.toLocaleDateString();
  }
});
