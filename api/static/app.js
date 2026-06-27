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
  // Respuestas sin cuerpo (204 No Content, 205)
  if (response.status === 204 || response.status === 205) return null;
  const ct = response.headers.get("content-type") || "";
  if (!ct.includes("application/json")) return null;
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

async function abrirFichaRepuesto(repuestoId) {
  // Mostrar modal superpuesto con la ficha del repuesto
  const overlay = document.createElement("div");
  overlay.id = "ficha-overlay";
  overlay.style.cssText =
    "position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px";
  overlay.innerHTML = `<div style="background:#fff;border-radius:12px;width:min(480px,100%);max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.3)">
    <div style="padding:16px;text-align:center;color:#666">Cargando ficha…</div>
  </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener("click", e => { if (e.target === overlay) overlay.remove(); });

  try {
    const f = await apiFetch(`/api/repuestos/${repuestoId}/ficha`);
    const imgHtml = f.tiene_imagen
      ? `<img src="${state.serverBase}/api/admin/repuestos/${f.id}/imagen"
             style="width:100%;max-height:200px;object-fit:cover;border-radius:8px 8px 0 0;display:block" />`
      : "";
    const provHtml = f.proveedores.length
      ? `<div style="margin-top:14px">
           <div style="font-size:12px;color:#666;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">Proveedores</div>
           ${f.proveedores.map(p => `
             <div style="background:#f9fafb;border-radius:8px;padding:10px 12px;margin-bottom:8px">
               <div style="font-weight:600">${escapeHtml(p.nombre)} ${p.es_principal ? `<span style="background:#10b981;color:#fff;border-radius:4px;padding:1px 6px;font-size:11px">Principal</span>` : ""}</div>
               ${p.contacto ? `<div style="font-size:13px;color:#555;margin-top:2px">👤 ${escapeHtml(p.contacto)}</div>` : ""}
               ${p.telefono ? `<div style="font-size:13px;color:#555">📞 ${escapeHtml(p.telefono)}</div>` : ""}
               ${p.email    ? `<div style="font-size:13px;color:#555">✉ ${escapeHtml(p.email)}</div>` : ""}
             </div>`).join("")}
         </div>`
      : `<div style="margin-top:14px;color:#999;font-size:13px">Sin proveedores registrados.</div>`;

    overlay.querySelector("div").innerHTML = `
      ${imgHtml}
      <div style="padding:18px">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
          <h2 style="margin:0;font-size:20px">${escapeHtml(f.nombre)}</h2>
          <button id="close-ficha" style="background:none;border:none;font-size:22px;cursor:pointer;color:#666;flex-shrink:0">✕</button>
        </div>
        ${f.descripcion ? `<p style="color:#555;font-size:14px;margin:6px 0 0">${escapeHtml(f.descripcion)}</p>` : ""}
        <div style="background:#f0fdf4;border-radius:8px;padding:10px 14px;margin:14px 0;display:flex;align-items:center;gap:10px">
          <span style="font-size:28px;font-weight:700;color:#15803d">${f.stock_actual}</span>
          <span style="color:#555;font-size:13px">unidades en stock</span>
        </div>
        ${f.observaciones ? `<div style="font-size:13px;color:#666;background:#fffbeb;padding:8px 12px;border-radius:6px;border-left:3px solid #f59e0b">${escapeHtml(f.observaciones)}</div>` : ""}
        ${provHtml}
      </div>`;
    document.getElementById("close-ficha").addEventListener("click", () => overlay.remove());
  } catch(err) {
    overlay.querySelector("div").innerHTML = `
      <div style="padding:20px;text-align:center">
        <p style="color:#ef4444">${escapeHtml(err.message)}</p>
        <button onclick="document.getElementById('ficha-overlay').remove()" class="button secondary">Cerrar</button>
      </div>`;
  }
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
      ${state.tecnico?.es_admin ? `<a class="nav-link ${active === "admin" ? "active" : ""}" href="/admin/hub">Admin ${state.alertasCount > 0 ? `<span class="badge">${state.alertasCount}</span>` : ""}</a>` : ""}
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
            ${paso.repuesto_nombre
              ? `<a href="#" class="paso-repuesto-link" data-repuesto-id="${paso.repuesto_id}"
                   style="display:inline-block;background:#e0f2fe;color:#0369a1;border-radius:6px;padding:3px 10px;font-size:12px;text-decoration:none;margin:4px 0">
                   📦 ${escapeHtml(paso.repuesto_nombre)} — ver ficha
                 </a>`
              : ""}
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
  // Ficha de repuesto desde paso
  document.querySelectorAll(".paso-repuesto-link").forEach(a => {
    a.addEventListener("click", e => {
      e.preventDefault();
      abrirFichaRepuesto(Number(a.dataset.repuestoId));
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

// Nombre legible por sección para el topbar
const ADMIN_LABELS = {
  dashboard: "Dashboard", alertas: "Alertas",
  equipos: "Equipos", tipos: "Tipos de equipo", programas: "Programas de mantenimiento",
  repuestos: "Repuestos", consolidado: "Stock consolidado", proveedores: "Proveedores", tecnicos: "Técnicos", ordenes: "Órdenes",
  generar: "Generar órdenes", electricidad: "Electricidad", "base-datos": "Base de datos",
};

function layoutAdmin(section, content) {
  const esHub = section === "hub";
  const titulo = esHub ? "Administración" : (ADMIN_LABELS[section] ?? section);
  const backLink = esHub ? "" : `<a class="back-link" href="/admin/hub" style="margin-right:10px">← Panel</a>`;
  return layout(`
    <div class="topbar"><div>${backLink}<h1>${titulo}</h1></div></div>
    ${content}
  `, "admin");
}

function renderAdminHub() {
  const grupos = [
    {
      titulo: "🔔 Monitoreo",
      items: [
        { href: "/admin/dashboard", icon: "📊", label: "Dashboard", desc: "Estadísticas globales: órdenes activas, equipos y alertas pendientes" },
        { href: "/admin/alertas",   icon: "🔔", label: "Alertas",   desc: "Notificaciones de stock bajo, órdenes sin técnico asignado y mantenimientos vencidos" },
      ],
    },
    {
      titulo: "⚙️ Gestión",
      items: [
        { href: "/admin/equipos",   icon: "🏭", label: "Equipos",   desc: "Gestión de máquinas con programas preventivos, repuestos asignados e historial de órdenes" },
        { href: "/admin/tipos",     icon: "🏷️",  label: "Tipos de equipo", desc: "Categorías para clasificar los equipos (ej: Bomba, Motor, Compresor)" },
        { href: "/admin/repuestos", icon: "📦", label: "Repuestos", desc: "Catálogo global de repuestos con descripción, imagen y proveedores" },
        { href: "/admin/repuestos/consolidado", icon: "📊", label: "Stock consolidado", desc: "Stock actual vs suma de mínimos requeridos por cada equipo" },
        { href: "/admin/proveedores", icon: "🏢", label: "Proveedores", desc: "Empresas proveedoras: datos de contacto, CUIT y vínculo con repuestos" },
        { href: "/admin/tecnicos",  icon: "👷", label: "Técnicos",  desc: "Alta y modificación de usuarios técnicos, roles y contraseñas" },
        { href: "/admin/ordenes",   icon: "📝", label: "Órdenes",   desc: "Ver, editar y eliminar todas las órdenes de trabajo del sistema" },
      ],
    },
    {
      titulo: "🔧 Herramientas",
      items: [
        { href: "/admin/generar",      icon: "📅", label: "Generar órdenes", desc: "Crea automáticamente órdenes preventivas para los programas que vencen en el mes seleccionado" },
        { href: "/admin/electricidad", icon: "⚡", label: "Electricidad",    desc: "Medidores EDESUR, carga de facturas y gráficos de consumo, demanda y factor de potencia" },
        { href: "/admin/base-datos",   icon: "💾", label: "Base de datos",   desc: "Descargar backup, importar datos o purgar órdenes no completadas" },
      ],
    },
  ];

  document.querySelector("#app").innerHTML = layoutAdmin("hub", `
    <div style="padding:16px;display:flex;flex-direction:column;gap:20px">
      ${grupos.map(g => `
        <div>
          <div style="font-size:13px;font-weight:700;color:#888;letter-spacing:.5px;margin-bottom:8px;padding:0 2px">${g.titulo}</div>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px">
            ${g.items.map(it => `
              <a href="${it.href}" style="text-decoration:none">
                <div class="admin-hub-card">
                  <span style="font-size:22px">${it.icon}</span>
                  <div>
                    <div style="font-weight:600;font-size:14px">${it.label}</div>
                    <div style="font-size:11px;color:#888;margin-top:2px">${it.desc}</div>
                  </div>
                </div>
              </a>`).join("")}
          </div>
        </div>`).join("")}
    </div>
  `);
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
  let title = ADMIN_LABELS[section] ?? section;
  let extraHeader = "";

  if (section === "equipos") {
    tableHead = `<tr><th>#</th><th>Nombre</th><th>Tipo</th><th>Ubicación</th><th>Activo</th><th></th></tr>`;
    tableRows = items.map(r => `<tr>
      <td class="muted">${r.id}</td><td>${escapeHtml(r.nombre)}</td><td>${escapeHtml(r.tipo_nombre)}</td>
      <td>${escapeHtml(r.ubicacion)}</td><td>${r.activo ? "✓" : "–"}</td>
      <td style="white-space:nowrap">
        <a class="btn-icon" href="/admin/equipos/${r.id}/programas" title="Programas de mantenimiento">🗓️</a>
        <a class="btn-icon" href="/admin/equipos/${r.id}/repuestos" title="Repuestos del equipo">📦</a>
        <a class="btn-icon" href="/admin/equipos/${r.id}/historial" title="Historial de órdenes">📋</a>
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
    tableHead = `<tr><th></th><th>Nombre</th><th>Descripción</th><th>Stock</th><th>Activo</th><th></th></tr>`;
    tableRows = items.map(r => `<tr>
      <td style="width:36px">${r.tiene_imagen
        ? `<img src="${state.serverBase}/api/admin/repuestos/${r.id}/imagen" style="width:32px;height:32px;object-fit:cover;border-radius:4px" />`
        : `<span style="font-size:20px">📦</span>`}</td>
      <td><strong>${escapeHtml(r.nombre)}</strong></td>
      <td class="muted" style="font-size:12px">${escapeHtml(r.descripcion || "")}</td>
      <td>${r.stock_actual}</td>
      <td>${r.activo ? "✓" : "–"}</td>
      <td style="white-space:nowrap">
        <a class="btn-icon" href="/admin/repuestos/${r.id}/proveedores" title="Proveedores">🏢</a>
        <a class="btn-icon" href="/admin/repuestos/${r.id}" title="Editar">✏️</a>
        <button class="btn-icon" data-delete="${r.id}" title="Eliminar">🗑️</button>
      </td></tr>`).join("");
  } else if (section === "proveedores") {
    tableHead = `<tr><th>Nombre</th><th>CUIT</th><th>Contacto</th><th>Teléfono</th><th>Email</th><th>Activo</th><th></th></tr>`;
    tableRows = items.map(r => `<tr>
      <td><strong>${escapeHtml(r.nombre)}</strong></td>
      <td>${escapeHtml(r.cuit)}</td>
      <td>${escapeHtml(r.contacto)}</td>
      <td>${escapeHtml(r.telefono)}</td>
      <td>${escapeHtml(r.email)}</td>
      <td>${r.activo ? "✓" : "–"}</td>
      <td style="white-space:nowrap">
        <a class="btn-icon" href="/admin/proveedores/${r.id}" title="Editar">✏️</a>
        <button class="btn-icon" data-delete="${r.id}" title="Eliminar">🗑️</button>
      </td></tr>`).join("");
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

async function renderAdminForm(section, id, _extras = {}, equipoIdOrigen = null) {
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
    const equipoFijo = equipoIdOrigen ?? item?.equipo_id ?? null;
    const equipoNombreFijo = equipoFijo ? (extras.equipos.find(e => e.id === equipoFijo)?.nombre ?? `#${equipoFijo}`) : null;
    const equipoOpts = extras.equipos.filter(e => e.activo || item?.equipo_id === e.id)
      .map(e => `<option value="${e.id}" ${(item?.equipo_id ?? equipoFijo) === e.id ? "selected" : ""}>${escapeHtml(e.nombre)}</option>`).join("");
    fields = `
      ${equipoFijo
        ? `<div class="field"><label>Equipo</label><strong>${escapeHtml(equipoNombreFijo)}</strong><input type="hidden" name="equipo_id" value="${equipoFijo}" /></div>`
        : `<div class="field"><label>Equipo *</label><select name="equipo_id" required><option value="">Seleccionar...</option>${equipoOpts}</select></div>`}
      <div class="field"><label>Descripción *</label><input name="descripcion" value="${escapeHtml(item?.descripcion ?? "")}" required /></div>
      <div class="field"><label>Frecuencia (meses) *</label><input name="frecuencia_meses" type="number" min="1" max="120" value="${item?.frecuencia_meses ?? 1}" required /></div>
      <div class="field"><label>Última ejecución</label><input name="ultima_ejecucion" type="date" value="${escapeHtml(item?.ultima_ejecucion ?? "")}" /></div>
      <div class="field"><label><input type="checkbox" name="activo" ${item?.activo !== false ? "checked" : ""}> Activo</label></div>`;
  } else if (section === "repuestos") {
    fields = `
      <div class="field"><label>Nombre *</label><input name="nombre" value="${escapeHtml(item?.nombre ?? "")}" required /></div>
      <div class="field"><label>Descripción</label><textarea name="descripcion" rows="2">${escapeHtml(item?.descripcion ?? "")}</textarea></div>
      <div class="field"><label>Observaciones internas</label><textarea name="observaciones">${escapeHtml(item?.observaciones ?? "")}</textarea></div>
      <div class="field"><label>Stock actual</label><input name="stock_actual" type="number" step="0.001" value="${item?.stock_actual ?? 0}" /></div>
      ${item ? `<div class="field"><label>Imagen del repuesto</label>
        ${item.tiene_imagen ? `<img src="${state.serverBase}/api/admin/repuestos/${item.id}/imagen" style="height:80px;border-radius:6px;margin-bottom:6px;display:block" />` : ""}
        <input type="file" id="repuesto-img-input" accept="image/*" />
        ${item.tiene_imagen ? `<button type="button" id="repuesto-img-delete" class="button secondary" style="font-size:12px;margin-top:4px">🗑 Quitar imagen</button>` : ""}
      </div>` : ""}
      <div class="field"><label><input type="checkbox" name="activo" ${item?.activo !== false ? "checked" : ""}> Activo</label></div>`;
  } else if (section === "proveedores") {
    fields = `
      <div class="field"><label>Nombre *</label><input name="nombre" value="${escapeHtml(item?.nombre ?? "")}" required /></div>
      <div class="field"><label>CUIT</label><input name="cuit" value="${escapeHtml(item?.cuit ?? "")}" /></div>
      <div class="field"><label>Contacto</label><input name="contacto" value="${escapeHtml(item?.contacto ?? "")}" /></div>
      <div class="field"><label>Teléfono</label><input name="telefono" value="${escapeHtml(item?.telefono ?? "")}" /></div>
      <div class="field"><label>Email</label><input name="email" type="email" value="${escapeHtml(item?.email ?? "")}" /></div>
      <div class="field"><label>Dirección</label><input name="direccion" value="${escapeHtml(item?.direccion ?? "")}" /></div>
      <div class="field"><label>Notas / condiciones</label><textarea name="notas" rows="3">${escapeHtml(item?.notas ?? "")}</textarea></div>
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

  const title = `${isNew ? "Nuevo" : "Editar"} — ${ADMIN_LABELS[section] ?? section}`;
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

  // Botón eliminar imagen de repuesto
  const delImgBtn = document.getElementById("repuesto-img-delete");
  if (delImgBtn) delImgBtn.addEventListener("click", () => { delImgBtn.dataset.clicked = "1"; delImgBtn.textContent = "✓ Se eliminará al guardar"; delImgBtn.disabled = true; });

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
        body = { nombre: g("nombre"), descripcion: g("descripcion"),
                 observaciones: g("observaciones"),
                 stock_actual: gNum("stock_actual"), activo: gBool("activo") };
      } else if (section === "proveedores") {
        body = { nombre: g("nombre"), cuit: g("cuit"), contacto: g("contacto"),
                 telefono: g("telefono"), email: g("email"), direccion: g("direccion"),
                 notas: g("notas"), activo: gBool("activo") };
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
      let savedId = id;
      if (isNew) {
        const saved = await apiFetch(`/api/admin/${apiSec}`, { method: "POST", body: JSON.stringify(body) });
        savedId = saved?.id ?? id;
      } else {
        await apiFetch(`/api/admin/${apiSec}/${id}`, { method: "PUT", body: JSON.stringify(body) });
      }
      // Upload imagen de repuesto si se seleccionó una
      if (section === "repuestos" && savedId) {
        const imgInput = document.getElementById("repuesto-img-input");
        if (imgInput?.files?.length) {
          const fd = new FormData();
          fd.append("imagen", imgInput.files[0]);
          await fetch(`${state.serverBase}/api/admin/repuestos/${savedId}/imagen`, {
            method: "POST", headers: { Authorization: `Bearer ${state.token}` }, body: fd,
          });
        }
        const delBtn = document.getElementById("repuesto-img-delete");
        if (delBtn?.dataset?.clicked) {
          await apiFetch(`/api/admin/repuestos/${savedId}/imagen`, { method: "DELETE" });
        }
      }
      // Si viene desde un equipo, volver a sus programas
      if (section === "programas" && equipoIdOrigen) {
        navigate(`/admin/equipos/${equipoIdOrigen}/programas`);
      } else {
        navigate(`/admin/${section}`);
      }
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

// ── Programas de un equipo ────────────────────────────────────────────────────

async function renderAdminProgramasEquipo(equipoId) {
  renderLoading("Cargando programas...");
  const [equipos, todosProgramas] = await Promise.all([
    apiFetch("/api/admin/equipos"),
    apiFetch("/api/admin/programas"),
  ]);
  const equipo = equipos.find(e => e.id === equipoId);
  const programas = todosProgramas.filter(p => p.equipo_id === equipoId);
  const titulo = equipo ? escapeHtml(equipo.nombre) : `Equipo #${equipoId}`;

  document.querySelector("#app").innerHTML = layoutAdmin("equipos", `
    <div class="topbar">
      <div>
        <a class="back-link" href="/admin/equipos">← Equipos</a>
        <h1>${titulo} — Programas de mantenimiento</h1>
      </div>
      <a class="button primary" href="/admin/equipos/${equipoId}/programas/nuevo" style="font-size:13px;padding:6px 14px">+ Nuevo programa</a>
    </div>

    ${programas.length === 0
      ? `<p class="muted" style="text-align:center;padding:32px">Sin programas definidos para este equipo.<br>
         <a href="/admin/equipos/${equipoId}/programas/nuevo" class="button primary" style="display:inline-block;margin-top:12px;padding:8px 16px">+ Crear primer programa</a></p>`
      : `<table class="admin-table"><thead><tr>
          <th>Descripción</th><th>Frecuencia</th><th>Última ejec.</th><th>Próxima ejec.</th><th>Activo</th><th></th>
        </tr></thead><tbody>
        ${programas.map(p => `<tr>
          <td><strong>${escapeHtml(p.descripcion)}</strong></td>
          <td>Cada ${p.frecuencia_meses} mes${p.frecuencia_meses !== 1 ? "es" : ""}</td>
          <td>${p.ultima_ejecucion ? p.ultima_ejecucion.slice(0,10) : "—"}</td>
          <td>${p.proxima_ejecucion ? `<span style="color:${new Date(p.proxima_ejecucion) < new Date() ? "#ef4444" : "#10b981"}">${p.proxima_ejecucion.slice(0,10)}</span>` : "—"}</td>
          <td>${p.activo ? "✓" : "–"}</td>
          <td style="white-space:nowrap">
            <a class="btn-icon" href="/admin/equipos/${equipoId}/programas/${p.id}/pasos" title="Pasos">🗂️</a>
            <a class="btn-icon" href="/admin/equipos/${equipoId}/programas/${p.id}" title="Editar">✏️</a>
            <button class="btn-icon" data-delete-prog="${p.id}" title="Eliminar">🗑️</button>
          </td>
        </tr>`).join("")}
        </tbody></table>`}
  `);

  document.querySelectorAll("[data-delete-prog]").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!window.confirm("¿Eliminar este programa?")) return;
      await apiFetch(`/api/admin/programas/${btn.dataset.deleteProg}`, { method: "DELETE" });
      await renderAdminProgramasEquipo(equipoId);
    });
  });
}

async function renderAdminPasos(programaId) {
  renderLoading("Cargando pasos...");
  const [programas, pasos, repuestosEquipo] = await Promise.all([
    apiFetch("/api/admin/programas"),
    apiFetch(`/api/admin/programas/${programaId}/pasos`),
    apiFetch(`/api/admin/programas/${programaId}/repuestos-equipo`),
  ]);
  const prog = programas.find(p => p.id === programaId);
  const titulo = prog ? `${escapeHtml(prog.equipo_nombre)} — ${escapeHtml(prog.descripcion)}` : `Programa #${programaId}`;
  const equipoId = prog?.equipo_id ?? null;

  const repuestoOpts = (selectedId) =>
    `<option value="">— Sin repuesto —</option>` +
    repuestosEquipo.map(r =>
      `<option value="${r.repuesto_id}" ${r.repuesto_id === selectedId ? "selected" : ""}>${escapeHtml(r.repuesto_nombre)}</option>`
    ).join("");

  const pasoCard = (p) => `
    <div class="panel" style="padding:10px 14px">
      <!-- Vista lectura -->
      <div class="paso-vista" id="vista-${p.id}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
          <div style="flex:1">
            <div style="font-weight:600;margin-bottom:2px">${p.posicion}. ${escapeHtml(p.descripcion)}</div>
            ${p.observaciones ? `<div class="muted" style="font-size:13px;margin-bottom:4px">${escapeHtml(p.observaciones)}</div>` : ""}
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:4px">
              ${p.repuesto_nombre
                ? `<span style="background:#e0f2fe;color:#0369a1;border-radius:6px;padding:2px 8px;font-size:12px">📦 ${escapeHtml(p.repuesto_nombre)}</span>`
                : ""}
            </div>
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
        <div class="field"><label>Repuesto requerido</label>
          <select class="ep-repuesto">${repuestoOpts(p.repuesto_id)}</select>
          ${repuestosEquipo.length === 0 && equipoId
            ? `<div style="font-size:12px;margin-top:4px;color:#6b7280">
                Sin repuestos en este equipo.
                <a href="/admin/equipos/${equipoId}/repuestos" style="color:#3b82f6">+ Agregar repuesto al equipo</a>
               </div>`
            : equipoId
              ? `<div style="font-size:12px;margin-top:4px">
                  <a href="/admin/equipos/${equipoId}/repuestos" style="color:#3b82f6">+ Agregar otro repuesto al equipo</a>
                 </div>`
              : ""}
        </div>
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

  const backToEquipo = prog ? `/admin/equipos/${prog.equipo_id}/programas` : "/admin/equipos";
  document.querySelector("#app").innerHTML = layoutAdmin("equipos", `
    <div class="panel" style="padding:10px 14px">
      <a class="back-link" href="${backToEquipo}" style="font-size:13px">← Volver a programas de ${prog ? escapeHtml(prog.equipo_nombre) : "equipo"}</a>
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
        <div class="field"><label>Repuesto requerido</label>
          <select id="np-repuesto">${repuestoOpts(null)}</select>
          ${equipoId ? `<div style="font-size:12px;margin-top:4px"><a href="/admin/equipos/${equipoId}/repuestos" style="color:#3b82f6">+ Agregar repuesto al equipo</a></div>` : ""}
        </div>
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
      const repId = Number(form.querySelector(".ep-repuesto").value) || null;
      if (!desc) { window.alert("La descripción no puede estar vacía."); return; }
      btn.disabled = true;
      try {
        await apiFetch(`/api/admin/programas/${programaId}/pasos/${id}`, {
          method: "PUT", body: JSON.stringify({ descripcion: desc, observaciones: obs, repuesto_id: repId }),
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
    const repId = Number(document.querySelector("#np-repuesto").value) || null;
    const file = document.querySelector("#np-file").files[0];
    if (!desc) return;
    const btn = e.currentTarget.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      const nuevoPaso = await apiFetch(`/api/admin/programas/${programaId}/pasos`, {
        method: "POST", body: JSON.stringify({ descripcion: desc, observaciones: obs, repuesto_id: repId }),
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

const ALERTA_TABS = [
  { key: "todas",       label: "Todas",        tipo: null },
  { key: "stock",       label: "📦 Stock",     tipo: "STOCK_BAJO" },
  { key: "ordenes",     label: "📝 Órdenes",   tipo: "ORDEN_NUEVA" },
  { key: "mantenimiento", label: "🔧 Mantenimiento", tipo: "MANT_VENCIDO" },
];

let _alertasData = [];
let _alertasTab = "todas";

async function renderAlertas(tab = _alertasTab) {
  if (_alertasData.length === 0) {
    renderLoading("Cargando alertas...");
    _alertasData = await apiFetch("/api/alertas");
    state.alertasCount = _alertasData.length;
  }
  _alertasTab = tab;

  const colores = { alta: "#ef4444", media: "#f59e0b", baja: "#10b981" };
  const tipoActivo = ALERTA_TABS.find(t => t.key === tab)?.tipo ?? null;
  const lista = tipoActivo ? _alertasData.filter(a => a.tipo === tipoActivo) : _alertasData;

  const conteos = {};
  ALERTA_TABS.forEach(t => {
    conteos[t.key] = t.tipo ? _alertasData.filter(a => a.tipo === t.tipo).length : _alertasData.length;
  });

  const tabColors = { todas: "#6b7280", stock: "#f97316", ordenes: "#3b82f6", mantenimiento: "#10b981" };

  document.querySelector("#app").innerHTML = layoutAdmin("alertas", `
    <div class="topbar"><div><h1>Alertas (${_alertasData.length})</h1></div></div>

    <div class="tabs" style="grid-template-columns:repeat(${ALERTA_TABS.length},1fr)">
      ${ALERTA_TABS.map(t => `
        <button class="tab ${t.key === tab ? "active" : ""}" data-alerta-tab="${t.key}"
          style="border:none;background:none;cursor:pointer">
          ${t.label}
          ${conteos[t.key] > 0
            ? `<span style="margin-left:4px;background:${tabColors[t.key]||"#999"};color:#fff;border-radius:10px;font-size:10px;padding:1px 6px">${conteos[t.key]}</span>`
            : ""}
        </button>`).join("")}
    </div>

    <div style="padding:16px;display:flex;flex-direction:column;gap:10px">
      ${lista.length === 0
        ? `<p style="color:#666;text-align:center;padding:32px">Sin alertas en esta categoría</p>`
        : lista.map(a => `
          <div style="background:#fff;border-radius:8px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.1);border-left:4px solid ${colores[a.severidad] || "#999"}">
            <div style="font-weight:600;margin-bottom:6px">${escapeHtml(a.mensaje)}</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
              <span style="font-size:11px;background:${colores[a.severidad]}22;color:${colores[a.severidad]};padding:2px 8px;border-radius:12px">${a.severidad}</span>
              <button class="button secondary" style="font-size:11px;padding:2px 10px" data-snooze="${escapeHtml(a.key)}">Posponer 7d</button>
              <button class="button secondary" style="font-size:11px;padding:2px 10px" data-ignorar="${escapeHtml(a.key)}">Ignorar</button>
            </div>
          </div>`).join("")}
    </div>
  `);

  // Tabs — event listeners (necesario porque type="module" no expone globales a onclick)
  document.querySelectorAll("[data-alerta-tab]").forEach(btn => {
    btn.addEventListener("click", () => renderAlertas(btn.dataset.alertaTab));
  });

  // Snooze / Ignorar — event delegation
  document.querySelectorAll("[data-snooze]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await apiFetch(`/api/alertas/${encodeURIComponent(btn.dataset.snooze)}/snooze`, { method: "POST", body: JSON.stringify({ dias: 7 }) });
      _alertasData = [];
      await renderAlertas(_alertasTab);
    });
  });
  document.querySelectorAll("[data-ignorar]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await apiFetch(`/api/alertas/${encodeURIComponent(btn.dataset.ignorar)}/ignorar`, { method: "POST", body: JSON.stringify({}) });
      _alertasData = [];
      await renderAlertas(_alertasTab);
    });
  });
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
  const H = 110;
  canvas.width = W;
  canvas.height = H;

  const valores = puntos.map(p => p.valor);
  const max = Math.max(...valores) || 1;
  const min = baseline !== null ? baseline : 0;
  const range = (max - min) || 1;
  const barW = Math.max(2, (W - 20) / puntos.length - 2);
  const esMobile = window.matchMedia("(hover: none)").matches || "ontouchstart" in window;
  const decimales = unidad === "cos φ" ? 3 : 1;

  // Aclara un color hex para resaltar la barra activa
  function colorActivo(hex) {
    const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
    return `rgba(${Math.min(255,r+70)},${Math.min(255,g+70)},${Math.min(255,b+70)},1)`;
  }

  // Convierte coordenada X del cliente al índice de barra
  function barIdx(clientX) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = W / rect.width;
    const relX = (clientX - rect.left) * scaleX;
    const i = Math.floor((relX - 10) / (barW + 2));
    return (i >= 0 && i < puntos.length) ? i : null;
  }

  function draw(activeIdx = null) {
    ctx.clearRect(0, 0, W, H);

    // Barras
    puntos.forEach((p, i) => {
      const x = 10 + i * (barW + 2);
      const barH = Math.max(0, ((p.valor - min) / range) * (H - 30));
      ctx.fillStyle = i === activeIdx ? colorActivo(color) : color;
      ctx.fillRect(x, H - barH - 18, barW, barH);
    });

    // Etiquetas de escala
    ctx.fillStyle = "#888";
    ctx.font = "9px sans-serif";
    ctx.fillText(`${max.toFixed(decimales)} ${unidad}`, 2, 10);
    if (min > 0) ctx.fillText(min.toFixed(decimales), 2, H - 6);

    // Tooltip de la barra activa
    if (activeIdx !== null) {
      const p = puntos[activeIdx];
      const x = 10 + activeIdx * (barW + 2);
      const barH = Math.max(0, ((p.valor - min) / range) * (H - 30));
      const label = `${p.periodo}  ${p.valor.toFixed(decimales)} ${unidad}`;

      ctx.font = "bold 10px sans-serif";
      const tw = ctx.measureText(label).width;
      const pad = 5;
      let tx = x + barW / 2 - tw / 2 - pad;
      tx = Math.max(0, Math.min(tx, W - tw - pad * 2 - 4));
      const ty = H - barH - 40;
      const tooltipY = Math.max(2, ty);

      ctx.fillStyle = "rgba(30,30,30,0.82)";
      ctx.beginPath();
      ctx.rect(tx, tooltipY, tw + pad * 2, 18);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.fillText(label, tx + pad, tooltipY + 13);

      // Línea vertical indicadora
      ctx.strokeStyle = "rgba(30,30,30,0.35)";
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(x + barW / 2, tooltipY + 18);
      ctx.lineTo(x + barW / 2, H - barH - 18);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  // Dibujo inicial
  draw();

  // ── Desktop: hover ────────────────────────────────────────────────────────
  if (!esMobile) {
    canvas.addEventListener("mousemove", e => draw(barIdx(e.clientX)));
    canvas.addEventListener("mouseleave", () => draw());
  }

  // ── Mobile: toque persistente ─────────────────────────────────────────────
  if (esMobile) {
    let selected = null;
    canvas.addEventListener("touchstart", e => {
      e.preventDefault();
      const i = barIdx(e.touches[0].clientX);
      selected = (i !== null && i !== selected) ? i : null;
      draw(selected);
    }, { passive: false });
    // Toque fuera del canvas deselecciona
    document.addEventListener("touchstart", e => {
      if (!canvas.contains(e.target) && selected !== null) {
        selected = null;
        draw();
      }
    }, { passive: true });
  }
}

// ── Base de datos (export/import) ─────────────────────────────────────────────

// ── Repuestos por equipo ──────────────────────────────────────────────────────

async function renderAdminRepuestosEquipo(equipoId) {
  renderLoading("Cargando repuestos del equipo...");
  const [equipos, vinculos, catalogo] = await Promise.all([
    apiFetch("/api/admin/equipos"),
    apiFetch(`/api/admin/equipos/${equipoId}/repuestos`),
    apiFetch("/api/admin/repuestos"),
  ]);
  const equipo = equipos.find(e => e.id === equipoId);
  const titulo = equipo ? escapeHtml(equipo.nombre) : `Equipo #${equipoId}`;
  const vinculadosIds = new Set(vinculos.map(v => v.repuesto_id));
  const disponibles = catalogo.filter(r => r.activo && !vinculadosIds.has(r.id));

  document.querySelector("#app").innerHTML = layoutAdmin("equipos", `
    <div class="topbar">
      <div><a class="back-link" href="/admin/equipos">← Equipos</a><h1>${titulo} — Repuestos</h1></div>
    </div>
    <div style="padding:16px">
      ${vinculos.length === 0
        ? `<p class="muted" style="text-align:center;padding:24px">Sin repuestos vinculados a este equipo.</p>`
        : `<table class="admin-table"><thead><tr>
            <th></th><th>Repuesto</th><th>Descripción</th><th>Stock global</th><th>Mínimo este equipo</th><th>Observaciones</th><th></th>
          </tr></thead><tbody>
          ${vinculos.map(v => `<tr>
            <td style="width:36px">${v.tiene_imagen
              ? `<img src="${state.serverBase}/api/admin/repuestos/${v.repuesto_id}/imagen" style="width:32px;height:32px;object-fit:cover;border-radius:4px" />`
              : `<span style="font-size:18px">📦</span>`}</td>
            <td><strong>${escapeHtml(v.repuesto_nombre)}</strong></td>
            <td class="muted" style="font-size:12px">${escapeHtml(v.repuesto_descripcion || "")}</td>
            <td>${v.stock_actual ?? "—"}</td>
            <td>
              <input type="number" step="0.001" min="0" value="${v.stock_minimo}"
                data-vinculo-id="${v.id}" data-field="stock_minimo"
                style="width:70px;padding:3px 6px;border:1px solid #ccc;border-radius:4px" />
            </td>
            <td>
              <input type="text" value="${escapeHtml(v.observaciones)}"
                data-vinculo-id="${v.id}" data-field="observaciones"
                style="width:140px;padding:3px 6px;border:1px solid #ccc;border-radius:4px" />
            </td>
            <td>
              <button class="btn-icon" data-save-vinculo="${v.id}" title="Guardar">💾</button>
              <button class="btn-icon" data-del-vinculo="${v.id}" title="Desvincular">🗑️</button>
            </td>
          </tr>`).join("")}
          </tbody></table>`}

      <div style="margin-top:20px;padding-top:16px;border-top:1px solid #eee">
        <h3 style="margin-bottom:12px">Agregar repuesto</h3>
        ${disponibles.length > 0 ? `
          <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">
            <div class="field" style="margin:0"><label>Repuesto</label>
              <select id="new-rep-id" style="min-width:180px">
                <option value="">Seleccionar...</option>
                ${disponibles.map(r => `<option value="${r.id}">${escapeHtml(r.nombre)}</option>`).join("")}
              </select>
            </div>
            <div class="field" style="margin:0"><label>Stock mínimo</label>
              <input id="new-rep-min" type="number" step="0.001" min="0" value="0" style="width:80px" />
            </div>
            <div class="field" style="margin:0"><label>Observaciones</label>
              <input id="new-rep-obs" type="text" style="width:140px" />
            </div>
            <button id="btn-add-vinculo" class="button primary">+ Vincular</button>
          </div>` : `
          <p style="color:#666;font-size:13px">
            Todos los repuestos del catálogo ya están vinculados a este equipo.
            <a href="/admin/repuestos/nuevo" style="color:#3b82f6">+ Crear nuevo repuesto</a>
          </p>`}
      </div>
    </div>
  `);

  // Guardar cambios en vínculo existente
  document.querySelectorAll("[data-save-vinculo]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const vid = btn.dataset.saveVinculo;
      const row = btn.closest("tr");
      const minInput = row.querySelector(`[data-vinculo-id="${vid}"][data-field="stock_minimo"]`);
      const obsInput = row.querySelector(`[data-vinculo-id="${vid}"][data-field="observaciones"]`);
      await apiFetch(`/api/admin/equipos/${equipoId}/repuestos/${vid}`, {
        method: "PUT",
        body: JSON.stringify({ stock_minimo: Number(minInput.value), observaciones: obsInput.value }),
      });
      btn.textContent = "✓";
      setTimeout(() => { btn.textContent = "💾"; }, 1500);
    });
  });

  // Desvincular
  document.querySelectorAll("[data-del-vinculo]").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!window.confirm("¿Desvincular este repuesto del equipo?")) return;
      await apiFetch(`/api/admin/equipos/${equipoId}/repuestos/${btn.dataset.delVinculo}`, { method: "DELETE" });
      await renderAdminRepuestosEquipo(equipoId);
    });
  });

  // Agregar nuevo vínculo
  document.getElementById("btn-add-vinculo")?.addEventListener("click", async () => {
    const repId = Number(document.getElementById("new-rep-id").value);
    if (!repId) { window.alert("Seleccioná un repuesto."); return; }
    const minimo = Number(document.getElementById("new-rep-min").value);
    const obs = document.getElementById("new-rep-obs").value;
    try {
      await apiFetch(`/api/admin/equipos/${equipoId}/repuestos`, {
        method: "POST",
        body: JSON.stringify({ repuesto_id: repId, stock_minimo: minimo, observaciones: obs }),
      });
      await renderAdminRepuestosEquipo(equipoId);
    } catch (err) { window.alert(err.message); }
  });
}

