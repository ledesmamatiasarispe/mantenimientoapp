const state = {
  token: localStorage.getItem("gm_token") || "",
  tecnico: JSON.parse(localStorage.getItem("gm_tecnico") || "null"),
  serverBase: localStorage.getItem("gm_server") || "",
  tab: "pendientes",
  cronogramaAnio: new Date().getFullYear(),
  adminProgramaEquipoId: null,
  adjuntoViewer: null,
  cronogramaEquipoId: null,
  alertasCount: 0,
};

function setServerBase(url) {
  state.serverBase = url.replace(/\/+$/, "");
  localStorage.setItem("gm_server", state.serverBase);
}

async function pingServer(base) {
  const url = (base === undefined ? state.serverBase : base);
  try {
    const r = await fetch(url + "/api/health", {
      signal: AbortSignal.timeout ? AbortSignal.timeout(4000) : undefined,
    });
    return r.ok;
  } catch {
    return false;
  }
}

function serverConfigView(error = "", testing = false) {
  const cached = getNetworkInfo();
  const ipButtons = cached && cached.ips && cached.ips.length > 0
    ? `<p style="font-size:12px;color:#666;margin:8px 0 4px">IPs del servidor (última conexión exitosa):</p>
       ${cached.ips.map(entry => `
         <button type="button" class="button secondary ip-quick"
           data-url="http://${entry.ip}:${cached.port}"
           style="width:100%;text-align:left;margin-bottom:6px;font-size:12px;padding:6px 10px">
           <strong>${escapeHtml(entry.label)}</strong> — http://${entry.ip}:${cached.port}
         </button>`).join("")}`
    : `<p style="font-size:12px;color:#999;margin-top:8px">
         Conectate una vez para que el servidor informe sus IPs automáticamente.
       </p>`;

  return `
    <div class="login-shell">
      <form class="login-card" id="server-form">
        <h1 class="title">Gestión de Mantenimiento</h1>
        <p class="subtitle">No se pudo conectar al servidor. Ingresá la dirección IP.</p>
        <div class="field">
          <label for="server-url">URL del servidor</label>
          <input id="server-url" name="server-url" type="text"
            placeholder="http://192.168.100.228:54321"
            value="${escapeHtml(state.serverBase)}" required />
        </div>
        ${ipButtons}
        <button class="button primary" type="submit" ${testing ? "disabled" : ""}
          style="width:100%;margin-top:12px">
          ${testing ? "Conectando…" : "Conectar"}
        </button>
        ${error ? `<p class="error">${escapeHtml(error)}</p>` : ""}
      </form>
    </div>
  `;
}

function showServerConfig(error = "") {
  document.querySelector("#app").innerHTML = serverConfigView(error);

  // Botones de IP rápida
  document.querySelectorAll(".ip-quick").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelector("#server-url").value = btn.dataset.url;
    });
  });

  document.querySelector("#server-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = document.querySelector("#server-url").value.trim().replace(/\/+$/, "");
    document.querySelector("#app").innerHTML = serverConfigView("", true);
    const ok = await pingServer(url);
    if (ok) {
      setServerBase(url);
      render().catch((err) => showServerConfig(err.message));
    } else {
      showServerConfig(`No se pudo conectar a "${url}". Verificá la IP y que el servidor esté corriendo.`);
    }
  });
}

async function fetchNetworkInfo() {
  try {
    const info = await apiFetch("/api/network-info");
    state.serverNetworkInfo = info;
    localStorage.setItem("gm_network_info", JSON.stringify(info));
  } catch (_) { /* no crítico */ }
}

function getNetworkInfo() {
  if (state.serverNetworkInfo) return state.serverNetworkInfo;
  try {
    return JSON.parse(localStorage.getItem("gm_network_info") || "null");
  } catch { return null; }
}

