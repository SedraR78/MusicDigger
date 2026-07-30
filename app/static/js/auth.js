/*
 * Connexion et inscription.
 *
 * Le même fichier sert les deux pages : il détecte la présence des boutons
 * pour savoir sur laquelle il tourne.
 *
 * Note : les mots de passe partent en clair dans le corps de la requête.
 * C'est normal — c'est HTTPS qui les chiffre en transit. En local on est en
 * HTTP, donc à ne jamais faire en production sans certificat.
 */

document.addEventListener('DOMContentLoaded', () => {
  const loginBtn    = document.getElementById('loginBtn');
  const registerBtn = document.getElementById('registerBtn');

  // Déjà connecté : inutile de rester sur ces pages
  if (Auth.isLoggedIn && (loginBtn || registerBtn)) {
    window.location.href = '/trending';
    return;
  }

  if (loginBtn)    wireLogin(loginBtn);
  if (registerBtn) wireRegister(registerBtn);
  wireDemoAccounts();
  wireEnterKey();
});


/* ---------- Connexion ---------- */

function wireLogin(button) {
  button.addEventListener('click', async () => {
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
      showToast('Email and password are required');
      return;
    }

    button.disabled = true;
    button.textContent = 'Logging in...';

    try {
      const data = await API.post('/api/auth/login', { email, password });

      // On stocke les deux tokens + l'utilisateur pour la navbar
      Auth.save(data.access_token, data.refresh_token, data.user);
      window.location.href = '/trending';

    } catch (err) {
      // Le serveur renvoie le même message que l'email existe ou non,
      // pour ne pas permettre d'énumérer les comptes.
      showToast(err.message);
      button.disabled = false;
      button.textContent = 'Log in';
    }
  });
}


/* ---------- Inscription ---------- */

function wireRegister(button) {
  button.addEventListener('click', async () => {
    const username = document.getElementById('username').value.trim();
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    // Validation côté client : uniquement pour le confort.
    // Le serveur revalide tout — on ne fait jamais confiance au client.
    if (username.length < 3) {
      showToast('Username must be at least 3 characters');
      return;
    }
    if (password.length < 8) {
      showToast('Password must be at least 8 characters');
      return;
    }

    button.disabled = true;
    button.textContent = 'Creating account...';

    try {
      const data = await API.post('/api/auth/register', {
        username, email, password,
      });

      Auth.save(data.access_token, data.refresh_token, data.user);
      showToast('Welcome to MusicDigger', 'info');
      // Un nouveau compte n'a aucun signal de goût : on l'envoie sur DigsCover
      setTimeout(() => (window.location.href = '/digscover'), 700);

    } catch (err) {
      // 409 si l'email ou le username est déjà pris
      showToast(err.message);
      button.disabled = false;
      button.textContent = 'Create account';
    }
  });
}


/* ---------- Comptes de démo ---------- */

function wireDemoAccounts() {
  document.querySelectorAll('[data-demo]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('email').value = btn.dataset.demo;
      document.getElementById('password').value = 'password123';
      document.getElementById('loginBtn')?.focus();
    });
  });
}


/* ---------- Entrée pour valider ---------- */

function wireEnterKey() {
  document.querySelectorAll('input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        document.getElementById('loginBtn')?.click();
        document.getElementById('registerBtn')?.click();
      }
    });
  });
}
