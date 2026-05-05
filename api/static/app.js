const state = {
  token: localStorage.getItem("gm_token") || "",
  tecnico: JSON.parse(localStorage.getItem("gm_tecnico") || "null"),
  tab: "mis",
};

function setAuth(token, tecnico) {
  state.token = token;
  state.tecnico = tecnico;
  localStorage.setItem("gm_token", token);
  localStorage.setItem("gm_tecnico", JSON.stringify(tecnico));
}

function clearAuth() {
  state.token = "";
  state.tecnico = null;
  localStorage.removeItem("gm_token");
  localStorage.removeItem("gm_tecnico");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function badgeClass(estado) {
  const normalized = estado.toLowerCase();
  if (normalized === "en_progreso") return "en-progreso";
  if (normalized === "completada") return "completada";
  if (normalized === "cancelada") return "cancelada";
  return "pendiente";
}

async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) {
    clearAuth();
    render();
    throw new Error("Sesión vencida.");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Error inesperado." }));
    throw new Error(payload.detail || "Error inesperado.");
  }
  return response.json();
}

function layout(content, active = "ordenes") {
  return `
    <div class="app-shell">${content}</div>
    <nav class="bottom-nav">
      <a class="nav-link ${active === "ordenes" ? "active" : ""}" href="#ordenes">Órdenes</a>
      <a class="nav-link ${active === "biblioteca" ? "active" : ""}" href="#biblioteca">Biblioteca</a>
    </nav>
  `;
}

function loginView(error = "") {
  return `
    <div class="login-shell">
      <form class="login-card" id="login-form">
        <h1 class="title">Técnico de Mantenimiento</h1>
        <p class="subtitle">Acceso móvil a órdenes y programas.</p>
        <div class="field">
          <label for="dni">DNI</label>
          <input id="dni" name="dni" required />
        </div>
        <div class="field">
          <label for="password">Contraseña</label>
          <input id="password" name="password" type="password" required />
        </div>
        <button class="button primary" type="submit">Ingresar</button>
        ${error ? `<p class="error">${escapeHtml(error)}</p>` : ""}
      </form>
    </div>
  `;
}

function renderLoading(text = "Cargando...") {
  document.querySelector("#app").innerHTML = layout(`<div class="panel">${escapeHtml(text)}</div>`);
}

function ordenCard(orden) {
  return `
    <a class="card" href="#orden/${orden.id}">
      <div class="badge ${badgeClass(orden.estado)}">${escapeHtml(orden.estado)}</div>
      <h3>${escapeHtml(orden.equipo_nombre)}</h3>
      <div>${escapeHtml(orden.tipo)} · ${escapeHtml(orden.equipo_tipo_nombre)}</div>
      <div class="meta">
        <span>${escapeHtml(orden.fecha_apertura)}</span>
        <span>${escapeHtml(orden.equipo_ubicacion)}</span>
      </div>
      <div class="muted">${escapeHtml(orden.descripcion)}</div>
    </a>
  `;
}