function setAuth(token, tecnico) {
  state.token = token;
  state.tecnico = tecnico;
  localStorage.setItem("gm_token", token);
  localStorage.setItem("gm_tecnico", JSON.stringify(tecnico));
  fetchNetworkInfo(); // cargar IPs en background tras el login
  refreshAlertasBadge(); // badge de alertas
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
  const response = await fetch(state.serverBase + path, { ...options, headers });
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

async function fetchBlobAutenticado(url) {
  const fullUrl = url.startsWith("http") ? url : state.serverBase + url;
  const response = await fetch(fullUrl, {
    headers: state.token ? { Authorization: `Bearer ${state.token}` } : {},
  });
  if (!response.ok) throw new Error("No se pudo cargar la foto.");
  return URL.createObjectURL(await response.blob());
}

async function openFotoAutenticada(url) {
  const win = window.open("", "_blank");
  if (!win) { window.alert("El navegador bloqueó la ventana emergente. Permitir popups para este sitio."); return; }
  try {
    win.location.href = await fetchBlobAutenticado(url);
  } catch (e) {
    win.close();
    window.alert(e.message);
  }
}

async function cargarMiniaturas() {
  const imgs = document.querySelectorAll("img[data-src]");
  await Promise.all([...imgs].map(async (img) => {
    try {
      img.src = await fetchBlobAutenticado(img.dataset.src);
    } catch { /* deja la imagen rota silenciosamente */ }
  }));
}

function abrirAdjunto(url, nombre, backPath) {
  state.adjuntoViewer = { url, nombre, backPath };
  navigate("/adjunto");
}

async function renderAdjunto() {
  const viewer = state.adjuntoViewer;
  if (!viewer) { navigate("/ordenes"); return; }
  renderLoading("Cargando adjunto...");
  try {
    const blobUrl = await fetchBlobAutenticado(viewer.url);
    const nombre = viewer.nombre || "adjunto";
    const isImage = /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(nombre);
    const isPdf   = /\.pdf$/i.test(nombre);
    const navActive = viewer.backPath.startsWith("/admin") ? "admin" : "ordenes";

    document.querySelector("#app").innerHTML = layout(`
      <div class="topbar">
        <div>
          <a class="back-link" href="${viewer.backPath}">← Volver</a>
          <h2>${escapeHtml(nombre)}</h2>
        </div>
        <a href="${blobUrl}" download="${escapeHtml(nombre)}" class="button secondary" style="align-self:flex-end;white-space:nowrap">⬇ Descargar</a>
      </div>
      <div class="panel" style="padding:0;overflow:hidden;background:#000">
        ${isImage
          ? `<img src="${blobUrl}" style="width:100%;display:block;object-fit:contain;max-height:80vh" />`
          : isPdf
          ? `<iframe src="${blobUrl}" style="width:100%;height:78vh;border:none;background:#fff"></iframe>`
          : `<div style="padding:24px;text-align:center">
               <a href="${blobUrl}" download="${escapeHtml(nombre)}" class="button primary">⬇ Descargar ${escapeHtml(nombre)}</a>
             </div>`}
      </div>
    `, navActive);

    window.addEventListener("popstate", () => URL.revokeObjectURL(blobUrl), { once: true });
  } catch (e) {
    document.querySelector("#app").innerHTML = layout(
      `<div class="panel"><div class="muted">Error al cargar el adjunto: ${escapeHtml(e.message)}</div></div>`
    );
  }
}

function layout(content, active = "ordenes") {
  return `
    <div class="app-shell">${content}</div>
    <nav class="bottom-nav">
      <a class="nav-link ${active === "ordenes" ? "active" : ""}" href="/ordenes">Órdenes</a>
      <a class="nav-link ${active === "cronograma" ? "active" : ""}" href="/cronograma">Cronograma</a>
      ${state.tecnico?.es_admin ? `<a class="nav-link ${active === "admin" ? "active" : ""}" href="/admin/dashboard">Admin ${state.alertasCount > 0 ? `<span class="badge">${state.alertasCount}</span>` : ""}</a>` : ""}
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
  const nro = `Orden Nº ${String(orden.id).padStart(4, "0")}`;
  return `
    <a class="card" href="/orden/${orden.id}">
      <div class="card-header-row">
        <span class="muted" style="font-size:12px">${nro}</span>
        <span class="tecnico-tag">${escapeHtml(orden.equipo_nombre)}${tecnico}</span>
      </div>
      <div class="meta" style="margin-top:4px">
        <div class="badge ${badgeClass(orden.estado)}">${escapeHtml(orden.estado)}</div>
        <span>${escapeHtml(orden.tipo)} · ${escapeHtml(orden.equipo_tipo_nombre)}</span>
      </div>
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
      <div style="display:flex;gap:8px;align-items:center">
        <a class="button primary" href="/nueva-orden">+ Nueva</a>
        <button class="button secondary" id="logout-button">Salir</button>
      </div>
    </div>
    <div class="tabs">
      <a class="tab ${state.tab === "pendientes"  ? "active" : ""}" href="/ordenes?tab=pendientes">Pendientes</a>
      <a class="tab ${state.tab === "mis"         ? "active" : ""}" href="/ordenes?tab=mis">Mis órdenes</a>
      <a class="tab ${state.tab === "todas"       ? "active" : ""}" href="/ordenes?tab=todas">Todas</a>
      <a class="tab ${state.tab === "completadas" ? "active" : ""}" href="/ordenes?tab=completadas">Completadas</a>
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

function programaMarkup(programa, { ordenId = null, puedeTogglear = false } = {}) {
  const pasos = programa.pasos ?? [];
  const completados = pasos.filter((p) => p.completado).length;
  const pasosHtml = pasos.length
    ? `<div class="pasos-lista">
        <div class="pasos-progreso muted">${completados}/${pasos.length} pasos completados</div>
        ${pasos.map((paso) => `
          <div class="paso-fila">
            <label class="paso-item ${paso.completado ? "completado" : ""}">
              <input type="checkbox" class="paso-check" data-paso-id="${paso.id}" data-orden-id="${ordenId ?? ""}"
                ${paso.completado ? "checked" : ""} ${puedeTogglear ? "" : "disabled"} />
              <span>${escapeHtml(paso.descripcion)}</span>
            </label>
            <button class="btn-icon paso-info-btn" data-paso-id="${paso.id}" title="Ver detalle">ℹ️</button>
          </div>
          <div class="paso-detalle" id="paso-det-${paso.id}" style="display:none">
            <div class="paso-detalle-titulo">${paso.posicion}. ${escapeHtml(paso.descripcion)}</div>
            ${paso.observaciones ? `<div style="font-size:13px;margin:2px 0">${escapeHtml(paso.observaciones)}</div>` : ""}
            ${paso.adjunto_nombre
              ? `<a href="#" class="paso-adjunto-link" data-url="/api/pasos/${paso.id}/adjunto" data-nombre="${escapeHtml(paso.adjunto_nombre)}" data-back="/orden/${ordenId ?? ""}">📎 ${escapeHtml(paso.adjunto_nombre)}</a>`
              : `<span class="muted">Sin adjunto</span>`}
          </div>
        `).join("")}
      </div>`
    : "";

  return `
    <div class="card">
      <h4>${escapeHtml(programa.descripcion)}</h4>
      <div class="meta">
        <span>Cada ${programa.frecuencia_meses} meses</span>
        <span>Próxima: ${escapeHtml(programa.proxima_ejecucion)}</span>
      </div>
      ${pasosHtml}
      ${programa.adjuntos.length ? `
        <div class="meta" style="margin-top:6px">
          ${programa.adjuntos.map((adjunto) => `<span>${escapeHtml(adjunto.tipo)} · ${escapeHtml(adjunto.nombre)}</span>`).join("")}
        </div>
      ` : ""}
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
  const puedeCancelarAceptacion = ordenAbierta && yaColabora;
  const asignadaAMi = Number(orden.tecnico_id) === miId || yaColabora;
  const puedeTrabajar = orden.estado === "EN_PROGRESO" && asignadaAMi;
  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <a class="back-link" href="/ordenes">← Volver</a>
        <h2>${escapeHtml(orden.equipo_nombre)}</h2>
      </div>
      <div style="text-align:right;align-self:flex-end;padding-bottom:2px">
        <span class="muted" style="font-size:13px">Orden Nº ${String(ordenId).padStart(4, "0")}</span>
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
    ${state.tecnico?.es_admin ? `
    <div class="panel">
      <div class="section-title">Observaciones</div>
      <div class="prewrap">${escapeHtml(orden.observaciones || "Sin observaciones.")}</div>
    </div>` : ""}
    <div class="panel">
      <div class="section-title">Repuestos utilizados</div>
      ${orden.repuestos.length ? orden.repuestos.map((item) => `
        <div class="card" style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <h4 style="margin:0">${escapeHtml(item.descripcion)}</h4>
            <div class="meta"><span>Cantidad: ${item.cantidad}</span></div>
          </div>
          ${!["COMPLETADA","CANCELADA"].includes(orden.estado)
            ? `<button class="button secondary quitar-rep-btn" data-item-id="${item.id}" style="min-width:36px;padding:0 10px">✕</button>`
            : ""}
        </div>
      `).join("") : '<div class="muted">Sin repuestos.</div>'}
      ${puedeTrabajar ? `<button class="button secondary" id="agregar-repuesto-btn" style="margin-top:8px">+ Agregar repuesto</button>` : ""}
      <div id="repuesto-form-container"></div>
    </div>
    <div class="panel">
      <div class="section-title">Programas vinculados</div>
      ${orden.programas.length
        ? orden.programas.map((p) => programaMarkup(p, { ordenId, puedeTogglear: puedeTrabajar })).join("")
        : '<div class="muted">Sin programas vinculados.</div>'}
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
        <div class="section-title">Fotos</div>
        <div id="fotos-lista">
          ${(orden.fotos ?? []).map((f) => `
            <div class="foto-item">
              <a class="foto-thumb" href="#" data-foto-url="/api/ordenes/${ordenId}/fotos/${f.id}" data-nombre="${escapeHtml(f.nombre)}" data-back="/orden/${ordenId}">
                <img data-src="/api/ordenes/${ordenId}/fotos/${f.id}" alt="${escapeHtml(f.nombre)}" style="background:#f3f4f6" />
                <span class="muted">${escapeHtml(f.nombre)}</span>
              </a>
              <button class="btn-icon eliminar-foto-btn" data-foto-id="${f.id}" title="Eliminar foto" style="color:#dc2626;font-size:18px">🗑️</button>
            </div>
          `).join("") || '<span class="muted">Sin fotos.</span>'}
        </div>
        <label class="button secondary" style="margin-top:8px;cursor:pointer;display:inline-block">
          📷 Agregar foto
          <input type="file" id="foto-input" accept="image/*" capture="environment" style="display:none" />
        </label>
        <div id="foto-upload-status"></div>
        <div style="margin-top:14px">
          <div class="field">
            <label for="nota">Observación al completar</label>
            <textarea id="nota" name="nota"></textarea>
          </div>
          <div class="button-row">
            <button class="button success" id="complete-button">Marcar completada</button>
            ${puedeCancelarAceptacion ? `<button class="button danger" id="cancel-accept-button">Salir de orden</button>` : ""}
          </div>
        </div>
      </div>
    ` : ""}
  `, "ordenes");

  // Cargar miniaturas de fotos con auth
  cargarMiniaturas();

  // Detalle de paso (toggle)
  document.querySelectorAll(".paso-info-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const det = document.querySelector(`#paso-det-${btn.dataset.pasoId}`);
      if (det) det.style.display = det.style.display === "none" ? "block" : "none";
    });
  });
  document.querySelectorAll(".paso-adjunto-link").forEach(a => {
    a.addEventListener("click", e => {
      e.preventDefault();
      abrirAdjunto(a.dataset.url, a.dataset.nombre, a.dataset.back || "/ordenes");
    });
  });

  // Links de fotos — abrir visor
  document.querySelectorAll("[data-foto-url]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      abrirAdjunto(a.dataset.fotoUrl, a.dataset.nombre, a.dataset.back || `#orden/${ordenId}`);
    });
  });

  // Eliminar foto
  document.querySelectorAll(".eliminar-foto-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!window.confirm("¿Eliminar esta foto?")) return;
      btn.disabled = true;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/fotos/${btn.dataset.fotoId}`, { method: "DELETE" });
        await refresh();
      } catch (err) {
        window.alert(err.message);
        btn.disabled = false;
      }
    });
  });

  // Botones quitar repuesto (✕)
  document.querySelectorAll(".quitar-rep-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!window.confirm("¿Quitar este repuesto? Se restaurará el stock.")) return;
      btn.disabled = true;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/repuestos/${btn.dataset.itemId}`, { method: "DELETE" });
        await refresh();
      } catch (error) {
        window.alert(error.message);
        btn.disabled = false;
      }
    });
  });

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

  const cancelAcceptButton = document.querySelector("#cancel-accept-button");
  if (cancelAcceptButton) {
    cancelAcceptButton.addEventListener("click", async () => {
      if (!window.confirm("¿Está seguro que quiere salir de la orden? La orden volverá a estar en Pendiente.")) return;
      cancelAcceptButton.disabled = true;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/cancelar-aceptacion`, { method: "POST" });
        await refresh();
      } catch (error) {
        window.alert(error.message);
        cancelAcceptButton.disabled = false;
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
        state.tab = "completadas";
        navigate("/ordenes?tab=completadas");
      } catch (error) {
        window.alert(error.message);
        completeButton.disabled = false;
      }
    });
  }

  // Foto upload
  const fotoInput = document.querySelector("#foto-input");
  if (fotoInput) {
    fotoInput.addEventListener("change", async () => {
      const file = fotoInput.files[0];
      if (!file) return;
      const status = document.querySelector("#foto-upload-status");
      status.textContent = "Subiendo foto...";
      const formData = new FormData();
      formData.append("foto", file);
      try {
        const headers = {};
        if (state.token) headers.Authorization = `Bearer ${state.token}`;
        const response = await fetch(`/api/ordenes/${ordenId}/fotos`, {
          method: "POST",
          headers,
          body: formData,
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({ detail: "Error inesperado." }));
          throw new Error(String(payload.detail || "Error al subir foto."));
        }
        status.textContent = "";
        await refresh();
      } catch (error) {
        status.textContent = error.message;
        window.alert(error.message);
      }
    });
  }

  // Paso toggle
  document.querySelectorAll(".paso-check").forEach((checkbox) => {
    checkbox.addEventListener("change", async () => {
      const pasoId = checkbox.dataset.pasoId;
      checkbox.disabled = true;
      try {
        await apiFetch(`/api/ordenes/${ordenId}/pasos/${pasoId}/toggle`, { method: "POST" });
        await refresh();
      } catch (error) {
        window.alert(error.message);
        checkbox.checked = !checkbox.checked;
        checkbox.disabled = false;
      }
    });
  });
}


async function renderNuevaOrden() {
  renderLoading("Cargando equipos...");
  const equipos = await apiFetch("/api/equipos");
  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div>
        <a class="back-link" href="/ordenes">← Volver</a>
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
          <a class="button secondary" href="/ordenes">Cancelar</a>
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
      navigate(`/orden/${orden.id}`);
    } catch (error) {
      errorEl.textContent = error.message;
      errorEl.style.display = "block";
      submitBtn.disabled = false;
      submitBtn.textContent = "Crear orden";
    }
  });
}

const _MESES_CORTOS = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];

async function renderCronograma() {
  renderLoading("Cargando cronograma...");
  const anioActual = new Date().getFullYear();
  const anio = state.cronogramaAnio ?? anioActual;

  const filas = await apiFetch(`/api/cronograma?anio=${anio}`);
  const mesHoy = new Date().getMonth() + 1;

  // Equipos únicos de las filas para el filtro
  const equiposMap = new Map();
  filas.forEach(f => { if (!equiposMap.has(f.equipo_id)) equiposMap.set(f.equipo_id, f.equipo_nombre); });
  const equiposOpts = [`<option value="">— Todos los equipos —</option>`,
    ...[...equiposMap.entries()].map(([id, nombre]) =>
      `<option value="${id}" ${state.cronogramaEquipoId === id ? "selected" : ""}>${escapeHtml(nombre)}</option>`)
  ].join("");

  const filasFiltradas = state.cronogramaEquipoId
    ? filas.filter(f => f.equipo_id === state.cronogramaEquipoId)
    : filas;

  const optsAnio = [];
  for (let y = anioActual - 2; y <= anioActual + 4; y++) {
    optsAnio.push(`<option value="${y}" ${y === anio ? "selected" : ""}>${y}</option>`);
  }

  const headerCols = _MESES_CORTOS.map((m, i) => `<th class="${i + 1 === mesHoy && anio === anioActual ? "mes-hoy" : ""}">${m}</th>`).join("");

  const bodyRows = filasFiltradas.map((fila) => {
    const celdas = _MESES_CORTOS.map((_, i) => {
      const mes = i + 1;
      const estado = fila.meses[String(mes)];
      const esHoy = mes === mesHoy && anio === anioActual;
      if (estado === "completada") return `<td class="crono-completada ${esHoy ? "crono-hoy" : ""}">✔</td>`;
      if (estado === "activa")     return `<td class="crono-activa ${esHoy ? "crono-hoy" : ""}">⏳</td>`;
      if (estado === "planned")    return `<td class="crono-planned ${esHoy ? "crono-hoy" : ""}">·</td>`;
      return `<td class="${esHoy ? "crono-hoy" : ""}"></td>`;
    }).join("");
    return `<tr><td class="crono-label">${escapeHtml(fila.etiqueta)}</td>${celdas}</tr>`;
  }).join("");

  document.querySelector("#app").innerHTML = layout(`
    <div class="topbar">
      <div><h1>Cronograma</h1></div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <select id="crono-equipo" style="font-size:13px;padding:4px 6px;border:1px solid var(--border);border-radius:6px">${equiposOpts}</select>
        <select id="crono-anio" class="crono-anio-select">${optsAnio.join("")}</select>
      </div>
    </div>
    <div class="crono-leyenda">
      <span class="crono-dot crono-planned">·</span> Planificado
      <span class="crono-dot crono-activa">⏳</span> Abierta
      <span class="crono-dot crono-completada">✔</span> Completada
    </div>
    <div class="crono-scroll">
      <table class="crono-table">
        <thead><tr><th class="crono-label-header">Mantenimiento</th>${headerCols}</tr></thead>
        <tbody>${bodyRows || `<tr><td colspan="13" class="muted" style="padding:12px">Sin programas para este equipo.</td></tr>`}</tbody>
      </table>
    </div>
  `, "cronograma");

  document.querySelector("#crono-anio").addEventListener("change", (e) => {
    state.cronogramaAnio = Number(e.target.value);
    renderCronograma();
  });

  document.querySelector("#crono-equipo").addEventListener("change", (e) => {
    state.cronogramaEquipoId = Number(e.target.value) || null;
    renderCronograma();
  });
}

// ── Admin ──────────────────────────────────────────────────────────────────

const ADMIN_SECTIONS = [
  { key: "dashboard",   label: "🏠 Inicio" },
  { key: "alertas",     label: "🔔 Alertas" },
  { key: "equipos",     label: "Equipos" },
  { key: "tipos",       label: "Tipos" },
  { key: "programas",   label: "Programas" },
  { key: "repuestos",   label: "Repuestos" },
  { key: "tecnicos",    label: "Técnicos" },
  { key: "ordenes",     label: "Órdenes" },
  { key: "generar",     label: "📅 Generar" },
  { key: "electricidad",label: "⚡ Electr." },
  { key: "base-datos",  label: "💾 DB" },
];

function adminTabs(active) {
  return `<div class="tabs" style="grid-template-columns:repeat(${ADMIN_SECTIONS.length},1fr)">
    ${ADMIN_SECTIONS.map(s => `<a class="tab ${active === s.key ? "active" : ""}" href="/admin/${s.key}">${s.label}</a>`).join("")}
  </div>`;
}

function layoutAdmin(section, content) {
  return layout(`
    <div class="topbar"><div><h1>Administración</h1></div></div>
    ${adminTabs(section)}
    ${content}
  `, "admin");
}

async function renderAdminList(section) {
  renderLoading("Cargando...");
  const apiSection = section === "tipos" ? "tipos-equipo" : section;

  let items, equiposFiltro = [];
  if (section === "programas") {
    [items, equiposFiltro] = await Promise.all([
      apiFetch("/api/admin/programas"),
      apiFetch("/api/admin/equipos"),
    ]);
  } else {
    items = await apiFetch(`/api/admin/${apiSection}`);
  }

  let tableHead = "";
  let tableRows = "";
  let title = ADMIN_SECTIONS.find(s => s.key === section)?.label ?? section;
  let extraHeader = "";

  if (section === "equipos") {
    tableHead = `<tr><th>#</th><th>Nombre</th><th>Tipo</th><th>Ubicación</th><th>Activo</th><th></th></tr>`;
    tableRows = items.map(r => `<tr>
      <td class="muted">${r.id}</td><td>${escapeHtml(r.nombre)}</td><td>${escapeHtml(r.tipo_nombre)}</td>
      <td>${escapeHtml(r.ubicacion)}</td><td>${r.activo ? "✓" : "–"}</td>
      <td style="white-space:nowrap">
        <a class="btn-icon" href="/admin/equipos/${r.id}/historial" title="Historial">📋</a>
        <a class="btn-icon" href="/admin/equipos/${r.id}" title="Editar">✏️</a>
        <button class="btn-icon" data-delete="${r.id}" title="Eliminar">🗑️</button>
      </td></tr>`).join("");
  } else if (section === "tipos") {
    tableHead = `<tr><th>#</th><th>Nombre</th><th>Activo</th><th></th></tr>`;
    tableRows = items.map(r => `<tr>
      <td class="muted">${r.id}</td><td>${escapeHtml(r.nombre)}</td><td>${r.activo ? "✓" : "–"}</td>
      <td><a class="btn-icon" href="/admin/tipos/${r.id}" title="Editar">✏️</a>
          <button class="btn-icon" data-delete="${r.id}" title="Eliminar">🗑️</button></td></tr>`).join("");
  } else if (section === "programas") {
    const equipoOpts = equiposFiltro.map(e =>
      `<option value="${e.id}" ${state.adminProgramaEquipoId === e.id ? "selected" : ""}>${escapeHtml(e.nombre)}</option>`
    ).join("");
    extraHeader = `
      <div class="panel" style="padding:8px 14px">
        <select id="filtro-equipo" style="width:100%;padding:6px 8px;font-size:14px;border:1px solid var(--border);border-radius:6px">
          <option value="">— Todos los equipos —</option>
          ${equipoOpts}
        </select>
      </div>`;
    const filtered = state.adminProgramaEquipoId
      ? items.filter(r => r.equipo_id === state.adminProgramaEquipoId)
      : items;
    tableHead = `<tr><th>#</th><th>Descripción</th><th>Frec.</th><th>Próxima</th><th>Activo</th><th></th></tr>`;
    tableRows = filtered.map(r => `<tr>
      <td class="muted">${r.id}</td><td>${escapeHtml(r.descripcion)}</td>
      <td>${r.frecuencia_meses}m</td><td>${escapeHtml(r.proxima_ejecucion)}</td><td>${r.activo ? "✓" : "–"}</td>
      <td style="white-space:nowrap">
        <a class="btn-icon" href="/admin/programas/${r.id}/pasos" title="Pasos">📋</a>
        <a class="btn-icon" href="/admin/programas/${r.id}" title="Editar">✏️</a>
        <button class="btn-icon" data-delete="${r.id}" title="Eliminar">🗑️</button>
      </td></tr>`).join("");
  } else if (section === "repuestos") {
    tableHead = `<tr><th>#</th><th>Nombre</th><th>Stock</th><th>Mín.</th><th>Activo</th><th></th></tr>`;
    tableRows = items.map(r => `<tr>
      <td class="muted">${r.id}</td><td>${escapeHtml(r.nombre)}</td>
      <td>${r.stock_actual}</td><td>${r.stock_minimo}</td><td>${r.activo ? "✓" : "–"}</td>
      <td><a class="btn-icon" href="/admin/repuestos/${r.id}" title="Editar">✏️</a>
          <button class="btn-icon" data-delete="${r.id}" title="Eliminar">🗑️</button></td></tr>`).join("");
  } else if (section === "tecnicos") {
    tableHead = `<tr><th>#</th><th>Apellido</th><th>Nombre</th><th>Legajo</th><th>Activo</th><th></th></tr>`;
    tableRows = items.map(r => `<tr>
      <td class="muted">${r.id}</td><td>${escapeHtml(r.apellido)}</td><td>${escapeHtml(r.nombre)}</td>
      <td>${escapeHtml(r.legajo)}</td><td>${r.activo ? "✓" : "–"}</td>
      <td style="white-space:nowrap">
        <a class="btn-icon" href="/admin/tecnicos/${r.id}" title="Editar">✏️</a>
        <a class="btn-icon" href="/admin/tecnicos/${r.id}/password" title="Cambiar contraseña">🔑</a>
        <button class="btn-icon" data-delete="${r.id}" title="Eliminar">🗑️</button>
      </td></tr>`).join("");
  } else if (section === "ordenes") {
    tableHead = `<tr><th>#</th><th>Equipo</th><th>Tipo</th><th>Estado</th><th>Apertura</th><th></th></tr>`;
    tableRows = items.map(r => `<tr>
      <td class="muted">${r.id}</td><td>${escapeHtml(r.equipo_nombre)}</td><td>${escapeHtml(r.tipo)}</td>
      <td><span class="badge ${badgeClass(r.estado)}">${escapeHtml(r.estado)}</span></td>
      <td>${escapeHtml(r.fecha_apertura)}</td>
      <td style="white-space:nowrap">
        <a class="btn-icon" href="/admin/ordenes/${r.id}" title="Editar">✏️</a>
        <button class="btn-icon" data-delete="${r.id}" title="Eliminar">🗑️</button>
      </td></tr>`).join("");
  }

  document.querySelector("#app").innerHTML = layoutAdmin(section, `
    <div class="panel" style="padding:10px 14px;display:flex;justify-content:space-between;align-items:center">
      <strong>${title}</strong>
      <a class="button primary" href="/admin/${section}/nuevo" style="font-size:13px;padding:6px 14px">+ Nuevo</a>
    </div>
    ${extraHeader}
    <div class="crono-scroll">
      <table class="admin-table">
        <thead>${tableHead}</thead>
        <tbody>${tableRows || `<tr><td colspan="10" class="muted" style="padding:12px">Sin registros.</td></tr>`}</tbody>
      </table>
    </div>
  `);

  document.querySelectorAll("[data-delete]").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!window.confirm("¿Eliminar este registro?")) return;
      btn.disabled = true;
      try {
        const apiSec = section === "tipos" ? "tipos-equipo" : section;
        await apiFetch(`/api/admin/${apiSec}/${btn.dataset.delete}`, { method: "DELETE" });
        await renderAdminList(section);
      } catch (e) {
        window.alert(e.message);
        btn.disabled = false;
      }
    });
  });

  const filtroEquipo = document.querySelector("#filtro-equipo");
  if (filtroEquipo) {
    filtroEquipo.addEventListener("change", () => {
      state.adminProgramaEquipoId = Number(filtroEquipo.value) || null;
      renderAdminList("programas");
    });
  }
}