// ── Proveedores de un repuesto ────────────────────────────────────────────────

async function renderAdminRepuestosProveedor(repuestoId) {
  renderLoading("Cargando proveedores del repuesto...");
  const [repuestos, vinculos, catalogoProv] = await Promise.all([
    apiFetch("/api/admin/repuestos"),
    apiFetch(`/api/admin/repuestos/${repuestoId}/proveedores`),
    apiFetch("/api/admin/proveedores"),
  ]);
  const repuesto = repuestos.find(r => r.id === repuestoId);
  const titulo = repuesto ? escapeHtml(repuesto.nombre) : `Repuesto #${repuestoId}`;
  const vinculadosIds = new Set(vinculos.map(v => v.proveedor_id));
  const disponibles = catalogoProv.filter(p => p.activo && !vinculadosIds.has(p.id));

  document.querySelector("#app").innerHTML = layoutAdmin("repuestos", `
    <div class="topbar">
      <div><a class="back-link" href="/admin/repuestos">← Repuestos</a><h1>${titulo} — Proveedores</h1></div>
    </div>
    <div style="padding:16px">
      ${vinculos.length === 0
        ? `<p class="muted" style="text-align:center;padding:24px">Sin proveedores vinculados.</p>`
        : `<table class="admin-table"><thead><tr>
            <th>Proveedor</th><th>Contacto</th><th>Teléfono</th><th>Email</th><th>Principal</th><th></th>
          </tr></thead><tbody>
          ${vinculos.map(v => `<tr>
            <td><strong>${escapeHtml(v.proveedor_nombre)}</strong></td>
            <td>${escapeHtml(v.proveedor_contacto)}</td>
            <td>${escapeHtml(v.proveedor_telefono)}</td>
            <td>${escapeHtml(v.proveedor_email)}</td>
            <td style="text-align:center">
              ${v.es_principal
                ? `<span style="background:#10b981;color:#fff;border-radius:6px;padding:2px 8px;font-size:11px">⭐ Principal</span>`
                : `<button class="button secondary" style="font-size:11px;padding:2px 8px" data-set-principal="${v.id}">Marcar principal</button>`}
            </td>
            <td><button class="btn-icon" data-del-vinculo-prov="${v.id}" title="Desvincular">🗑️</button></td>
          </tr>`).join("")}
          </tbody></table>`}

      <div style="margin-top:20px;padding-top:16px;border-top:1px solid #eee">
        <h3 style="margin-bottom:12px">Agregar proveedor</h3>
        ${disponibles.length > 0 ? `
          <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">
            <div class="field" style="margin:0"><label>Proveedor</label>
              <select id="new-prov-id" style="min-width:200px">
                <option value="">Seleccionar...</option>
                ${disponibles.map(p => `<option value="${p.id}">${escapeHtml(p.nombre)}</option>`).join("")}
              </select>
            </div>
            <div class="field" style="margin:0">
              <label><input type="checkbox" id="new-prov-principal" /> Principal</label>
            </div>
            <button id="btn-add-prov" class="button primary">+ Vincular</button>
          </div>` : `
          <p style="color:#666;font-size:13px">
            Todos los proveedores del catálogo ya están vinculados a este repuesto.
            <a href="/admin/proveedores/nuevo" style="color:#3b82f6">+ Crear nuevo proveedor</a>
          </p>`}
      </div>
    </div>
  `);

  // Marcar como principal
  document.querySelectorAll("[data-set-principal]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await apiFetch(`/api/admin/repuestos/${repuestoId}/proveedores/${btn.dataset.setPrincipal}`, {
        method: "PUT", body: JSON.stringify({ es_principal: true }),
      });
      await renderAdminRepuestosProveedor(repuestoId);
    });
  });

  // Desvincular
  document.querySelectorAll("[data-del-vinculo-prov]").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!window.confirm("¿Desvincular este proveedor?")) return;
      await apiFetch(`/api/admin/repuestos/${repuestoId}/proveedores/${btn.dataset.delVinculoProv}`, { method: "DELETE" });
      await renderAdminRepuestosProveedor(repuestoId);
    });
  });

  // Agregar
  document.getElementById("btn-add-prov")?.addEventListener("click", async () => {
    const provId = Number(document.getElementById("new-prov-id").value);
    if (!provId) { window.alert("Seleccioná un proveedor."); return; }
    const esPrincipal = document.getElementById("new-prov-principal").checked;
    try {
      await apiFetch(`/api/admin/repuestos/${repuestoId}/proveedores`, {
        method: "POST", body: JSON.stringify({ proveedor_id: provId, es_principal: esPrincipal }),
      });
      await renderAdminRepuestosProveedor(repuestoId);
    } catch (err) { window.alert(err.message); }
  });
}

