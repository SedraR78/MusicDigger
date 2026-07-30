/*
 * Couche d'accès à l'API.
 *
 * Centralise trois choses : le stockage du token, l'ajout automatique du
 * header Authorization, et la gestion uniforme des erreurs.
 *
 * Sans ça, chaque appel dans chaque page devrait répéter la même plomberie.
 */

const Auth = {
  get token()  { return localStorage.getItem('md_token'); },
  get user()   { return JSON.parse(localStorage.getItem('md_user') || 'null'); },

  save(token, refresh, user) {
    localStorage.setItem('md_token', token);
    localStorage.setItem('md_refresh', refresh);
    localStorage.setItem('md_user', JSON.stringify(user));
  },

  clear() {
    localStorage.removeItem('md_token');
    localStorage.removeItem('md_refresh');
    localStorage.removeItem('md_user');
  },

  get isLoggedIn() { return Boolean(this.token); },
};


const API = {
  /*
   * Appel générique. Ajoute le token si présent, parse le JSON, et lève
   * une erreur porteuse du message renvoyé par le serveur.
   *
   * C'est possible parce que TOUTES nos erreurs ont le même format :
   * {"error": "...", "code": 400}. Un seul gestionnaire suffit.
   */
  async request(path, { method = 'GET', body = null } = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (Auth.token) headers['Authorization'] = `Bearer ${Auth.token}`;

    const response = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    });

    // 204 No Content n'a pas de corps à parser
    const data = response.status === 204 ? {} : await response.json();

    if (!response.ok) {
      // Token expiré : on nettoie et on renvoie vers le login
      if (response.status === 401 && Auth.isLoggedIn) {
        Auth.clear();
        showToast('Session expired, please log in again');
        setTimeout(() => (window.location.href = '/login'), 1200);
      }
      throw new Error(data.error || 'Something went wrong');
    }

    return data;
  },

  get(path)         { return this.request(path); },
  post(path, body)  { return this.request(path, { method: 'POST', body }); },
  put(path, body)   { return this.request(path, { method: 'PUT', body }); },
  delete(path, body){ return this.request(path, { method: 'DELETE', body }); },
};


/* ---------- Toasts ---------- */

function showToast(message, kind = 'error') {
  const zone = document.getElementById('toastZone');
  if (!zone) return;

  const toast = document.createElement('div');
  toast.className = `rounded-lg px-4 py-2.5 text-sm shadow-xl border
    ${kind === 'error'
      ? 'bg-red-950 border-red-800 text-red-200'
      : 'bg-neutral-900 border-edge text-neutral-100'}`;
  toast.textContent = message;

  zone.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}