async function renderAdminForm(section, id) {
  renderLoading("Cargando...");
  const apiSection = section === "tipos" ? "tipos-equipo" : section;
  const isNew = id === null;

  let item = null;
  let extras = {};

  if (!isNew) {
    const list = await apiFetch(`/api/admin/${apiSection}`);
    item = list.find(x => x.id === id) ?? null;
  }

  if (section === "equipos" || section === "programas") {
    extras.tipos = await apiFetch("/api/admin/tipos-equipo");
    extras.equipos = await apiFetch("/api/admin/equipos");
  }
  if (section === "ordenes") {
    [extras.equipos, extras.tecnicos] = await Promise.all([
      apiFetch("/api/admin/equipos"),
      apiFetch("/api/admin/tecnicos"),
    ]);
  }

  let fields = "";
  if (section === "tipos") {
    fields = `
      <div class="field"><label>Nombre *</label><input name="nombre" value="${escapeHtml(item?.nombre ?? "")}" required /></div>
      <div class="field"><label><input type="checkbox" name="activo" ${item?.activo !== false ? "checked" : ""}> Activo</label></div>`;
  } else if (section === "equipos") {
    const tipoOpts = extras.tipos.map(t => `<option value="${t.id}" ${item?.tipo_id === t.id ? "selected" : ""}>${escapeHtml(t.nombre)}</option>`).join("");
    fields = `
      <div class="field"><label>Nombre *</label><input name="nombre" value="${escapeHtml(item?.nombre ?? "")}" required /></div>
      <div class="field"><label>Tipo</label><select name="tipo_id"><option value="">Sin tipo</option>${tipoOpts}</select></div>
      <div class="field"><label>Nº Serie</label><input name="numero_serie" value="${escapeHtml(item?.numero_serie ?? "")}" /></div>
      <div class="field"><label>Marca</label><input name="marca" value="${escapeHtml(item?.marca ?? "")}" /></div>
      <div class="field"><label>Modelo</label><input name="modelo" value="${escapeHtml(item?.modelo ?? "")}" /></div>
      <div class="field"><label>Ubicación</label><input name="ubicacion" value="${escapeHtml(item?.ubicacion ?? "")}" /></div>
      <div class="field"><label>Fecha adquisición</label><input name="fecha_adquisicion" type="date" value="${escapeHtml(item?.fecha_adquisicion ?? "")}" /></div>
      <div class="field"><label>Observaciones</label><textarea name="observaciones">${escapeHtml(item?.observaciones ?? "")}</textarea></div>
      <div class="field"><label><input type="checkbox" name="activo" ${item?.activo !== false ? "checked" : ""}> Activo</label></div>`;
  } else if (section === "programas") {
    const equipoOpts = extras.equipos.filter(e => e.activo || item?.equipo_id === e.id)
      .map(e => `<option value="${e.id}" ${item?.equipo_id === e.id ? "selected" : ""}>${escapeHtml(e.nombre)}</option>`).join("");
    fields = `
      <div class="field"><label>Equipo *</label><select name="equipo_id" required><option value="">Seleccionar...</option>${equipoOpts}</select></div>
      <div class="field"><label>Descripción *</label><input name="descripcion" value="${escapeHtml(item?.descripcion ?? "")}" required /></div>
      <div class="field"><label>Frecuencia (meses) *</label><input name="frecuencia_meses" type="number" min="1" max="120" value="${item?.frecuencia_meses ?? 1}" required /></div>
      <div class="field"><label>Última ejecución</label><input name="ultima_ejecucion" type="date" value="${escapeHtml(item?.ultima_ejecucion ?? "")}" /></div>
      <div class="field"><label><input type="checkbox" name="activo" ${item?.activo !== false ? "checked" : ""}> Activo</label></div>`;
  } else if (section === "repuestos") {
    fields = `
      <div class="field"><label>Nombre *</label><input name="nombre" value="${escapeHtml(item?.nombre ?? "")}" required /></div>
      <div class="field"><label>Observaciones</label><textarea name="observaciones">${escapeHtml(item?.observaciones ?? "")}</textarea></div>
      <div class="field"><label>Stock actual</label><input name="stock_actual" type="number" step="0.001" value="${item?.stock_actual ?? 0}" /></div>
      <div class="field"><label>Stock mínimo</label><input name="stock_minimo" type="number" step="0.001" value="${item?.stock_minimo ?? 0}" /></div>
      <div class="field"><label><input type="checkbox" name="activo" ${item?.activo !== false ? "checked" : ""}> Activo</label></div>`;
  } else if (section === "tecnicos") {
    fields = `
      <div class="field"><label>Nombre *</label><input name="nombre" value="${escapeHtml(item?.nombre ?? "")}" required /></div>
      <div class="field"><label>Apellido *</label><input name="apellido" value="${escapeHtml(item?.apellido ?? "")}" required /></div>
      <div class="field"><label>Legajo *</label><input name="legajo" value="${escapeHtml(item?.legajo ?? "")}" required /></div>
      <div class="field"><label>Teléfono</label><input name="telefono" value="${escapeHtml(item?.telefono ?? "")}" /></div>
      <div class="field"><label>Especialidad</label><input name="especialidad" value="${escapeHtml(item?.especialidad ?? "")}" /></div>
      ${isNew ? `<div class="field"><label>Contraseña *</label><input name="password" type="password" required /></div>` : ""}
      ${!isNew ? `<div class="field"><label><input type="checkbox" name="activo" ${item?.activo !== false ? "checked" : ""}> Activo</label></div>` : ""}`;
  } else if (section === "ordenes") {
    const equipoOpts = extras.equipos.filter(e => e.activo || item?.equipo_id === e.id)
      .map(e => `<option value="${e.id}" ${item?.equipo_id === e.id ? "selected" : ""}>${escapeHtml(e.nombre)}</option>`).join("");
    const tecnicoOpts = `<option value="">Sin asignar</option>` + extras.tecnicos.filter(t => t.activo || item?.tecnico_id === t.id)
      .map(t => `<option value="${t.id}" ${item?.tecnico_id === t.id ? "selected" : ""}>${escapeHtml(t.apellido)} ${escapeHtml(t.nombre)}</option>`).join("");
    const tipoOpts = ["PREVENTIVO","CORRECTIVO","MEJORA"].map(v => `<option ${item?.tipo === v ? "selected" : ""}>${v}</option>`).join("");
    const estadoOpts = ["PENDIENTE","EN_PROGRESO","COMPLETADA","CANCELADA"].map(v => `<option ${item?.estado === v ? "selected" : ""}>${v}</option>`).join("");
    fields = `
      <div class="field"><label>Equipo *</label><select name="equipo_id" required><option value="">Seleccionar...</option>${equipoOpts}</select></div>
      <div class="field"><label>Tipo</label><select name="tipo">${tipoOpts}</select></div>
      <div class="field"><label>Descripción</label><textarea name="descripcion">${escapeHtml(item?.descripcion ?? "")}</textarea></div>
      <div class="field"><label>Fecha apertura *</label><input name="fecha_apertura" type="date" value="${escapeHtml(item?.fecha_apertura ?? "")}" required /></div>
      <div class="field"><label>Fecha cierre</label><input name="fecha_cierre" type="date" value="${escapeHtml(item?.fecha_cierre ?? "")}" /></div>
      <div class="field"><label>Estado</label><select name="estado">${estadoOpts}</select></div>
      <div class="field"><label>Técnico asignado</label><select name="tecnico_id">${tecnicoOpts}</select></div>
      <div class="field"><label>Costo mano de obra</label><input name="costo_mano_obra" type="number" step="0.01" value="${item?.costo_mano_obra ?? 0}" /></div>
      <div class="field"><label>Observaciones</label><textarea name="observaciones">${escapeHtml(item?.observaciones ?? "")}</textarea></div>`;
  }

  const title = `${isNew ? "Nuevo" : "Editar"} — ${ADMIN_SECTIONS.find(s => s.key === section)?.label ?? section}`;
  document.querySelector("#app").innerHTML = layoutAdmin(section, `
    <div class="panel">
      <h3 style="margin:0 0 12px">${title}</h3>
      <form id="admin-form">
        ${fields}
        <div class="button-row" style="margin-top:12px">
          <a class="button secondary" href="/admin/${section}">Cancelar</a>
          <button class="button primary" type="submit">Guardar</button>
        </div>
      </form>
    </div>
  `);

  document.querySelector("#admin-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.currentTarget;
    const g = name => f.elements[name]?.value ?? "";
    const gNum = name => Number(f.elements[name]?.value ?? 0);
    const gBool = name => f.elements[name]?.checked ?? true;
    const gNullId = name => { const v = f.elements[name]?.value; return v ? Number(v) : null; };
    const btn = f.querySelector("[type=submit]");
    btn.disabled = true;

    try {
      let body = {};
      if (section === "tipos") {
        body = { nombre: g("nombre"), activo: gBool("activo") };
      } else if (section === "equipos") {
        body = { nombre: g("nombre"), tipo_id: gNullId("tipo_id"), numero_serie: g("numero_serie"),
                 marca: g("marca"), modelo: g("modelo"), ubicacion: g("ubicacion"),
                 fecha_adquisicion: g("fecha_adquisicion"), observaciones: g("observaciones"), activo: gBool("activo") };
      } else if (section === "programas") {
        body = { equipo_id: gNum("equipo_id"), descripcion: g("descripcion"),
                 frecuencia_meses: gNum("frecuencia_meses"), ultima_ejecucion: g("ultima_ejecucion"), activo: gBool("activo") };
      } else if (section === "repuestos") {
        body = { nombre: g("nombre"), observaciones: g("observaciones"),
                 stock_actual: gNum("stock_actual"), stock_minimo: gNum("stock_minimo"), activo: gBool("activo") };
      } else if (section === "tecnicos") {
        if (isNew) {
          body = { nombre: g("nombre"), apellido: g("apellido"), legajo: g("legajo"),
                   telefono: g("telefono"), especialidad: g("especialidad"), password: g("password") };
        } else {
          body = { nombre: g("nombre"), apellido: g("apellido"), legajo: g("legajo"),
                   telefono: g("telefono"), especialidad: g("especialidad"), activo: gBool("activo") };
        }
      } else if (section === "ordenes") {
        body = { equipo_id: gNum("equipo_id"), tipo: g("tipo"), descripcion: g("descripcion"),
                 fecha_apertura: g("fecha_apertura"), fecha_cierre: g("fecha_cierre"), estado: g("estado"),
                 tecnico_id: gNullId("tecnico_id"), costo_mano_obra: gNum("costo_mano_obra"), observaciones: g("observaciones") };
      }

      const apiSec = section === "tipos" ? "tipos-equipo" : section;
      if (isNew) {
        await apiFetch(`/api/admin/${apiSec}`, { method: "POST", body: JSON.stringify(body) });
      } else {
        await apiFetch(`/api/admin/${apiSec}/${id}`, { method: "PUT", body: JSON.stringify(body) });
      }
      navigate(`/admin/${section}`);
    } catch (err) {
      window.alert(err.message);
      btn.disabled = false;
    }
  });
}

