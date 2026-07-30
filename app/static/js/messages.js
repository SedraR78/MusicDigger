/*
 * Messagerie privée.
 *
 * Le rafraîchissement se fait par POLLING (une requête toutes les 4 secondes
 * avec un paramètre `since`), pas par WebSockets. C'est un choix documenté au
 * Stage 3 : suffisant pour un MVP, beaucoup plus simple à déployer et à
 * déboguer. Le client ne reçoit que les messages postérieurs à ce qu'il
 * affiche déjà, donc la charge reste faible.
 */

let currentConversation = null;
let lastMessageAt = null;
let pollTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  if (!document.getElementById('conversationList')) return;

  if (!Auth.isLoggedIn) {
    document.getElementById('conversationList').innerHTML = `
      <p class="px-3 py-2 text-sm text-neutral-500">
        <a href="/login" class="text-dig hover:underline">Log in</a> to see your messages.
      </p>`;
    return;
  }

  loadConversations();
  wireSend();
  wireNewConversation();
});


/* ---------- Liste des conversations ---------- */

async function loadConversations() {
  const list = document.getElementById('conversationList');

  try {
    const { conversations } = await API.get('/api/conversations');

    if (!conversations.length) {
      list.innerHTML = `
        <p class="px-3 py-2 text-sm text-neutral-500">No conversations yet.</p>`;
      return;
    }

    list.innerHTML = conversations.map(c => {
      const other = c.other_user;
      const last = c.last_message;
      return `
        <button data-conversation="${c.id}"
                data-username="${escapeHtml(other?.username || '')}"
                class="flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2
                       text-left hover:bg-edge">
          <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full
                       border border-edge bg-ink text-sm font-medium">
            ${escapeHtml((other?.username || '?')[0].toUpperCase())}
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-medium">
              ${escapeHtml(other?.username || 'Unknown')}
            </span>
            <span class="block truncate text-xs text-neutral-500">
              ${last ? escapeHtml(last.content) : 'No messages yet'}
            </span>
          </span>
        </button>`;
    }).join('');

    list.querySelectorAll('[data-conversation]').forEach(btn => {
      btn.addEventListener('click', () => {
        openConversation(btn.dataset.conversation, btn.dataset.username);
      });
    });

  } catch (err) {
    list.innerHTML = `<p class="px-3 py-2 text-sm text-red-400">${err.message}</p>`;
  }
}


/* ---------- Ouvrir une conversation ---------- */

async function openConversation(conversationId, username) {
  currentConversation = conversationId;
  lastMessageAt = null;

  const header = document.getElementById('chatHeader');
  const input  = document.getElementById('chatInput');

  header.classList.remove('hidden');
  header.classList.add('flex');
  input.classList.remove('hidden');
  input.classList.add('flex');

  document.getElementById('chatUsername').textContent = username;
  document.getElementById('chatAvatar').textContent = username[0].toUpperCase();

  document.getElementById('chatMessages').innerHTML =
    `<p class="text-sm text-neutral-500">Loading…</p>`;

  await loadMessages({ replace: true });
  startPolling();
}


async function loadMessages({ replace = false } = {}) {
  if (!currentConversation) return;

  // `since` évite de redemander tout l'historique à chaque tour de polling
  const params = lastMessageAt && !replace
    ? `?since=${encodeURIComponent(lastMessageAt)}`
    : '';

  try {
    const { messages } = await API.get(
      `/api/conversations/${currentConversation}/messages${params}`);

    const zone = document.getElementById('chatMessages');

    if (replace) {
      zone.innerHTML = messages.length
        ? messages.map(messageBubble).join('')
        : `<p class="mt-20 text-center text-sm text-neutral-500">
             No messages yet. Say something.
           </p>`;
    } else if (messages.length) {
      // On retire l'éventuel état vide avant d'ajouter
      if (zone.querySelector('.text-center')) zone.innerHTML = '';
      zone.insertAdjacentHTML('beforeend', messages.map(messageBubble).join(''));
    }

    if (messages.length) {
      lastMessageAt = messages[messages.length - 1].created_at;
      zone.scrollTop = zone.scrollHeight;
    }

  } catch (err) {
    // 403 si on n'est pas participant : on arrête le polling
    stopPolling();
    showToast(err.message);
  }
}


/*
 * Bulle de message. Les miennes à droite, celles de l'autre à gauche.
 * Un message peut porter un DIG partagé (le lien 0..1 de l'ER).
 */
