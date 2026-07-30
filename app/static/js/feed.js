/*
 * Feed des personnes suivies.
 *
 * Rendu côté client parce que le contenu dépend entièrement du token.
 * Une page rendue par Jinja2 aurait dû lire le token, or il n'est pas
 * envoyé au serveur sur une navigation classique.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const list = document.getElementById('feedList');
  if (!list) return;

  if (!Auth.isLoggedIn) {
    list.innerHTML = emptyState(
      'Log in to see your feed',
      'Follow curators and their digs will show up here.',
      '<a href="/login" class="mt-3 inline-block text-sm text-dig hover:underline">Log in</a>'
    );
    return;
  }

  try {
    const { digs } = await API.get('/api/digs/feed');

    if (!digs.length) {
      list.innerHTML = emptyState(
        'Your feed is empty',
        "You're not following anyone yet, or they haven't dug anything.",
        '<a href="/people" class="mt-3 inline-block text-sm text-dig hover:underline">Find people to follow</a>'
      );
      return;
    }

    list.innerHTML = digs.map(digCard).join('');
  } catch (err) {
    list.innerHTML = `<p class="text-sm text-red-400">${err.message}</p>`;
  }
});


function emptyState(title, subtitle, action = '') {
  return `
    <div class="rounded-2xl border border-edge bg-panel p-10 text-center">
      <p class="text-3xl">⛏</p>
      <p class="mt-3 font-medium">${title}</p>
      <p class="mt-1 text-sm text-neutral-400">${subtitle}</p>
      ${action}
    </div>`;
}


/*
 * Version JS de la carte DIG.
 *
 * Duplication assumée avec components/dig_card.html : Jinja2 rend côté
 * serveur, ce fichier rend côté client. Les deux doivent rester cohérents.
 * Une V2 utiliserait un système de templates partagé.
 */
function digCard(dig) {
  return `
    <article class="rounded-2xl border border-edge bg-panel p-4" data-dig-id="${dig.id}">

      <header class="mb-3 flex items-center gap-2.5">
        <a href="/u/${encodeURIComponent(dig.user.username)}"
           class="flex h-9 w-9 items-center justify-center rounded-full
                  border border-edge bg-ink text-sm font-medium">
          ${escapeHtml(dig.user.username[0].toUpperCase())}
        </a>
        <a href="/u/${encodeURIComponent(dig.user.username)}"
           class="text-sm font-semibold hover:underline">${escapeHtml(dig.user.username)}</a>
      </header>

      <div class="flex flex-col gap-4 sm:flex-row">
        ${dig.cover
          ? `<img src="${dig.cover}" alt="" class="h-28 w-28 shrink-0 rounded-lg object-cover">`
          : `<div class="flex h-28 w-28 shrink-0 items-center justify-center
                        rounded-lg border border-edge bg-ink text-2xl text-neutral-600">♪</div>`}

        <div class="min-w-0 flex-1">
          <h3 class="truncate font-bold leading-tight">${escapeHtml(dig.title || '')}</h3>
          <p class="truncate text-sm text-neutral-400">${escapeHtml(dig.artist || '')}</p>
          ${dig.genre ? `<span class="mt-1.5 inline-block rounded-full border border-edge
                                      px-2 py-0.5 text-xs text-neutral-400">${escapeHtml(dig.genre)}</span>` : ''}
          <p class="mt-3 text-sm leading-relaxed text-neutral-200">${escapeHtml(dig.content)}</p>
        </div>
      </div>

      ${dig.embed
        ? `<iframe src="${dig.embed}" loading="lazy"
                   class="mt-4 h-20 w-full rounded-lg border-0" allow="encrypted-media"></iframe>`
        : ''}

      <footer class="mt-3 flex items-center gap-1 border-t border-edge pt-3 text-sm">
        <button data-action="upvote" data-dig="${dig.id}"
                class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5
                       ${dig.is_upvoted ? 'text-dig' : 'text-neutral-400'}
                       transition hover:bg-edge hover:text-white">
          <span>⬆</span><span data-count="upvotes">${dig.upvotes_count}</span>
        </button>

        <button data-action="redig" data-dig="${dig.id}"
                class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5
                       ${dig.is_rediged ? 'text-dig' : 'text-neutral-400'}
                       transition hover:bg-edge hover:text-white">
          <span>⛏</span><span data-count="redigs">${dig.redigs_count}</span>
        </button>

        <a href="/digs/${dig.id}"
           class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5
                  text-neutral-400 transition hover:bg-edge hover:text-white">
          <span>💬</span><span>${dig.comments_count}</span>
        </a>

        <button data-action="share" data-dig="${dig.id}"
                class="ml-auto rounded-lg px-2.5 py-1.5 text-neutral-400
                       transition hover:bg-edge hover:text-white">🔗</button>
      </footer>
    </article>`;
}