async function renderOrdenes() {
  renderLoading("Cargando órdenes...");
  const ordenes = await apiFetch("/api/ordenes");
  const filtered = ordenes.filter((orden) => {
    if (state.tab === "mis") {
      return ["PENDIENTE", "EN_PROGRESO"].includes(orden.estado);
    }
    if (state.tab === "completadas") {
      return orden.estado === "COMPLETADA";
    }
    return true;
  });
  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <h1>Órdenes</h1>
        <div class="muted">${escapeHtml(state.tecnico.nombre)} ${escapeHtml(state.tecnico.apellido)}</div>
      </div>
      <button class="button secondary" id="logout-button">Salir</button>
    </div>
    <div class="tabs">
      <a class="tab ${state.tab === "mis" ? "active" : ""}" href="#ordenes?tab=mis">Mis órdenes</a>
      <a class="tab ${state.tab === "todas" ? "active" : ""}" href="#ordenes?tab=todas">Todas</a>
      <a class="tab ${state.tab === "completadas" ? "active" : ""}" href="#ordenes?tab=completadas">Completadas</a>
    </div>
    <div class="list">
      ${filtered.length ? filtered.map(ordenCard).join("") : '<div class="panel empty">No hay órdenes para mostrar.</div>'}
    </div>
  `, "ordenes");
  document.querySelector("#logout-button").addEventListener("click", () => {
    clearAuth();
    render();
  });
}

function programaMarkup(programa) {
  return `
    <div class="card">
      <h4>${escapeHtml(programa.descripcion)}</h4>
      <div class="meta">
        <span>Cada ${programa.frecuencia_meses} meses</span>
        <span>Próxima: ${escapeHtml(programa.proxima_ejecucion)}</span>
      </div>
      ${programa.adjuntos.length ? `
        <div class="meta">
          ${programa.adjuntos.map((adjunto) => `<a href="#programa/${programa.id}">${escapeHtml(adjunto.tipo)} · ${escapeHtml(adjunto.nombre)}</a>`).join("")}
        </div>
      ` : '<div class="muted">Sin adjuntos.</div>'}
    </div>
  `;
}

async function renderOrdenDetalle(ordenId) {
  renderLoading("Cargando orden...");
  const orden = await apiFetch(`/api/ordenes/${ordenId}`);
  const asignadaAMi = orden.tecnico_id === state.tecnico.id;
  const puedeAceptar = orden.estado === "PENDIENTE";
  const puedeTrabajar = orden.estado === "EN_PROGRESO" && asignadaAMi;
  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <a class="back-link" href="#ordenes">← Volver</a>
        <h2>${escapeHtml(orden.equipo_nombre)}</h2>
      </div>
    </div>
    <div class="panel">
      <div class="badge ${badgeClass(orden.estado)}">${escapeHtml(orden.estado)}</div>
      <h3>${escapeHtml(orden.tipo)}</h3>
      <div class="meta">
        <span>${escapeHtml(orden.equipo_ubicacion)}</span>
        <span>${escapeHtml(orden.equipo_marca)} ${escapeHtml(orden.equipo_modelo)}</span>
      </div>
      <div class="prewrap">${escapeHtml(orden.descripcion)}</div>
    </div>
    <div class="panel">
      <div class="section-title">Observaciones</div>
      <div class="prewrap">${escapeHtml(orden.observaciones || "Sin observaciones.")}</div>
    </div>
    <div class="panel">
      <div class="section-title">Repuestos</div>
      ${orden.repuestos.length ? orden.repuestos.map((item) => `
        <div class="card">
          <h4>${escapeHtml(item.descripcion)}</h4>
          <div class="meta">
            <span>Cantidad: ${item.cantidad}</span>
            <span>Costo: ${item.costo_unitario}</span>
          </div>
        </div>
      `).join("") : '<div class="muted">Sin repuestos.</div>'}
    </div>
    <div class="panel">
      <div class="section-title">Programas vinculados</div>
      ${orden.programas.length ? orden.programas.map(programaMarkup).join("") : '<div class="muted">Sin programas vinculados.</div>'}
    </div>
    ${puedeAceptar ? `
      <div class="panel">
        <button class="button success" id="accept-button">Aceptar orden</button>
      </div>
    ` : ""}
    ${puedeTrabajar ? `
      <div class="panel">
        <form id="note-form">
          <div class="field">
            <label for="nota">Agregar observación</label>
            <textarea id="nota" name="nota"></textarea>
          </div>
          <div class="button-row">
            <button class="button secondary" type="submit">Guardar nota</button>
            <button class="button success" type="button" id="complete-button">Marcar completada</button>
          </div>
        </form>
      </div>
    ` : ""}
  `, "ordenes");

  const acceptButton = document.querySelector("#accept-button");
  if (acceptButton) {
    acceptButton.addEventListener("click", async () => {
      if (!window.confirm("¿Confirmar que vas a realizar esta orden?")) return;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/aceptar`, { method: "POST" });
        location.hash = `#orden/${ordenId}`;
      } catch (error) {
        window.alert(error.message);
      }
    });
  }

  const noteForm = document.querySelector("#note-form");
  if (noteForm) {
    noteForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const texto = noteForm.nota.value.trim();
      if (!texto) return;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/observaciones`, {
          method: "POST",
          body: JSON.stringify({ texto }),
        });
        location.hash = `#orden/${ordenId}`;
      } catch (error) {
        window.alert(error.message);
      }
    });
  }

  const completeButton = document.querySelector("#complete-button");
  if (completeButton) {
    completeButton.addEventListener("click", async () => {
      const observaciones = document.querySelector("#nota").value.trim();
      if (!window.confirm("¿Confirmar que la orden quedó completada?")) return;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/completar`, {
          method: "POST",
          body: JSON.stringify({ observaciones }),
        });
        location.hash = "#ordenes?tab=completadas";
      } catch (error) {
        window.alert(error.message);
      }
    });
  }
}

async function renderBiblioteca() {
  renderLoading("Cargando equipos...");
  const equipos = await apiFetch("/api/equipos");
  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <h1>Biblioteca</h1>
        <div class="muted">Equipos y programas</div>
      </div>
    </div>
    <div class="list">
      ${equipos.map((equipo) => `
        <a class="card" href="#equipo/${equipo.id}">
          <h3>${escapeHtml(equipo.nombre)}</h3>
          <div>${escapeHtml(equipo.tipo_nombre)}</div>
          <div class="meta">
            <span>${escapeHtml(equipo.ubicacion)}</span>
            <span>${equipo.programas_activos_count} programas</span>
          </div>
        </a>
      `).join("")}
    </div>
  `, "biblioteca");
}

async function renderEquipoDetalle(equipoId) {
  renderLoading("Cargando equipo...");
  const equipo = await apiFetch(`/api/equipos/${equipoId}`);
  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <a class="back-link" href="#biblioteca">← Volver</a>
        <h2>${escapeHtml(equipo.nombre)}</h2>
      </div>
    </div>
    <div class="panel">
      <div>${escapeHtml(equipo.tipo_nombre)}</div>
      <div class="meta">
        <span>${escapeHtml(equipo.marca)} ${escapeHtml(equipo.modelo)}</span>
        <span>${escapeHtml(equipo.ubicacion)}</span>
      </div>
      <div class="prewrap">${escapeHtml(equipo.observaciones || "Sin observaciones.")}</div>
    </div>
    <div class="panel">
      <div class="section-title">Programas</div>
      ${equipo.programas.length ? equipo.programas.map(programaMarkup).join("") : '<div class="muted">Sin programas activos.</div>'}
    </div>
  `, "biblioteca");
}

async function renderProgramaDetalle(programaId) {
  renderLoading("Cargando programa...");
  const programa = await apiFetch(`/api/programas/${programaId}`);
  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <a class="back-link" href="#biblioteca">← Volver</a>
        <h2>${escapeHtml(programa.descripcion)}</h2>
      </div>
    </div>
    <div class="panel">
      <div>${escapeHtml(programa.equipo_nombre)}</div>
      <div class="meta">
        <span>Cada ${programa.frecuencia_meses} meses</span>
        <span>Próxima: ${escapeHtml(programa.proxima_ejecucion)}</span>
      </div>
    </div>
    <div class="panel">
      <div class="section-title">Adjuntos</div>
      ${programa.adjuntos.length ? programa.adjuntos.map((adjunto) => `
        <a class="card" ${adjunto.tipo === "PDF" ? 'target="_blank"' : ""} href="/api/adjuntos/${adjunto.id}">
          <h4>${adjunto.tipo === "FOTO" ? "Foto" : "PDF"}</h4>
          <div>${escapeHtml(adjunto.nombre)}</div>
        </a>
      `).join("") : '<div class="muted">Sin adjuntos.</div>'}
    </div>
  `, "biblioteca");
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const payload = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ dni: form.dni.value.trim(), password: form.password.value }),
    });
    setAuth(payload.access_token, payload.tecnico);
    location.hash = "#ordenes";
    render();
  } catch (error) {
    document.querySelector("#app").innerHTML = loginView(error.message);
    document.querySelector("#login-form").addEventListener("submit", handleLoginSubmit);
  }
}

