# 🎓 Guía Maestra: Validaciones y Alertas Visuales en la Misma Vista
### *Proyecto Debatto — Manual Pedagógico para el Docente y el Alumno*

---

## 📌 1. Diagnóstico: ¿Por qué ocurre el problema actual?

### El Comportamiento Actual
En `templates/sidebar.html`, los formularios de Login y Signup están definidos como formularios HTML tradicionales:
```html
<form action="{{ url_for('login') }}" method="post" id="login-form">
    <input type="text" name="username">
    <input type="password" name="password">
    <button type="submit">Go</button>
</form>
```
Y en `newapp.py`:
```python
@app.route("/login", methods=["POST"])
def login():
    ...
    if not user:
        return "User not found", 404
    if not check_password_hash(user["password"], password):
        return "Incorrect password", 401
```

### ¿Qué pasa en el navegador?
1. Al hacer click en "Go", el navegador realiza un **POST síncrono** tradicional.
2. El navegador **abandona la página actual** (sea Home, un debate o un perfil) y navega a la URL `/login`.
3. Como Flask devuelve un texto plano (`"User not found"`) con código 404, la pantalla se vuelve blanca mostrando solo ese texto.
4. El usuario está obligado a presionar la flecha "Atrás" de su navegador para volver a donde estaba.

---

## 🎯 2. La Solución Arquitectónica: Las 3 Capas de Validación

Para lograr una experiencia de usuario moderna (UX profesional), la validación debe dividirse en 3 capas complementarias:

```
[Usuario llena el formulario]
          │
          ▼
[Capa 1: Validación Front-End Instantánea] ──► ¿Datos inválidos? ──► Muestra Tooltip/Alerta en la vista
          │ (Datos válidos)
          ▼
[Capa 2: Envío Asíncrono con fetch() AJAX] ──► (No recarga la página)
          │
          ▼
[Capa 3: Validación Back-End en Flask] ────► ¿Credenciales erróneas? ──► Responde JSON {ok: false, error: "..."}
          │                                                                      │
          ▼ (Credenciales válidas)                                               ▼
     Responde JSON {ok: true}                                    JavaScript dibuja la alerta roja
          │                                                       en el formulario sin cambiar de URL
          ▼
     Recarga suave / actualiza sesión
```

1. **Capa 1 (Front-end instantáneo):** Atrapa errores obvios antes de tocar el servidor (ej: campos vacíos, contraseñas de menos de 5 caracteres, archivos mayores a 5MB).
2. **Capa 2 (Comunicación asíncrona / Fetch):** Intercepta el evento `submit`, envía los datos en segundo plano por HTTP sin recargar la página.
3. **Capa 3 (Back-end Flask con JSON):** Valida reglas de negocio (ej: si el usuario existe en la base de datos). Si falla, responde un objeto JSON `{ "ok": false, "error": "Usuario o contraseña incorrectos" }`.

---

## 🎨 3. Diseño Visual: Alertas, Tooltips e Inputs con Error

Agregamos estilos CSS en `static/style.css` acordes a la estética oscura de Debatto (`#151515`, `#1f1f1f`, bordes luminosos y microanimaciones).

### 3.1 Clases CSS a incorporar en `static/style.css`