// ── Vista consolidada de stock ────────────────────────────────────────────────

async function renderAdminConsolidado() {
  renderLoading("Cargando stock consolidado...");
  const items = await apiFetch("/api/admin/repuestos/consolidado");
  const alertas = items.filter(i => i.en_alerta).length;

  document.querySelector("#app").innerHTML = layoutAdmin("consolidado", `
    <div class="topbar">
      <div><h1>Stock consolidado ${alertas > 0 ? `<span style="background:#ef4444;color:#fff;border-radius:10px;font-size:13px;padding:2px 10px;margin-left:8px">${alertas} con alerta</span>` : ""}</h1></div>
    </div>
    <div style="padding:16px">
      ${items.length === 0
        ? `<p class="muted" style="text-align:center;padding:32px">Sin repuestos en el sistema.</p>`
        : `<table class="admin-table"><thead><tr>
            <th></th><th>Repuesto</th><th>Descripción</th><th>Stock actual</th><th>Suma mínimos</th><th>Estado</th><th>Equipos</th>
          </tr></thead><tbody>
          ${items.map((it, idx) => `
            <tr style="${it.en_alerta ? "background:#fff5f5" : ""}">
              <td style="width:36px">${it.tiene_imagen
                ? `<img src="${state.serverBase}/api/admin/repuestos/${it.repuesto_id}/imagen" style="width:32px;height:32px;object-fit:cover;border-radius:4px" />`
                : `<span style="font-size:18px">📦</span>`}</td>
              <td><strong>${escapeHtml(it.repuesto_nombre)}</strong></td>
              <td class="muted" style="font-size:12px">${escapeHtml(it.repuesto_descripcion || "")}</td>
              <td><strong>${it.stock_actual}</strong></td>
              <td>${it.suma_minimos}</td>
              <td>${it.en_alerta
                ? `<span style="background:#ef4444;color:#fff;border-radius:6px;padding:2px 8px;font-size:11px">⚠ BAJO STOCK</span>`
                : `<span style="background:#10b981;color:#fff;border-radius:6px;padding:2px 8px;font-size:11px">✓ OK</span>`}</td>
              <td>
                ${it.equipos.length === 0
                  ? `<span class="muted">—</span>`
                  : `<button class="button secondary" style="font-size:11px;padding:2px 8px" data-expand="${idx}">Ver (${it.equipos.length})</button>
                     <div id="equipos-${idx}" style="display:none;margin-top:6px;font-size:12px">
                       ${it.equipos.map(e => `<div>• ${escapeHtml(e.equipo_nombre)}: mín. <strong>${e.stock_minimo}</strong></div>`).join("")}
                     </div>`}
              </td>
            </tr>`).join("")}
          </tbody></table>`}
    </div>
  `);

  // Expandir/colapsar equipos
  document.querySelectorAll("[data-expand]").forEach(btn => {
    btn.addEventListener("click", () => {
      const div = document.getElementById(`equipos-${btn.dataset.expand}`);
      if (div.style.display === "none") { div.style.display = "block"; btn.textContent = "Ocultar"; }
      else { div.style.display = "none"; btn.textContent = `Ver (${div.querySelectorAll("div").length})`; }
    });
  });
}

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

      <div style="background:#fff;border-radius:8px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.1);border:1px solid #fca5a5">
        <h3 style="margin:0 0 8px;color:#b91c1c">🗑 Purgar órdenes no completadas</h3>
        <p style="color:#555;font-size:13px;margin-bottom:12px">
          Elimina <strong>permanentemente</strong> todas las órdenes en estado
          PENDIENTE, EN PROGRESO o CANCELADA. Las órdenes COMPLETADAS se conservan.
          Esta acción no se puede deshacer.
        </p>
        <button id="btn-purgar" class="button danger">Purgar órdenes…</button>
        <div id="purgar-resultado" style="margin-top:10px"></div>
      </div>

    </div>
  `);

  // Importar
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
        method: "POST", headers: { Authorization: `Bearer ${state.token}` }, body: formData,
      });
      if (!resp.ok) throw new Error(`Error ${resp.status}`);
      div.innerHTML = `<p style="color:#10b981">✅ Importado correctamente. Recargá la app para ver los cambios.</p>`;
    } catch(err) {
      div.innerHTML = `<p style="color:#ef4444">${escapeHtml(err.message)}</p>`;
    }
  });

  // Purgar órdenes
  document.querySelector("#btn-purgar").addEventListener("click", () => {
    const div = document.querySelector("#purgar-resultado");
    div.innerHTML = `
      <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;padding:14px;margin-top:4px">
        <p style="font-size:13px;color:#7f1d1d;margin:0 0 10px">
          Ingresá tu contraseña para confirmar la purga:
        </p>
        <input id="purgar-pwd" type="password" placeholder="Contraseña"
          style="width:100%;padding:8px;border:1px solid #fca5a5;border-radius:6px;margin-bottom:8px" />
        <div style="display:flex;gap:8px">
          <button id="btn-purgar-confirmar" class="button danger" style="flex:1">Confirmar y purgar</button>
          <button id="btn-purgar-cancelar" class="button secondary" style="flex:1">Cancelar</button>
        </div>
        <div id="purgar-msg" style="margin-top:8px"></div>
      </div>`;

    document.querySelector("#btn-purgar-cancelar").addEventListener("click", () => {
      div.innerHTML = "";
    });

    document.querySelector("#btn-purgar-confirmar").addEventListener("click", async () => {
      const pwd = document.querySelector("#purgar-pwd").value;
      const msg = document.querySelector("#purgar-msg");
      if (!pwd) { msg.innerHTML = `<p style="color:#ef4444">Ingresá tu contraseña.</p>`; return; }
      msg.innerHTML = `<p style="color:#666">Purgando...</p>`;
      try {
        const r = await apiFetch("/api/admin/ordenes/purgar", {
          method: "POST", body: JSON.stringify({ password: pwd }),
        });
        div.innerHTML = `<p style="color:#10b981;margin-top:8px">
          ✅ Se eliminaron ${r.eliminadas} orden(es) no completadas.
        </p>`;
      } catch(err) {
        msg.innerHTML = `<p style="color:#ef4444">${escapeHtml(err.message)}</p>`;
      }
    });
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
  if (path === "admin" || path === "admin/hub") {
    renderAdminHub();
    return;
  }
  if (path.startsWith("admin/")) {
    const parts = path.split("/");
    const section = parts[1];
    const subId = parts[2];
    const subAction = parts[3];
    if (section === "hub") {
      renderAdminHub();
    } else if (section === "dashboard") {
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
    } else if (section === "repuestos" && subId === "consolidado") {
      await renderAdminConsolidado();
    } else if (section === "repuestos" && subId && !isNaN(Number(subId)) && subAction === "proveedores") {
      await renderAdminRepuestosProveedor(Number(subId));
    } else if (section === "equipos" && subId && !isNaN(Number(subId)) && subAction === "programas") {
      const subSubId = parts[4];  // /admin/equipos/{id}/programas/{progId}
      if (subSubId === "nuevo") {
        await renderAdminForm("programas", null, {}, Number(subId));
      } else if (subSubId && !isNaN(Number(subSubId)) && parts[5] === "pasos") {
        await renderAdminPasos(Number(subSubId));
      } else if (subSubId && !isNaN(Number(subSubId))) {
        await renderAdminForm("programas", Number(subSubId), {}, Number(subId));
      } else {
        await renderAdminProgramasEquipo(Number(subId));
      }
    } else if (section === "equipos" && subId && !isNaN(Number(subId)) && subAction === "repuestos") {
      await renderAdminRepuestosEquipo(Number(subId));
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