async function renderAdminPasswordForm(tecnicoId) {
  renderLoading("Cargando...");
  const list = await apiFetch("/api/admin/tecnicos");
  const tec = list.find(t => t.id === tecnicoId);
  const nombre = tec ? `${escapeHtml(tec.apellido)} ${escapeHtml(tec.nombre)}` : `#${tecnicoId}`;

  document.querySelector("#app").innerHTML = layoutAdmin("tecnicos", `
    <div class="panel">
      <h3 style="margin:0 0 12px">Cambiar contraseña — ${nombre}</h3>
      <form id="pw-form">
        <div class="field"><label>Nueva contraseña *</label><input name="password" type="password" required /></div>
        <div class="button-row" style="margin-top:12px">
          <a class="button secondary" href="/admin/tecnicos">Cancelar</a>
          <button class="button primary" type="submit">Guardar</button>
        </div>
      </form>
    </div>
  `);

  document.querySelector("#pw-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.currentTarget.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await apiFetch(`/api/admin/tecnicos/${tecnicoId}/password`, {
        method: "POST",
        body: JSON.stringify({ password: e.currentTarget.password.value }),
      });
      navigate("/admin/tecnicos");
    } catch (err) {
      window.alert(err.message);
      btn.disabled = false;
    }
  });
}