function messageBubble(msg) {
  const isMine = msg.sender?.id === Auth.user?.id;

  return `
    <div class="flex ${isMine ? 'justify-end' : 'justify-start'}">
      <div class="max-w-[75%]">

        ${msg.shared_dig ? sharedDigCard(msg.shared_dig) : ''}

        <div class="rounded-2xl px-3.5 py-2 text-sm
                    ${isMine ? 'bg-dig text-white' : 'bg-ink text-neutral-100'}">
          ${escapeHtml(msg.content)}
        </div>
        <p class="mt-0.5 px-1 text-[11px] text-neutral-600
                  ${isMine ? 'text-right' : ''}">
          ${formatTime(msg.created_at)}
        </p>
      </div>
    </div>`;
}


/* La carte DIG intégrée dans une bulle — le partage de son en message */
function sharedDigCard(dig) {
  return `
    <a href="/digs/${dig.id}"
       class="mb-1.5 flex gap-2.5 rounded-xl border border-edge bg-ink p-2
              transition hover:border-neutral-600">
      ${dig.cover
        ? `<img src="${dig.cover}" alt="" class="h-12 w-12 shrink-0 rounded object-cover">`
        : `<div class="flex h-12 w-12 shrink-0 items-center justify-center
                      rounded border border-edge text-neutral-600">♪</div>`}
      <span class="min-w-0 flex-1">
        <span class="block truncate text-sm font-medium">${escapeHtml(dig.title || '')}</span>
        <span class="block truncate text-xs text-neutral-400">${escapeHtml(dig.artist || '')}</span>
      </span>
    </a>`;
}


/* ---------- Envoi ---------- */

function wireSend() {
  const input = document.getElementById('messageText');
  const btn   = document.getElementById('sendMessage');

  input?.addEventListener('input', () => {
    btn.disabled = input.value.trim().length === 0;
  });

  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && input.value.trim()) send();
  });

  btn?.addEventListener('click', send);

  async function send() {
    if (!currentConversation) return;

    const content = input.value.trim();
    input.value = '';
    btn.disabled = true;

    try {
      await API.post('/api/messages', {
        conversation_id: currentConversation,
        content,
      });
      await loadMessages();
    } catch (err) {
      showToast(err.message);
      input.value = content;   // on rend le texte à l'utilisateur
    }
  }
}


/* ---------- Nouvelle conversation ---------- */

/*
 * On suggère les utilisateurs depuis /api/search/suggest plutôt que de
 * demander un pseudo à l'aveugle. L'utilisateur clique au lieu de deviner
 * l'orthographe exacte.
 */
function wireNewConversation() {
  const input = document.getElementById('newConvSearch');
  const panel = document.getElementById('newConvSuggestions');
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

        // On ne garde que les utilisateurs, et pas soi-même
        const users = suggestions.filter(
          s => s.type === 'user' && s.label !== Auth.user?.username);

        if (!users.length) {
          panel.innerHTML = `
            <p class="px-3 py-2 text-xs text-neutral-500">No user found.</p>`;
          panel.classList.remove('hidden');
          return;
        }

        panel.innerHTML = users.map(u => `
          <button data-username="${escapeHtml(u.label)}"
                  class="flex w-full items-center gap-2.5 px-3 py-2 text-left
                         text-sm hover:bg-edge">
            <span class="flex h-7 w-7 items-center justify-center rounded-full
                         border border-edge bg-ink text-xs font-medium">
              ${escapeHtml(u.label[0].toUpperCase())}
            </span>
            ${escapeHtml(u.label)}
          </button>
        `).join('');
        panel.classList.remove('hidden');

        panel.querySelectorAll('button').forEach(btn => {
          btn.addEventListener('click', () => start(btn.dataset.username));
        });

      } catch (err) {
        panel.classList.add('hidden');
      }
    }, 250);
  });

  document.addEventListener('click', (e) => {
    if (!panel.contains(e.target) && e.target !== input) {
      panel.classList.add('hidden');
    }
  });

  async function start(username) {
    input.value = '';
    panel.classList.add('hidden');

    try {
      const { conversation } = await API.post('/api/conversations', { username });
      await loadConversations();
      openConversation(conversation.id, username);
    } catch (err) {
      showToast(err.message);
    }
  }
}


/* ---------- Polling ---------- */

function startPolling() {
  stopPolling();
  // 4 secondes : compromis entre réactivité et charge serveur
  pollTimer = setInterval(() => loadMessages(), 4000);
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
}

// On arrête le polling quand l'onglet passe en arrière-plan : inutile de
// solliciter le serveur si personne ne regarde.
document.addEventListener('visibilitychange', () => {
  if (document.hidden) stopPolling();
  else if (currentConversation) startPolling();
});


function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