function parseHash() {
  const raw = location.hash.slice(1) || "ordenes";
  const [path, queryString = ""] = raw.split("?");
  return { path, query: new URLSearchParams(queryString) };
}

async function render() {
  if (!state.token || !state.tecnico) {
    document.querySelector("#app").innerHTML = loginView();
    document.querySelector("#login-form").addEventListener("submit", handleLoginSubmit);
    return;
  }
  const { path, query } = parseHash();
  if (path === "ordenes") {
    state.tab = query.get("tab") || "mis";
    await renderOrdenes();
    return;
  }
  if (path.startsWith("orden/")) {
    await renderOrdenDetalle(path.split("/")[1]);
    return;
  }
  if (path === "biblioteca") {
    await renderBiblioteca();
    return;
  }
  if (path.startsWith("equipo/")) {
    await renderEquipoDetalle(path.split("/")[1]);
    return;
  }
  if (path.startsWith("programa/")) {
    await renderProgramaDetalle(path.split("/")[1]);
    return;
  }
  location.hash = "#ordenes";
}

window.addEventListener("hashchange", () => {
  render().catch((error) => window.alert(error.message));
});

render().catch((error) => {
  document.querySelector("#app").innerHTML = loginView(error.message);
  document.querySelector("#login-form").addEventListener("submit", handleLoginSubmit);
});