async function renderAdminPasos(programaId) {
  renderLoading("Cargando pasos...");
  const [programas, pasos] = await Promise.all([
    apiFetch("/api/admin/programas"),
    apiFetch(`/api/admin/programas/${programaId}/pasos`),
  ]);
  const prog = programas.find(p => p.id === programaId);
  const titulo = prog ? `${escapeHtml(prog.equipo_nombre)} — ${escapeHtml(prog.descripcion)}` : `Programa #${programaId}`;

  const pasoCard = (p) => `
    <div class="panel" style="padding:10px 14px">
      <!-- Vista lectura -->
      <div class="paso-vista" id="vista-${p.id}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
          <div style="flex:1">
            <div style="font-weight:600;margin-bottom:2px">${p.posicion}. ${escapeHtml(p.descripcion)}</div>
            ${p.observaciones ? `<div class="muted" style="font-size:13px;margin-bottom:4px">${escapeHtml(p.observaciones)}</div>` : ""}
            <div class="muted" style="font-size:12px">
              ${p.adjunto_nombre
                ? `📎 <a href="#" class="ver-adjunto-paso" data-url="/api/admin/programas/${programaId}/pasos/${p.id}/adjunto" data-nombre="${escapeHtml(p.adjunto_nombre)}" data-back="/admin/programas/${programaId}/pasos">${escapeHtml(p.adjunto_nombre)}</a>`
                : "Sin adjunto"}
            </div>
          </div>
          <div style="display:flex;gap:4px;flex-shrink:0">
            <button class="btn-icon toggle-edit-btn" data-paso-id="${p.id}" title="Editar">✏️</button>
            <button class="btn-icon del-paso-btn" data-paso-id="${p.id}" title="Eliminar" style="color:#dc2626">🗑️</button>
          </div>
        </div>
      </div>
      <!-- Formulario edición (oculto) -->
      <div class="paso-form" id="form-${p.id}" style="display:none">
        <div class="field"><label>Descripción *</label>
          <input class="ep-desc" value="${escapeHtml(p.descripcion)}" /></div>
        <div class="field"><label>Observaciones</label>
          <textarea class="ep-obs">${escapeHtml(p.observaciones)}</textarea></div>
        <div class="field"><label>Adjunto</label>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            ${p.adjunto_nombre
              ? `<span class="muted ep-adj-nombre">${escapeHtml(p.adjunto_nombre)}</span>
                 <a href="#" class="ver-adjunto-paso button secondary" data-url="/api/admin/programas/${programaId}/pasos/${p.id}/adjunto" data-nombre="${escapeHtml(p.adjunto_nombre)}" data-back="/admin/programas/${programaId}/pasos" style="padding:4px 10px;font-size:12px;text-decoration:none">Ver</a>
                 <button type="button" class="button secondary ep-del-adj" style="padding:4px 10px;font-size:12px">Quitar</button>`
              : `<span class="muted ep-adj-nombre">Sin adjunto</span>`}
            <label class="button secondary" style="padding:4px 10px;font-size:12px;cursor:pointer">
              📎 Subir<input type="file" class="ep-file" style="display:none" />
            </label>
          </div>
        </div>
        <div class="button-row" style="margin-top:8px">
          <button class="button secondary toggle-edit-btn" data-paso-id="${p.id}">Cancelar</button>
          <button class="button primary ep-save" data-paso-id="${p.id}">Guardar</button>
        </div>
      </div>
    </div>`;

  document.querySelector("#app").innerHTML = layoutAdmin("programas", `
    <div class="panel" style="padding:10px 14px">
      <a class="back-link" href="/admin/programas/${programaId}" style="font-size:13px">← Volver al programa</a>
      <div style="margin-top:6px"><strong>Pasos:</strong> ${titulo}</div>
    </div>
    ${pasos.length ? pasos.map(pasoCard).join("") : `<div class="muted" style="padding:12px">Sin pasos definidos.</div>`}
    <div class="panel">
      <div class="section-title">Agregar paso</div>
      <form id="form-nuevo-paso">
        <div class="field"><label>Descripción *</label>
          <input id="np-desc" type="text" required placeholder="Descripción del paso..." /></div>
        <div class="field"><label>Observaciones</label>
          <textarea id="np-obs" placeholder="Observaciones opcionales..."></textarea></div>
        <div class="field"><label>Adjunto</label>
          <input id="np-file" type="file" /></div>
        <button class="button primary" type="submit">Agregar paso</button>
      </form>
    </div>
  `);

  async function recargar() { await renderAdminPasos(programaId); }

  // Toggle edit/vista
  document.querySelectorAll(".toggle-edit-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.pasoId;
      const vista = document.querySelector(`#vista-${id}`);
      const form  = document.querySelector(`#form-${id}`);
      vista.style.display = vista.style.display === "none" ? "" : "none";
      form.style.display  = form.style.display  === "none" ? "" : "none";
    });
  });

  // Guardar edición
  document.querySelectorAll(".ep-save").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.pasoId;
      const form = document.querySelector(`#form-${id}`);
      const desc = form.querySelector(".ep-desc").value.trim();
      const obs  = form.querySelector(".ep-obs").value.trim();
      if (!desc) { window.alert("La descripción no puede estar vacía."); return; }
      btn.disabled = true;
      try {
        await apiFetch(`/api/admin/programas/${programaId}/pasos/${id}`, {
          method: "PUT", body: JSON.stringify({ descripcion: desc, observaciones: obs }),
        });
        // Subir nuevo adjunto si se seleccionó
        const fileInput = form.querySelector(".ep-file");
        if (fileInput?.files[0]) {
          const fd = new FormData();
          fd.append("archivo", fileInput.files[0]);
          await fetch(`/api/admin/programas/${programaId}/pasos/${id}/adjunto`, {
            method: "POST",
            headers: state.token ? { Authorization: `Bearer ${state.token}` } : {},
            body: fd,
          });
        }
        await recargar();
      } catch (err) { window.alert(err.message); btn.disabled = false; }
    });
  });

  // Quitar adjunto desde formulario de edición
  document.querySelectorAll(".ep-del-adj").forEach(btn => {
    btn.addEventListener("click", async () => {
      const form = btn.closest(".paso-form");
      const pasoId = form.id.replace("form-", "");
      btn.disabled = true;
      try {
        await apiFetch(`/api/admin/programas/${programaId}/pasos/${pasoId}/adjunto`, { method: "DELETE" });
        await recargar();
      } catch (err) { window.alert(err.message); btn.disabled = false; }
    });
  });

  // Ver adjunto
  document.querySelectorAll(".ver-adjunto-paso").forEach(a => {
    a.addEventListener("click", e => {
      e.preventDefault();
      abrirAdjunto(a.dataset.url, a.dataset.nombre, a.dataset.back || "/admin/programas");
    });
  });

  // Eliminar paso
  document.querySelectorAll(".del-paso-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!window.confirm("¿Eliminar este paso?")) return;
      btn.disabled = true;
      try {
        await apiFetch(`/api/admin/programas/${programaId}/pasos/${btn.dataset.pasoId}`, { method: "DELETE" });
        await recargar();
      } catch (err) { window.alert(err.message); btn.disabled = false; }
    });
  });

  // Agregar paso
  document.querySelector("#form-nuevo-paso").addEventListener("submit", async (e) => {
    e.preventDefault();
    const desc = document.querySelector("#np-desc").value.trim();
    const obs  = document.querySelector("#np-obs").value.trim();
    const file = document.querySelector("#np-file").files[0];
    if (!desc) return;
    const btn = e.currentTarget.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      const nuevoPaso = await apiFetch(`/api/admin/programas/${programaId}/pasos`, {
        method: "POST", body: JSON.stringify({ descripcion: desc, observaciones: obs }),
      });
      if (file) {
        const fd = new FormData();
        fd.append("archivo", file);
        await fetch(`/api/admin/programas/${programaId}/pasos/${nuevoPaso.id}/adjunto`, {
          method: "POST",
          headers: state.token ? { Authorization: `Bearer ${state.token}` } : {},
          body: fd,
        });
      }
      await recargar();
    } catch (err) { window.alert(err.message); btn.disabled = false; }
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
    navigate("/ordenes");
  } catch (error) {
    document.querySelector("#app").innerHTML = loginView(error.message);
    document.querySelector("#login-form").addEventListener("submit", handleLoginSubmit);
  }
}

