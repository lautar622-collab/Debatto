const translations = {
    en: {
        // Sidebar
        "tagline": "Where minds clash free",
        "btn_login": "Log In",
        "btn_signup": "Sign Up",
        "btn_back": "Back",
        "btn_go": "Go",
        "btn_logout": "Log Out",
        "nav_home": "Home",
        "nav_post": "Post",
        "nav_account": "Account",
        "search_placeholder": "Search...",
        "username_placeholder": "Username",
        "password_placeholder": "Password",
        "email_placeholder": "E-mail (Optional)",

        // Home
        "home_title": "Home",
        "seriousness_label": "Seriousness:",

        // New Post
        "newpost_title": "New Post",
        "title_placeholder": "Title (up to 200 characters)",
        "seriousness_select": "Seriousness",
        "content_placeholder": "Content",
        "add_topics": "Add topics",
        "attach_images": "Attach images",
        "attach_images_hint": "(optional · PNG, JPG, GIF, WEBP · max 5 MB each)",
        "choose_images_btn": "📎 Choose images",
        "attach_video": "Attach a video",
        "attach_video_hint": "(optional · paste a YouTube or direct video URL)",
        "video_placeholder": "https://www.youtube.com/watch?v=...",
        "btn_post": "Post",

        // Post view
        "seriousness_detail": "Seriousness:",
        "response_placeholder": "Write a response...",
        "marks_label": "Marks",
        "btn_post_response": "Post Response",
        "debate_title": "Debate",

        // Marks options
        "mark_agreed": "Agreed (!)",
        "mark_disagreed": "Disagreed (!)",
        "mark_neutral": "Neutral (-)",
        "mark_clarification": "Clarification (+)",
        "mark_doubt": "Doubt (?)",
        "mark_suggestion": "Suggestion (!?)",
        "mark_countershift": "Countershift (!!)",
    },
    es: {
        // Sidebar
        "tagline": "Donde las mentes chocan libres",
        "btn_login": "Ingresar",
        "btn_signup": "Registrarse",
        "btn_back": "Volver",
        "btn_go": "Ir",
        "btn_logout": "Cerrar sesión",
        "nav_home": "Inicio",
        "nav_post": "Publicar",
        "nav_account": "Mi cuenta",
        "search_placeholder": "Buscar...",
        "username_placeholder": "Usuario",
        "password_placeholder": "Contraseña",
        "email_placeholder": "E-mail (Opcional)",

        // Home
        "home_title": "Inicio",
        "seriousness_label": "Seriedad:",

        // New Post
        "newpost_title": "Nueva publicación",
        "title_placeholder": "Título (hasta 200 caracteres)",
        "seriousness_select": "Seriedad",
        "content_placeholder": "Contenido",
        "add_topics": "Agregar temas",
        "attach_images": "Adjuntar imágenes",
        "attach_images_hint": "(opcional · PNG, JPG, GIF, WEBP · máx 5 MB cada una)",
        "choose_images_btn": "📎 Elegir imágenes",
        "attach_video": "Adjuntar un video",
        "attach_video_hint": "(opcional · pegá una URL de YouTube o video directo)",
        "video_placeholder": "https://www.youtube.com/watch?v=...",
        "btn_post": "Publicar",

        // Post view
        "seriousness_detail": "Seriedad:",
        "response_placeholder": "Escribir una respuesta...",
        "marks_label": "Marcas",
        "btn_post_response": "Responder",
        "debate_title": "Debate",

        // Marks options
        "mark_agreed": "De acuerdo (!)",
        "mark_disagreed": "En desacuerdo (!)",
        "mark_neutral": "Neutral (-)",
        "mark_clarification": "Aclaración (+)",
        "mark_doubt": "Duda (?)",
        "mark_suggestion": "Sugerencia (!?)",
        "mark_countershift": "Contraposición (!!)",
    }
};

// Función principal: aplica el idioma a la página
function applyLanguage(lang) {
    localStorage.setItem('debatto_lang', lang);

    // Actualizar textos de elementos normales
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });

    // Actualizar placeholders de inputs/textareas
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[lang] && translations[lang][key]) {
            el.placeholder = translations[lang][key];
        }
    });

    // Marcar el botón activo
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
}

// Detectar idioma guardado o usar inglés por defecto
function initLanguage() {
    const savedLang = localStorage.getItem('debatto_lang') || 'en';
    applyLanguage(savedLang);
}

// Ejecutar cuando la página cargue
document.addEventListener('DOMContentLoaded', initLanguage);