```css
/* --- SISTEMA DE VALIDACIONES Y ALERTAS --- */

/* 1. Estado de error en inputs */
.input-error {
    border: 1px solid #ff4d4d !important;
    background-color: rgba(255, 77, 77, 0.08) !important;
    animation: shake 0.35s ease-in-out;
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-5px); }
    40%, 80% { transform: translateX(5px); }
}

/* 2. Banner de Alerta Inline */
.debatto-alert {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;
    line-height: 1.3;
    animation: fadeInSlide 0.25s ease-out;
}

.debatto-alert.error {
    background-color: rgba(255, 77, 77, 0.15);
    border: 1px solid #ff4d4d;
    color: #ff8585;
    box-shadow: 0 0 10px rgba(255, 77, 77, 0.2);
}

.debatto-alert.success {
    background-color: rgba(46, 204, 113, 0.15);
    border: 1px solid #2ecc71;
    color: #69f0ae;
    box-shadow: 0 0 10px rgba(46, 204, 113, 0.2);
}

.debatto-alert.warning {
    background-color: rgba(243, 156, 18, 0.15);
    border: 1px solid #f39c12;
    color: #f1c40f;
}

@keyframes fadeInSlide {
    from {
        opacity: 0;
        transform: translateY(-6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 3. Tooltip contextual debajo de un campo */
.field-tooltip {
    display: block;
    color: #ff6b6b;
    font-size: 0.75rem;
    margin-top: 3px;
    margin-bottom: 6px;
    animation: fadeInSlide 0.2s ease-out;
}

/* 4. Contador dinámico de caracteres */
.char-counter {
    font-size: 0.75rem;
    color: #888;
    margin-top: 2px;
    text-align: right;
    display: block;
}
.char-counter.limit-reached {
    color: #ff4d4d;
    font-weight: bold;
}
```

---

## 🛠️ 4. Guía Práctica de Implementación por Casos

---

### CASO 1: Login y Registro en el Sidebar (El caso crítico de la consulta)

#### Paso A: Ajustar el Backend en `newapp.py`
En lugar de devolver un string plano como `"User not found", 404`, Flask debe responder con `jsonify()` para que JavaScript procese el resultado sin recargar la página.

Asegurarse de importar `jsonify`:
```python
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,  # <--- AGREGAR ESTE IMPORT
)
```

Modificar la ruta `/login`:
```python
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Validación rápida de presencia
    if not username or not password:
        return jsonify({
            "ok": False, 
            "error": "Por favor completá usuario y contraseña."
        }), 400

    db = getdb()
    user = db.execute(
        "SELECT * FROM users WHERE lower(username) = lower(?)",
        (username,),
    ).fetchone()

    # Tip de Seguridad: usar un mensaje homogéneo ("Usuario o contraseña incorrectos")
    # para evitar que atacantes adivinen qué nombres de usuario existen.
    if not user or not check_password_hash(user["password"], password):
        return jsonify({
            "ok": False, 
            "error": "Usuario o contraseña incorrectos."
        }), 401

    session["username"] = user["username"]
    session["userid"] = user["id"]

    return jsonify({"ok": True, "message": "¡Sesión iniciada con éxito!"})
```

Y para la ruta `/signup`:
```python
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username", "").strip()
    rawpassword = request.form.get("password", "")
    email = request.form.get("email", "").strip()

    if len(username) < 3:
        return jsonify({"ok": False, "error": "El usuario debe tener al menos 3 caracteres."}), 400
    if len(username) > 25:
        return jsonify({"ok": False, "error": "El usuario no puede superar 25 caracteres."}), 400
    if len(rawpassword) < 5:
        return jsonify({"ok": False, "error": "La contraseña debe tener al menos 5 caracteres."}), 400
    if len(rawpassword) > 30:
        return jsonify({"ok": False, "error": "La contraseña no puede superar 30 caracteres."}), 400

    reserved = ["debatto", "anonymous"]
    if username.lower() in reserved:
        return jsonify({"ok": False, "error": "Ese nombre de usuario está reservado."}), 400

    db = getdb()
    existing_user = db.execute(
        "SELECT id FROM users WHERE lower(username) = lower(?)",
        (username,),
    ).fetchone()

    if existing_user:
        return jsonify({"ok": False, "error": "Ese nombre de usuario ya está registrado."}), 409

    password = generate_password_hash(rawpassword)
    cursor = db.execute(
        """
        INSERT INTO users (username, password, email, joined)
        VALUES (?, ?, ?, ?)
        """,
        (username, password, email, datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S")),
    )
    db.commit()

    session["username"] = username
    session["userid"] = cursor.lastrowid

    return jsonify({"ok": True, "message": "¡Cuenta creada exitosamente!"})
```

---

#### Paso B: Ajustar el HTML en `templates/sidebar.html`
Agregamos un contenedor para las alertas dentro de cada formulario y asignamos el manejador `onsubmit`:

```html
<!-- Formulario de Login -->
<form id="login-form" style="display:none;" onsubmit="handleAuthSubmit(event, '{{ url_for('login') }}', this)">
    <!-- Contenedor donde aparecerá la alerta dinámica -->
    <div class="form-feedback" id="login-feedback"></div>

    <input type="text" placeholder="Username" data-i18n-placeholder="username_placeholder" name="username">
    <input type="password" placeholder="Password" data-i18n-placeholder="password_placeholder" name="password">
    <button type="submit" data-i18n="btn_go">Go</button>
    <button type="button" onclick="showButtons()" data-i18n="btn_back">Back</button>
</form>

<!-- Formulario de Signup -->
<form id="signup-form" style="display:none;" onsubmit="handleAuthSubmit(event, '{{ url_for('signup') }}', this)">
    <!-- Contenedor donde aparecerá la alerta dinámica -->
    <div class="form-feedback" id="signup-feedback"></div>

    <input type="text" placeholder="Username" data-i18n-placeholder="username_placeholder" name="username">
    <input type="password" placeholder="Password" data-i18n-placeholder="password_placeholder" name="password">
    <input type="email" placeholder="E-mail (Optional)" data-i18n-placeholder="email_placeholder" name="email">
    <button type="submit" data-i18n="btn_go">Go</button>
    <button type="button" onclick="showButtons()" data-i18n="btn_back">Back</button>
</form>
```

#### Paso C: Script JavaScript en `templates/sidebar.html`

```javascript
// Función para mostrar alertas con estilo Debatto
function showInlineAlert(container, message, type = "error") {
    const icon = type === "error" ? "⚠️" : (type === "success" ? "✅" : "ℹ️");
    container.innerHTML = `
        <div class="debatto-alert ${type}">
            <span>${icon}</span>
            <span>${message}</span>
        </div>
    `;
}

// Limpiar alertas al cambiar de vista en el sidebar
function showLogin() {
    clearFeedback();
    document.getElementById("account-buttons").style.display = "none";
    document.getElementById("signup-form").style.display = "none";
    document.getElementById("login-form").style.display = "block";
}

function showSignup() {
    clearFeedback();
    document.getElementById("account-buttons").style.display = "none";
    document.getElementById("login-form").style.display = "none";
    document.getElementById("signup-form").style.display = "block";
}

function showButtons() {
    clearFeedback();
    document.getElementById("login-form").style.display = "none";
    document.getElementById("signup-form").style.display = "none";
    document.getElementById("account-buttons").style.display = "block";
}

function clearFeedback() {
    document.querySelectorAll('.form-feedback').forEach(el => el.innerHTML = '');
    document.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));
}

// Controlador maestro de Login y Signup
async function handleAuthSubmit(event, url, formElement) {
    event.preventDefault(); // 1. CRUCIAL: Evita que el navegador navegue y cambie de pantalla

    const feedbackDiv = formElement.querySelector('.form-feedback');
    const submitBtn = formElement.querySelector('button[type="submit"]');

    // Limpiar alertas y clases de error previas
    feedbackDiv.innerHTML = "";
    formElement.querySelectorAll('input').forEach(input => input.classList.remove('input-error'));

    // 2. Validación Frontend instantánea
    const usernameInput = formElement.querySelector('input[name="username"]');
    const passwordInput = formElement.querySelector('input[name="password"]');

    if (!usernameInput.value.trim()) {
        showInlineAlert(feedbackDiv, "Ingresá tu nombre de usuario.", "error");
        usernameInput.classList.add('input-error');
        usernameInput.focus();
        return;
    }

    if (!passwordInput.value) {
        showInlineAlert(feedbackDiv, "Ingresá tu contraseña.", "error");
        passwordInput.classList.add('input-error');
        passwordInput.focus();
        return;
    }

    // 3. Indicador de carga
    submitBtn.disabled = true;
    const originalBtnText = submitBtn.textContent;
    submitBtn.textContent = "...";

    try {
        const formData = new FormData(formElement);
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.ok) {
            // Éxito: mostrar mensaje verde y recargar suavemente la página
            showInlineAlert(feedbackDiv, data.message || "¡Acceso concedido!", "success");
            setTimeout(() => {
                window.location.reload(); // Recarga en el mismo lugar con la sesión activa
            }, 600);
        } else {
            // Error devuelto por Flask (ej: contraseña incorrecta, usuario existente)
            showInlineAlert(feedbackDiv, data.error || "Ocurrió un error.", "error");
            formElement.querySelectorAll('input:not([type="email"])').forEach(input => {
                input.classList.add('input-error');
            });
        }
    } catch (err) {
        showInlineAlert(feedbackDiv, "No se pudo conectar con el servidor.", "error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    }
}
```

