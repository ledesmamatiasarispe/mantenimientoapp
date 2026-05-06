const state = {
  token: localStorage.getItem("gm_token") || "",
  tecnico: JSON.parse(localStorage.getItem("gm_tecnico") || "null"),
  tab: "pendientes",
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
    const detail = payload.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg || JSON.stringify(d)).join(", ")
      : String(detail || "Error inesperado.");
    throw new Error(message);
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
          <label for="legajo">Legajo</label>
          <input id="legajo" name="legajo" required />
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
  const tecnico = orden.tecnico_nombre ? ` · ${escapeHtml(orden.tecnico_nombre)}` : "";
  return `
    <a class="card" href="#orden/${orden.id}">
      <div class="card-header-row">
        <div class="badge ${badgeClass(orden.estado)}">${escapeHtml(orden.estado)}</div>
        <span class="tecnico-tag">${escapeHtml(orden.equipo_nombre)}${tecnico}</span>
      </div>
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

  let url = "/api/ordenes";
  if (state.tab === "pendientes")   url = "/api/ordenes?estado=PENDIENTE";
  if (state.tab === "mis")          url = "/api/ordenes?solo_mis=true";
  if (state.tab === "completadas")  url = "/api/ordenes?estado=COMPLETADA";
  // "todas" usa la URL base sin filtro

  const ordenes = await apiFetch(url);

  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <h1>Órdenes</h1>
        <div class="muted">${escapeHtml(state.tecnico.nombre)} ${escapeHtml(state.tecnico.apellido)}</div>
      </div>
      <button class="button secondary" id="logout-button">Salir</button>
    </div>
    <div class="tabs">
      <a class="tab ${state.tab === "pendientes"  ? "active" : ""}" href="#ordenes?tab=pendientes">Pendientes</a>
      <a class="tab ${state.tab === "mis"         ? "active" : ""}" href="#ordenes?tab=mis">Mis órdenes</a>
      <a class="tab ${state.tab === "todas"       ? "active" : ""}" href="#ordenes?tab=todas">Todas</a>
      <a class="tab ${state.tab === "completadas" ? "active" : ""}" href="#ordenes?tab=completadas">Completadas</a>
    </div>
    <div class="list">
      ${ordenes.length ? ordenes.map(ordenCard).join("") : '<div class="panel empty">No hay órdenes para mostrar.</div>'}
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
  const colaboradores = orden.colaboradores ?? [];
  const miId = Number(state.tecnico.id);
  const yaColabora = colaboradores.some((c) => Number(c.id) === miId);
  const ordenAbierta = ["PENDIENTE", "EN_PROGRESO"].includes(orden.estado);
  const puedeAceptar = ordenAbierta && !yaColabora;
  const asignadaAMi = Number(orden.tecnico_id) === miId || yaColabora;
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
    ${orden.estado !== "PENDIENTE" ? `
    <div class="panel">
      <div class="section-title">Técnicos que trabajaron en esta orden</div>
      ${colaboradores.length > 0
        ? colaboradores.map((c, i) => `
            <div class="colaborador-row">
              ${i === 0 ? '<span class="badge pendiente">Principal</span>' : '<span class="badge en-progreso">Colaborador</span>'}
              <span>${escapeHtml(c.nombre)} ${escapeHtml(c.apellido)}</span>
            </div>`).join("")
        : orden.tecnico_nombre
          ? `<div class="colaborador-row"><span class="badge pendiente">Principal</span> <span>${escapeHtml(orden.tecnico_nombre)}</span></div>`
          : '<div class="muted">Sin técnicos asignados.</div>'
      }
    </div>` : ""}
    <div class="panel">
      <div class="section-title">Observaciones</div>
      <div class="prewrap">${escapeHtml(orden.observaciones || "Sin observaciones.")}</div>
    </div>
    <div class="panel">
      <div class="section-title">Repuestos utilizados</div>
      ${orden.repuestos.length ? orden.repuestos.map((item) => `
        <div class="card">
          <h4>${escapeHtml(item.descripcion)}</h4>
          <div class="meta"><span>Cantidad: ${item.cantidad}</span></div>
        </div>
      `).join("") : '<div class="muted">Sin repuestos.</div>'}
      ${puedeTrabajar ? `<button class="button secondary" id="agregar-repuesto-btn" style="margin-top:8px">+ Agregar repuesto</button>` : ""}
      <div id="repuesto-form-container"></div>
    </div>
    <div class="panel">
      <div class="section-title">Programas vinculados</div>
      ${orden.programas.length ? orden.programas.map(programaMarkup).join("") : '<div class="muted">Sin programas vinculados.</div>'}
    </div>
    ${puedeAceptar ? `
      <div class="panel">
        <button class="button success" id="accept-button">
          ${orden.estado === "PENDIENTE" ? "Aceptar orden" : "Unirme como colaborador"}
        </button>
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

  // Helper: recarga la pantalla actual sin cambiar la URL
  async function refresh() {
    await renderOrdenDetalle(ordenId);
  }

  const acceptButton = document.querySelector("#accept-button");
  if (acceptButton) {
    acceptButton.addEventListener("click", async () => {
      if (!window.confirm("¿Confirmar que vas a realizar esta orden?")) return;
      acceptButton.disabled = true;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/aceptar`, { method: "POST" });
        await refresh();
      } catch (error) {
        window.alert(error.message);
        acceptButton.disabled = false;
      }
    });
  }

  const noteForm = document.querySelector("#note-form");
  if (noteForm) {
    noteForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const texto = noteForm.nota.value.trim();
      if (!texto) return;
      const btn = noteForm.querySelector("[type=submit]");
      btn.disabled = true;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/observaciones`, {
          method: "POST",
          body: JSON.stringify({ texto }),
        });
        await refresh();
      } catch (error) {
        window.alert(error.message);
        btn.disabled = false;
      }
    });
  }

  const agregarRepuestoBtn = document.querySelector("#agregar-repuesto-btn");
  if (agregarRepuestoBtn) {
    agregarRepuestoBtn.addEventListener("click", async () => {
      agregarRepuestoBtn.disabled = true;
      const container = document.querySelector("#repuesto-form-container");
      try {
        const repuestos = await apiFetch("/api/repuestos");
        container.innerHTML = `
          <form id="rep-form" style="margin-top:10px">
            <div class="field">
              <label>Repuesto</label>
              <select id="rep-select" required>
                <option value="">Seleccionar...</option>
                ${repuestos.map((r) => `<option value="${r.id}" data-stock="${r.stock_actual}">${escapeHtml(r.nombre)} (stock: ${r.stock_actual})</option>`).join("")}
              </select>
            </div>
            <div class="field">
              <label>Cantidad</label>
              <input id="rep-cant" type="number" min="0.001" step="0.001" value="1" required />
            </div>
            <div class="button-row">
              <button type="button" class="button secondary" id="rep-cancel">Cancelar</button>
              <button type="submit" class="button primary">Agregar</button>
            </div>
          </form>`;
        document.querySelector("#rep-cancel").addEventListener("click", () => {
          container.innerHTML = "";
          agregarRepuestoBtn.disabled = false;
        });
        document.querySelector("#rep-form").addEventListener("submit", async (e) => {
          e.preventDefault();
          const repuesto_id = Number(document.querySelector("#rep-select").value);
          const cantidad = Number(document.querySelector("#rep-cant").value);
          if (!repuesto_id || cantidad <= 0) return;
          const submitBtn = e.currentTarget.querySelector("[type=submit]");
          submitBtn.disabled = true;
          submitBtn.textContent = "Agregando...";
          try {
            await apiFetch(`/api/ordenes/${ordenId}/repuestos`, {
              method: "POST",
              body: JSON.stringify({ repuesto_id, cantidad }),
            });
            await refresh();
          } catch (error) {
            window.alert(error.message);
            submitBtn.disabled = false;
            submitBtn.textContent = "Agregar";
          }
        });
      } catch (error) {
        window.alert(error.message);
        agregarRepuestoBtn.disabled = false;
      }
    });
  }

  const completeButton = document.querySelector("#complete-button");
  if (completeButton) {
    completeButton.addEventListener("click", async () => {
      const observaciones = document.querySelector("#nota").value.trim();
      if (!window.confirm("¿Confirmar que la orden quedó completada?")) return;
      completeButton.disabled = true;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/completar`, {
          method: "POST",
          body: JSON.stringify({ observaciones }),
        });
        // Después de completar sí navegamos a la lista
        state.tab = "completadas";
        location.hash = "#ordenes?tab=completadas";
      } catch (error) {
        window.alert(error.message);
        completeButton.disabled = false;
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
  const [equipo, historial] = await Promise.all([
    apiFetch(`/api/equipos/${equipoId}`),
    apiFetch(`/api/equipos/${equipoId}/historial`),
  ]);
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
      <div class="section-title">Programas de mantenimiento</div>
      ${equipo.programas.length ? equipo.programas.map(programaMarkup).join("") : '<div class="muted">Sin programas activos.</div>'}
    </div>
    <div class="panel">
      <div class="section-title">Historial de mantenimiento</div>
      ${historial.length ? historial.map((h) => `
        <div class="card">
          <div class="card-header-row">
            <span class="badge ${badgeClass(h.estado)}">${escapeHtml(h.estado)}</span>
            <span class="meta">${escapeHtml(h.fecha_cierre || h.fecha_apertura)}</span>
          </div>
          <h4>${escapeHtml(h.tipo)} — ${escapeHtml(h.descripcion || "Sin descripción")}</h4>
          ${h.colaboradores.length
            ? `<div class="muted">${h.colaboradores.map(escapeHtml).join(", ")}</div>`
            : h.tecnico_nombre ? `<div class="muted">${escapeHtml(h.tecnico_nombre)}</div>` : ""}
          ${h.observaciones
            ? `<details><summary class="muted">Ver observaciones</summary><div class="prewrap" style="margin-top:6px">${escapeHtml(h.observaciones)}</div></details>`
            : ""}
        </div>`).join("")
      : '<div class="muted">Sin historial registrado.</div>'}
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

async function renderNuevaOrden() {
  renderLoading("Cargando equipos...");
  const equipos = await apiFetch("/api/equipos");
  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <a class="back-link" href="#ordenes">← Volver</a>
        <h2>Nueva orden de trabajo</h2>
      </div>
    </div>
    <div class="panel">
      <form id="nueva-orden-form">
        <div class="field">
          <label for="equipo">Equipo *</label>
          <select id="equipo" name="equipo_id" required>
            <option value="">Seleccionar equipo...</option>
            ${equipos.map((e) => `<option value="${e.id}">${escapeHtml(e.nombre)} — ${escapeHtml(e.ubicacion)}</option>`).join("")}
          </select>
        </div>
        <div class="field">
          <label for="tipo">Tipo *</label>
          <select id="tipo" name="tipo" required>
            <option value="CORRECTIVO">Correctivo</option>
            <option value="PREVENTIVO">Preventivo</option>
            <option value="MEJORA">Mejora</option>
          </select>
        </div>
        <div class="field">
          <label for="descripcion">Descripción</label>
          <textarea id="descripcion" name="descripcion" rows="3" placeholder="Descripción del problema o tarea..."></textarea>
        </div>
        <div class="field">
          <label for="observaciones">Observaciones</label>
          <textarea id="observaciones" name="observaciones" rows="2" placeholder="Observaciones adicionales..."></textarea>
        </div>
        <div class="button-row">
          <a class="button secondary" href="#ordenes">Cancelar</a>
          <button class="button primary" type="submit">Crear orden</button>
        </div>
        <p id="form-error" class="error" style="display:none"></p>
      </form>
    </div>
  `, "ordenes");

  document.querySelector("#nueva-orden-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const errorEl = document.querySelector("#form-error");
    errorEl.style.display = "none";
    const submitBtn = form.querySelector("[type=submit]");
    submitBtn.disabled = true;
    submitBtn.textContent = "Creando...";
    try {
      const orden = await apiFetch("/api/ordenes", {
        method: "POST",
        body: JSON.stringify({
          equipo_id: Number(form.equipo_id.value),
          tipo: form.tipo.value,
          descripcion: form.descripcion.value.trim(),
          observaciones: form.observaciones.value.trim(),
        }),
      });
      location.hash = `#orden/${orden.id}`;
    } catch (error) {
      errorEl.textContent = error.message;
      errorEl.style.display = "block";
      submitBtn.disabled = false;
      submitBtn.textContent = "Crear orden";
    }
  });
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const payload = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ legajo: form.legajo.value.trim(), password: form.password.value }),
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
  if (path === "nueva-orden") {
    await renderNuevaOrden();
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
