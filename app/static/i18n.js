"use strict";

/* Translation dictionaries. Add a key here in both languages and reference it
   from HTML with data-i18n="key" (text) or data-i18n-attr="attr:key". */
const TRANSLATIONS = {
  en: {
    "nav.login": "Log in",
    "nav.signup": "Sign up",
    "nav.board": "Board",
    "nav.find": "Find jobs",
    "nav.logout": "Log out",
    "hero.title": "Track every job application in one place.",
    "hero.subtitle":
      "Search fresh remote listings, save the ones you like, and move them from saved to offer on a simple board. Free and open source.",
    "hero.cta_signup": "Get started — it's free",
    "hero.cta_login": "I already have an account",
    "feature.search.title": "Fresh listings",
    "feature.search.body": "Jobs pulled automatically from public job boards, updated daily.",
    "feature.board.title": "Kanban board",
    "feature.board.body": "Drag applications across saved, applied, interview and offer.",
    "feature.alerts.title": "Email alerts",
    "feature.alerts.body": "Get notified when new jobs match your keywords.",
    "auth.login_title": "Welcome back",
    "auth.signup_title": "Create your account",
    "auth.email": "Email",
    "auth.password": "Password",
    "auth.login_btn": "Log in",
    "auth.signup_btn": "Sign up",
    "auth.no_account": "Don't have an account?",
    "auth.have_account": "Already have an account?",
    "auth.switch_signup": "Sign up",
    "auth.switch_login": "Log in",
    "search.placeholder": "Search title, company or tag (e.g. python)...",
    "search.all_sources": "All sources",
    "search.remote_only": "Remote only",
    "search.button": "Search",
    "search.searching": "Searching...",
    "search.no_results": "No jobs match.",
    "search.save": "Save",
    "search.saved": "Saved ✓",
    "board.drop": "Drop a card here",
    "status.saved": "Saved",
    "status.applied": "Applied",
    "status.interview": "Interview",
    "status.offer": "Offer",
    "status.rejected": "Rejected",
    "panel.status": "Status",
    "panel.notes": "Notes",
    "panel.notes_ph": "Contacts, salary discussed, next steps...",
    "panel.open": "Open job posting ↗",
    "panel.delete": "Delete",
    "panel.save": "Save",
    "toast.moved": "Moved to",
    "toast.saved": "Saved",
    "toast.deleted": "Deleted",
    "toast.added": "Added to your board",
    "toast.already": "Already on your board",
    "confirm.delete": "Stop tracking this application?",
    "error.bad_login": "Incorrect email or password.",
    "error.email_taken": "That email is already registered.",
    "error.generic": "Something went wrong. Please try again.",
  },
  fr: {
    "nav.login": "Se connecter",
    "nav.signup": "S'inscrire",
    "nav.board": "Tableau",
    "nav.find": "Chercher des offres",
    "nav.logout": "Se déconnecter",
    "hero.title": "Suivez toutes vos candidatures au même endroit.",
    "hero.subtitle":
      "Trouvez des offres à distance récentes, sauvegardez celles qui vous plaisent, et faites-les passer de « sauvegardée » à « offre » sur un tableau simple. Gratuit et open source.",
    "hero.cta_signup": "Commencer — c'est gratuit",
    "hero.cta_login": "J'ai déjà un compte",
    "feature.search.title": "Offres récentes",
    "feature.search.body": "Des offres récupérées automatiquement sur des sites publics, mises à jour chaque jour.",
    "feature.board.title": "Tableau Kanban",
    "feature.board.body": "Glissez vos candidatures entre sauvegardée, postulée, entretien et offre.",
    "feature.alerts.title": "Alertes email",
    "feature.alerts.body": "Soyez notifiée quand de nouvelles offres correspondent à vos mots-clés.",
    "auth.login_title": "Bon retour",
    "auth.signup_title": "Créez votre compte",
    "auth.email": "Email",
    "auth.password": "Mot de passe",
    "auth.login_btn": "Se connecter",
    "auth.signup_btn": "S'inscrire",
    "auth.no_account": "Pas encore de compte ?",
    "auth.have_account": "Vous avez déjà un compte ?",
    "auth.switch_signup": "S'inscrire",
    "auth.switch_login": "Se connecter",
    "search.placeholder": "Chercher un titre, une entreprise ou un tag (ex. python)...",
    "search.all_sources": "Toutes les sources",
    "search.remote_only": "À distance uniquement",
    "search.button": "Chercher",
    "search.searching": "Recherche...",
    "search.no_results": "Aucune offre ne correspond.",
    "search.save": "Sauvegarder",
    "search.saved": "Sauvegardée ✓",
    "board.drop": "Déposez une carte ici",
    "status.saved": "Sauvegardée",
    "status.applied": "Postulée",
    "status.interview": "Entretien",
    "status.offer": "Offre",
    "status.rejected": "Refusée",
    "panel.status": "Statut",
    "panel.notes": "Notes",
    "panel.notes_ph": "Contacts, salaire évoqué, prochaines étapes...",
    "panel.open": "Ouvrir l'annonce ↗",
    "panel.delete": "Supprimer",
    "panel.save": "Enregistrer",
    "toast.moved": "Déplacée vers",
    "toast.saved": "Enregistré",
    "toast.deleted": "Supprimée",
    "toast.added": "Ajoutée à votre tableau",
    "toast.already": "Déjà sur votre tableau",
    "confirm.delete": "Arrêter le suivi de cette candidature ?",
    "error.bad_login": "Email ou mot de passe incorrect.",
    "error.email_taken": "Cet email est déjà utilisé.",
    "error.generic": "Une erreur est survenue. Réessayez.",
  },
};

let currentLang = localStorage.getItem("lang") || "en";

function t(key) {
  return (TRANSLATIONS[currentLang] && TRANSLATIONS[currentLang][key]) || key;
}

function applyTranslations(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  root.querySelectorAll("[data-i18n-attr]").forEach((el) => {
    const [attr, key] = el.dataset.i18nAttr.split(":");
    el.setAttribute(attr, t(key));
  });
  document.documentElement.lang = currentLang;
}

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem("lang", lang);
  applyTranslations();
  document.querySelectorAll("[data-lang-switch]").forEach(renderLangSwitch);
  document.dispatchEvent(new CustomEvent("langchange"));
}

function renderLangSwitch(container) {
  container.innerHTML = "";
  for (const lang of ["en", "fr"]) {
    const btn = document.createElement("button");
    btn.className = "lang-btn" + (lang === currentLang ? " active" : "");
    btn.textContent = lang.toUpperCase();
    btn.addEventListener("click", () => setLang(lang));
    container.appendChild(btn);
  }
}