---

### CASO 2: Creación de Publicaciones (`templates/newpost.html`)

En `newpost.html` podemos aplicar validaciones visuales preventivas de alta calidad:

1. **Contador dinámico de caracteres según el Nivel de Seriedad**:
   - Nivel 1: hasta 2.000 caracteres.
   - Nivel 5: hasta 10.000 caracteres.

```html
<!-- En newpost.html, agregar el contenedor de alerta y el contador debajo del textarea -->
<div id="post-alert-box"></div>

...
<textarea class="pcontent" id="post-content" name="content"></textarea>
<span id="content-char-counter" class="char-counter">0 / 2000 caracteres</span>
```

```javascript
// Script en newpost.html
const levelSelect = document.querySelector('select[name="level"]');
const contentArea = document.getElementById('post-content');
const charCounter = document.getElementById('content-char-counter');
const alertBox = document.getElementById('post-alert-box');

function updateLimits() {
    const level = parseInt(levelSelect.value) || 1;
    const maxChars = level * 2000;
    contentArea.maxLength = maxChars;

    const currentLength = contentArea.value.length;
    charCounter.textContent = `${currentLength} / ${maxChars} caracteres (Nivel ${level})`;

    if (currentLength >= maxChars) {
        charCounter.classList.add('limit-reached');
    } else {
        charCounter.classList.remove('limit-reached');
    }
}

levelSelect.addEventListener('change', updateLimits);
contentArea.addEventListener('input', updateLimits);

// Validación de imágenes antes de subir (máximo 5MB por archivo)
document.getElementById('image-input').addEventListener('change', function () {
    const maxBytes = 5 * 1024 * 1024;
    for (const file of this.files) {
        if (file.size > maxBytes) {
            showInlineAlert(alertBox, `El archivo "${file.name}" supera los 5MB permitidos.`, "error");
            this.value = ""; // Anula la selección
            document.getElementById('image-preview').innerHTML = "";
            return;
        }
    }
    alertBox.innerHTML = "";
});

// Validación al enviar el formulario
document.querySelector('.formpost').addEventListener('submit', function (e) {
    alertBox.innerHTML = "";
    const title = this.title.value.trim();
    const level = this.level.value;
    const content = this.content.value.trim();
    const topic1 = this.topic1.value.trim();

    if (!title) {
        e.preventDefault();
        showInlineAlert(alertBox, "El título de la publicación es obligatorio.", "error");
        this.title.classList.add('input-error');
        this.title.focus();
        return;
    }

    if (!level) {
        e.preventDefault();
        showInlineAlert(alertBox, "Por favor seleccioná el nivel de seriedad del debate.", "error");
        this.level.classList.add('input-error');
        this.level.focus();
        return;
    }

    if (!content) {
        e.preventDefault();
        showInlineAlert(alertBox, "El contenido del debate no puede estar vacío.", "error");
        this.content.classList.add('input-error');
        this.content.focus();
        return;
    }

    if (!topic1) {
        e.preventDefault();
        showInlineAlert(alertBox, "Debés agregar al menos un tema (Topic 1).", "error");
        this.topic1.classList.add('input-error');
        this.topic1.focus();
        return;
    }
});
```

---

### CASO 3: Respuestas y Debates (`templates/post.html`)