function parsePath() {
  const raw = location.pathname.slice(1) || "ordenes";
  return { path: raw, query: new URLSearchParams(location.search) };
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

async function renderDashboard() {
  renderLoading("Cargando dashboard...");
  const stats = await apiFetch("/api/admin/dashboard");
  document.querySelector("#app").innerHTML = layoutAdmin("dashboard", `
    <div class="topbar"><div><h1>Dashboard</h1></div></div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;padding:16px">
      ${[
        ["Pendientes", stats.ordenes_pendientes, "#f59e0b"],
        ["En progreso", stats.ordenes_en_progreso, "#3b82f6"],
        ["Completadas (mes)", stats.ordenes_completadas_mes, "#10b981"],
        ["Equipos activos", stats.equipos_activos, "#6366f1"],
        ["Alertas activas", stats.alertas_activas, "#ef4444"],
        ["Stock bajo", stats.repuestos_bajo_stock, "#f97316"],
        ["Mant. vencidos", stats.programas_vencidos, "#dc2626"],
      ].map(([label, valor, color]) => `
        <div style="background:#fff;border-radius:10px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.1);border-left:4px solid ${color}">
          <div style="font-size:28px;font-weight:700;color:${color}">${valor}</div>
          <div style="font-size:12px;color:#666;margin-top:4px">${label}</div>
        </div>`).join("")}
    </div>
  `);
}

// ── Alertas ───────────────────────────────────────────────────────────────────

async function renderAlertas() {
  renderLoading("Cargando alertas...");
  const alertas = await apiFetch("/api/alertas");
  state.alertasCount = alertas.length;
  const colores = { alta: "#ef4444", media: "#f59e0b", baja: "#10b981" };
  document.querySelector("#app").innerHTML = layoutAdmin("alertas", `
    <div class="topbar"><div><h1>Alertas (${alertas.length})</h1></div></div>
    <div style="padding:16px;display:flex;flex-direction:column;gap:10px">
      ${alertas.length === 0
        ? `<p style="color:#666;text-align:center;padding:32px">Sin alertas activas</p>`
        : alertas.map(a => `
        <div style="background:#fff;border-radius:8px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.1);border-left:4px solid ${colores[a.severidad] || "#999"}">
          <div style="font-weight:600;margin-bottom:6px">${escapeHtml(a.mensaje)}</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <span style="font-size:11px;background:#eee;padding:2px 8px;border-radius:12px">${a.tipo}</span>
            <span style="font-size:11px;background:${colores[a.severidad]}22;color:${colores[a.severidad]};padding:2px 8px;border-radius:12px">${a.severidad}</span>
            <button class="button secondary" style="font-size:11px;padding:2px 10px" onclick="snoozeAlerta('${escapeHtml(a.key)}')">Posponer 7d</button>
            <button class="button secondary" style="font-size:11px;padding:2px 10px" onclick="ignorarAlerta('${escapeHtml(a.key)}')">Ignorar</button>
          </div>
        </div>`).join("")}
    </div>
  `);
}

async function snoozeAlerta(key) {
  await apiFetch(`/api/alertas/${encodeURIComponent(key)}/snooze`, { method: "POST", body: JSON.stringify({ dias: 7 }) });
  await renderAlertas();
}

async function ignorarAlerta(key) {
  await apiFetch(`/api/alertas/${encodeURIComponent(key)}/ignorar`, { method: "POST", body: JSON.stringify({}) });
  await renderAlertas();
}

// ── Generar órdenes ───────────────────────────────────────────────────────────

async function renderGenerarOrdenes() {
  const hoy = new Date();
  document.querySelector("#app").innerHTML = layoutAdmin("generar", `
    <div class="topbar"><div><h1>Generar órdenes preventivas</h1></div></div>
    <div style="padding:20px;max-width:480px">
      <p style="color:#555;margin-bottom:16px">Genera órdenes de trabajo PREVENTIVO para los programas con vencimiento en el mes seleccionado. No duplica órdenes ya existentes.</p>
      <form id="generar-form" style="display:flex;flex-direction:column;gap:12px">
        <div class="field">
          <label>Mes</label>
          <select id="gen-mes" class="input">
            ${Array.from({length:12},(_,i)=>i+1).map(m=>`<option value="${m}" ${m===hoy.getMonth()+1?"selected":""}>${m.toString().padStart(2,"0")}</option>`).join("")}
          </select>
        </div>
        <div class="field">
          <label>Año</label>
          <input id="gen-anio" class="input" type="number" value="${hoy.getFullYear()}" min="2020" max="2030" />
        </div>
        <button class="button primary" type="submit">Generar órdenes</button>
      </form>
      <div id="generar-resultado" style="margin-top:16px"></div>
    </div>
  `);
  document.querySelector("#generar-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const mes = parseInt(document.querySelector("#gen-mes").value);
    const anio = parseInt(document.querySelector("#gen-anio").value);
    const div = document.querySelector("#generar-resultado");
    div.innerHTML = `<p>Generando...</p>`;
    try {
      const r = await apiFetch("/api/admin/generar-ordenes", { method: "POST", body: JSON.stringify({ mes, anio }) });
      div.innerHTML = `
        <div style="background:#d1fae5;border-radius:8px;padding:14px">
          <strong>${r.creadas} orden(es) creada(s)</strong>, ${r.existentes} ya existían.
          ${r.ordenes.length > 0 ? `<br>IDs: ${r.ordenes.join(", ")}` : ""}
        </div>`;
    } catch(err) {
      div.innerHTML = `<p style="color:#ef4444">${escapeHtml(err.message)}</p>`;
    }
  });
}