En `post.html`, cuando un usuario comenta o replica a otro usuario, actualmente si no selecciona una Marca (`rtype`) o deja el texto vacío, Flask devuelve un error 400.

#### Solución:
Agregar una función de validación que se ejecute en el evento `onsubmit` de los formularios de respuesta:

```html
<form action="{{ url_for('post', post_id=post.id) }}" class="reply" method="post" onsubmit="return validateReplyForm(this);">
    <!-- Contenedor para alerta local en este formulario específico -->
    <div class="reply-feedback"></div>

    <input type="text" name="rcontent" placeholder="Write a response...">
    <input type="hidden" name="post_id" value="{{ post.id }}">
    <br>
    <select name="rtype">
        <option value="" disabled selected>Marks</option>
        <option value="agreed !">Agreed (!)</option>
        <option value="disagreed !">Disagreed (!)</option>
        <option value="neutral -">Neutral (-)</option>
        <option value="clarification +">Clarification (+)</option>
        <option value="doubt ?">Doubt (?)</option>
        <option value="suggestion !?">Suggestion (!?)</option>
        <option value="countershift !!">Countershift (!!)</option>
    </select>
    <button type="submit">Post Response</button>
</form>
```

```javascript
function validateReplyForm(form) {
    const feedback = form.querySelector('.reply-feedback');
    const content = form.rcontent.value.trim();
    const mark = form.rtype.value;
    const isUserLogged = {{ 'true' if session.get('username') else 'false' }};

    feedback.innerHTML = "";
    form.rcontent.classList.remove('input-error');
    form.rtype.classList.remove('input-error');

    if (!isUserLogged) {
        showInlineAlert(feedback, "Debés iniciar sesión en la barra lateral para participar del debate.", "warning");
        if (typeof showLogin === "function") showLogin();
        return false; // Detiene el envío
    }

    if (!content) {
        showInlineAlert(feedback, "Por favor escribí un mensaje antes de responder.", "error");
        form.rcontent.classList.add('input-error');
        form.rcontent.focus();
        return false;
    }

    if (!mark) {
        showInlineAlert(feedback, "Seleccioná una Marca de debate (Agreed, Disagreed, etc.).", "error");
        form.rtype.classList.add('input-error');
        form.rtype.focus();
        return false;
    }

    return true; // Envío permitido
}
```

---

## 📋 5. Plan de Aprendizaje / Ejercicios para el Alumno

Para que el alumno construya y asimile el conocimiento, guialo con estas 4 misiones prácticas:

| Misión | Objetivo | Archivos Involucrados |
| :--- | :--- | :--- |
| **Misión 1: Estilizado** | Crear las clases `.debatto-alert`, `.input-error` y la animación `@keyframes shake` | `static/style.css` |
| **Misión 2: Auth sin recargas** | Convertir `/login` y `/signup` a respuestas JSON con `jsonify()` y conectar `fetch()` con `preventDefault()` | `newapp.py`, `templates/sidebar.html` |
| **Misión 3: Formulario Inteligente** | Implementar límite dinámico de caracteres y chequeo de 5MB de imágenes | `templates/newpost.html` |
| **Misión 4: Respuestas Validadas** | Validar que no se envíen comentarios vacíos o sin marca en los debates | `templates/post.html` |

---

## 🔐 6. Cuadro Comparativo de Buenas Prácticas

1. **Nunca confiar únicamente en el Front-End**: El front-end brinda una experiencia visual inmediata, pero un usuario técnico podría enviar un POST con `curl` o Postman. La validación en Python (`newapp.py`) sigue siendo el escudo de seguridad.
2. **Mensajes de Autenticación Genéricos**: Decir "El usuario no existe" vs "La contraseña es incorrecta" le revela a un atacante qué usuarios están registrados. Usar siempre: *"Usuario o contraseña incorrectos"*.
3. **Persistencia de Datos**: Cuando un usuario comete un error en un texto largo, nunca obligarlo a recargar la página vaciando lo que escribió. La validación en la misma vista preserva todo lo redactado.