// ── Historial equipo (desde detalle de equipo en admin) ───────────────────────

async function renderHistorialEquipo(equipoId) {
  renderLoading("Cargando historial...");
  const historial = await apiFetch(`/api/admin/equipos/${equipoId}/historial`);
  const equipo = (await apiFetch("/api/admin/equipos")).find(e => e.id === equipoId);
  document.querySelector("#app").innerHTML = layoutAdmin("equipos", `
    <div class="topbar">
      <div><a class="back-link" href="/admin/equipos">← Equipos</a><h1>Historial: ${escapeHtml(equipo?.nombre || `#${equipoId}`)}</h1></div>
    </div>
    <div style="padding:16px">
      ${historial.length === 0
        ? `<p style="color:#666;text-align:center;padding:32px">Sin órdenes registradas</p>`
        : `<table class="admin-table"><thead><tr>
            <th>#</th><th>Tipo</th><th>Estado</th><th>Apertura</th><th>Técnico</th><th>Horas</th><th>Costo</th>
           </tr></thead><tbody>
           ${historial.map(h=>`<tr>
             <td><a href="/orden/${h.id}">#${h.id}</a></td>
             <td><span class="badge-tipo">${h.tipo}</span></td>
             <td><span class="badge ${h.estado.toLowerCase().replace("_","-")}">${h.estado}</span></td>
             <td>${h.fecha_apertura.slice(0,10)}</td>
             <td>${escapeHtml(h.tecnico_nombre)}</td>
             <td>${h.horas_trabajo || 0}h</td>
             <td>$${h.costo_mano_obra.toFixed(0)}</td>
           </tr>`).join("")}
           </tbody></table>`}
    </div>
  `);
}

// ── Electricidad ──────────────────────────────────────────────────────────────

async function renderElectricidad(medidorId = null) {
  renderLoading("Cargando electricidad...");
  const medidores = await apiFetch("/api/admin/electricidad/medidores");
  const selId = medidorId || medidores[0]?.id || null;

  let facturas = [], graficos = null;
  if (selId) {
    [facturas, graficos] = await Promise.all([
      apiFetch(`/api/admin/electricidad/medidores/${selId}/facturas`),
      apiFetch(`/api/admin/electricidad/medidores/${selId}/graficos`),
    ]);
  }

  document.querySelector("#app").innerHTML = layoutAdmin("electricidad", `
    <div class="topbar">
      <div><h1>Electricidad</h1></div>
      <div><a class="button primary" href="/admin/electricidad/nuevo-medidor" style="font-size:12px;padding:4px 12px">+ Medidor</a></div>
    </div>
    <div style="padding:16px">
      ${medidores.length === 0
        ? `<p style="color:#666;text-align:center;padding:32px">Sin medidores. Agregá uno primero.</p>`
        : `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">
            ${medidores.map(m=>`<a href="/admin/electricidad/${m.id}" class="button ${m.id===selId?"primary":"secondary"}" style="font-size:12px;padding:4px 12px">${escapeHtml(m.nombre)}</a>`).join("")}
           </div>
           ${selId ? `
             <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
               <h3 style="margin:0">Facturas — ${escapeHtml(medidores.find(m=>m.id===selId)?.nombre||"")}</h3>
               <a class="button primary" href="/admin/electricidad/${selId}/nueva-factura" style="font-size:12px;padding:4px 12px">+ Factura</a>
             </div>
             ${graficos && graficos.consumo_kwh.length > 0 ? renderGraficosElectricidad(graficos) : ""}
             <table class="admin-table"><thead><tr>
               <th>Período</th><th>kWh</th><th>DRP kW</th><th>kVAR</th><th>Importe</th><th></th>
             </tr></thead><tbody>
             ${facturas.map(f=>`<tr>
               <td>${f.periodo}</td>
               <td>${(f.kwh_punta+f.kwh_valle_noc+f.kwh_restantes).toFixed(0)}</td>
               <td>${f.drp_kw.toFixed(1)}</td>
               <td>${f.kvar_reactiva.toFixed(1)}</td>
               <td>$${f.importe.toFixed(0)}</td>
               <td><a class="btn-icon" href="/admin/electricidad/${selId}/factura/${f.id}">✏️</a></td>
             </tr>`).join("")}
             </tbody></table>
           ` : ""}`}
    </div>
  `);

  // Dibujar gráficos
  if (graficos && graficos.consumo_kwh.length > 0) {
    dibujarGrafico("canvas-kwh", graficos.consumo_kwh, "#3b82f6", "kWh");
    dibujarGrafico("canvas-kw", graficos.demanda_kw, "#f59e0b", "kW");
    const maxFp = Math.max(...graficos.factor_potencia.map(p => p.valor), 0);
    dibujarGrafico("canvas-fp", graficos.factor_potencia, "#10b981", "cos φ", maxFp * 0.85);
    dibujarGrafico("canvas-costo", graficos.costo_total, "#6366f1", "$");
  }
}

function renderGraficosElectricidad(g) {
  return `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
      ${[["canvas-kwh","Consumo kWh"],["canvas-kw","Demanda kW"],["canvas-fp","Factor de potencia"],["canvas-costo","Costo $"]].map(([id,lbl])=>`
        <div style="background:#fff;border-radius:8px;padding:12px;box-shadow:0 1px 4px rgba(0,0,0,.1)">
          <div style="font-size:12px;color:#666;margin-bottom:6px;font-weight:600">${lbl}</div>
          <canvas id="${id}" height="100" style="width:100%"></canvas>
        </div>`).join("")}
    </div>`;
}

function dibujarGrafico(canvasId, puntos, color, unidad, baseline = null) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || puntos.length === 0) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.offsetWidth || 300;
  const H = 100;
  canvas.width = W;
  canvas.height = H;
  const valores = puntos.map(p => p.valor);
  const max = Math.max(...valores) || 1;
  const min = baseline !== null ? baseline : 0;
  const range = (max - min) || 1;
  const barW = Math.max(2, (W - 20) / puntos.length - 2);
  ctx.clearRect(0, 0, W, H);
  puntos.forEach((p, i) => {
    const x = 10 + i * (barW + 2);
    const barH = Math.max(0, ((p.valor - min) / range) * (H - 20));
    ctx.fillStyle = color;
    ctx.fillRect(x, H - barH - 10, barW, barH);
  });
  ctx.fillStyle = "#666";
  ctx.font = "9px sans-serif";
  ctx.fillText(`${max.toFixed(unidad === "cos φ" ? 3 : 0)} ${unidad}`, 2, 10);
  if (min > 0) ctx.fillText(min.toFixed(3), 2, H - 2);
}

// ── Base de datos (export/import) ─────────────────────────────────────────────

function renderBaseDatos() {
  document.querySelector("#app").innerHTML = layoutAdmin("base-datos", `
    <div class="topbar"><div><h1>Base de datos</h1></div></div>
    <div style="padding:20px;max-width:480px;display:flex;flex-direction:column;gap:16px">
      <div style="background:#fff;border-radius:8px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.1)">
        <h3 style="margin:0 0 8px">Exportar</h3>
        <p style="color:#555;font-size:13px;margin-bottom:12px">Descargá una copia de la base de datos completa (archivo .sqlite).</p>
        <a class="button primary" href="${state.serverBase}/api/admin/db/exportar" download>⬇ Descargar backup</a>
      </div>
      <div style="background:#fff;border-radius:8px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.1)">
        <h3 style="margin:0 0 8px">Importar</h3>
        <p style="color:#555;font-size:13px;margin-bottom:4px">⚠️ Reemplaza la base de datos actual. Se genera un backup automático antes.</p>
        <form id="import-form" style="margin-top:10px">
          <input id="import-file" type="file" accept=".sqlite,.db" style="margin-bottom:8px;display:block" />
          <button class="button primary" type="submit">⬆ Importar</button>
        </form>
        <div id="import-resultado" style="margin-top:8px"></div>
      </div>
    </div>
  `);
  document.querySelector("#import-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = document.querySelector("#import-file").files[0];
    if (!file) return;
    const div = document.querySelector("#import-resultado");
    div.innerHTML = `<p>Importando...</p>`;
    try {
      const formData = new FormData();
      formData.append("file", file);
      const resp = await fetch(`${state.serverBase}/api/admin/db/importar`, {
        method: "POST",
        headers: { Authorization: `Bearer ${state.token}` },
        body: formData,
      });
      if (!resp.ok) throw new Error(`Error ${resp.status}`);
      div.innerHTML = `<p style="color:#10b981">✅ Importado correctamente. Recargá la app para ver los cambios.</p>`;
    } catch(err) {
      div.innerHTML = `<p style="color:#ef4444">${escapeHtml(err.message)}</p>`;
    }
  });
}

// ── Refresh alertas badge ─────────────────────────────────────────────────────

async function refreshAlertasBadge() {
  if (!state.token || !state.tecnico?.es_admin) return;
  try {
    const alertas = await apiFetch("/api/alertas");
    state.alertasCount = alertas.length;
  } catch (_) {}
}

function navigate(path) {
  history.pushState({}, "", path);
  render().catch(err => window.alert(err.message));
}

async function render() {
  if (!state.token || !state.tecnico) {
    document.querySelector("#app").innerHTML = loginView();
    document.querySelector("#login-form").addEventListener("submit", handleLoginSubmit);
    return;
  }
  const { path, query } = parsePath();
  if (path === "ordenes") {
    state.tab = query.get("tab") || "mis";
    await renderOrdenes();
    return;
  }
  if (path.startsWith("orden/")) {
    await renderOrdenDetalle(path.split("/")[1]);
    return;
  }
  if (path === "cronograma") {
    await renderCronograma();
    return;
  }
  if (path === "nueva-orden") {
    await renderNuevaOrden();
    return;
  }
  if (path === "adjunto") {
    await renderAdjunto();
    return;
  }
  if (path.startsWith("admin/")) {
    const parts = path.split("/");
    const section = parts[1];
    const subId = parts[2];
    const subAction = parts[3];
    if (section === "dashboard") {
      await renderDashboard();
    } else if (section === "alertas") {
      await renderAlertas();
    } else if (section === "generar") {
      await renderGenerarOrdenes();
    } else if (section === "base-datos") {
      renderBaseDatos();
    } else if (section === "electricidad") {
      if (subId === "nuevo-medidor") {
        await renderAdminForm("medidor", null);
      } else if (subId && subAction === "nueva-factura") {
        await renderAdminForm("factura-nueva", Number(subId));
      } else if (subId && subAction === "factura" && parts[4]) {
        await renderAdminForm("factura", Number(parts[4]), Number(subId));
      } else if (subId && !isNaN(Number(subId))) {
        await renderElectricidad(Number(subId));
      } else {
        await renderElectricidad();
      }
    } else if (section === "equipos" && subId && subAction === "historial") {
      await renderHistorialEquipo(Number(subId));
    } else if (section === "tecnicos" && subId && subAction === "password") {
      await renderAdminPasswordForm(Number(subId));
    } else if (section === "programas" && subId && !isNaN(Number(subId)) && subAction === "pasos") {
      await renderAdminPasos(Number(subId));
    } else if (subId === "nuevo") {
      await renderAdminForm(section, null);
    } else if (subId && !isNaN(Number(subId))) {
      await renderAdminForm(section, Number(subId));
    } else {
      await renderAdminList(section);
    }
    return;
  }
  navigate("/ordenes");
}

window.addEventListener("popstate", () => {
  render().catch((error) => window.alert(error.message));
});

// Arranque: verificar conexión antes de mostrar login
(async function startup() {
  // Mostrar indicador de conexión
  document.querySelector("#app").innerHTML = `
    <div class="login-shell">
      <div class="login-card" style="text-align:center">
        <p style="color:#666;margin-bottom:12px">Conectando al servidor…</p>
        <progress style="width:100%;height:4px"></progress>
      </div>
    </div>`;

  // Intentar con la URL almacenada (o relativa si no hay)
  const ok = await pingServer();
  if (ok) {
    render().catch((err) => {
      document.querySelector("#app").innerHTML = loginView(err.message);
      document.querySelector("#login-form").addEventListener("submit", handleLoginSubmit);
    });
  } else {
    showServerConfig(
      state.serverBase
        ? `No se pudo conectar a "${state.serverBase}".`
        : "No se encontró el servidor. Ingresá la IP manualmente."
    );
  }
})();
