"""Importa equipos y programas de mantenimiento del Cronograma 2026 + fichas
de mantenimiento (13. Formularios\\Mantenimiento) a la base de datos de la app.

Por defecto corre en modo DRY-RUN (no escribe nada). Para escribir:
    python import_cronograma_2026.py --commit

Se hace un backup de la base de datos antes de escribir.
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = r"C:\Users\LABOR01\AppData\Roaming\gestion_mantenimiento\gestion_mantenimiento.sqlite3"

# ---------------------------------------------------------------------------
# Checklist canónico para los equipos tipo "puente grúa / aparejo / pluma /
# monorriel" (variante B de las fichas), agrupado por categoría -> 1 programa
# por categoría.
# ---------------------------------------------------------------------------
CHECKLIST: dict[str, list[str]] = {
    "ESTRUCTURA": [
        "Comprobar uniones de guía (apriete de tornillos, soldaduras, etc.)",
        "Inspeccionar los carriles de rodadura (alineación, desgaste, fijación de vigas, etc.)",
    ],
    "TESTEOS": [
        "Comprobar la frenada simultánea de los grupos motrices",
        "Comprobar funcionamiento de los motores",
        "Comprobar desgaste de las pestañas de las ruedas",
        "Verificar niveles de aceite y estado de grasas en los grupos reductores",
        "Comprobar que no existen grietas capilares en las zonas de rodadura de las ruedas",
        "Comprobar apriete de tornillos y tuercas de fijación de los elementos (motores, reductores, topes, etc.)",
    ],
    "CARRO": [
        "Engrase del cable de elevación",
        "Comprobar pérdidas de aceite o grasa",
        "Comprobar estado guía de cables",
        "Comprobar estado de las ruedas del carro (pestañas, grietas, etc.)",
        "Inspeccionar el cable de elevación y sus amarres",
        "Engrasar dientes, rodamientos y puntos de fricción",
        "Verificar niveles de aceite y estado de grasas en los grupos reductores de elevación y traslación",
        "Examinar el desgaste de los elementos de freno",
        "Comprobar colocación, estado y apriete de grapas",
        "Comprobar regulaciones de limitador de carga máxima",
        "Comprobar apriete de tornillos y tuercas de fijación de los elementos",
    ],
    "GANCHOS": [
        "Observar giro de poleas (engrase a vida)",
        "Comprobar buen estado del gancho de carga",
        "Engrase de rodamiento axial",
        "Engrase de poleas (si no tiene engrase a vida)",
    ],
    "INSTALACIÓN ELÉCTRICA": [
        "Comprobar estado de los aparatos de protección y control automático",
        "Comprobar estado de mandos y controles manuales",
        "Comprobar estado de las cajas de conexión",
        "Comprobar que los frenos se sueltan al activar los motores",
        "Comprobar limitadores de fin de carrera de elevación, traslación de carro y puente",
        "Revisar estado de los elementos móviles de alimentación eléctrica",
        "Comprobar el estado de las conexiones en general",
        "Comprobar puesta a tierra",
        "Comprobar empalmes y sujeción de línea de alimentación",
    ],
    "SEÑALIZACIÓN": [
        "Comprobar que indique mediante cartel la carga máxima a levantar",
    ],
}

PIVOTE = "Engrasar pivote"


def checklist_programas(freq: int, ultima: str, proxima: str, pivote: bool = False):
    out = []
    for categoria, tareas in CHECKLIST.items():
        items = list(tareas)
        if categoria == "ESTRUCTURA" and pivote:
            items = items + [PIVOTE]
        descripcion = f"{categoria}: " + "; ".join(items)
        out.append((descripcion, freq, ultima, proxima))
    return out


# ---------------------------------------------------------------------------
# Equipos a crear (no incluye "noyera 1" ni "granalladora", que ya existen
# en la base y ya tienen sus programas cargados a partir de las fichas).
# ---------------------------------------------------------------------------
EQUIPOS = [
    {
        "nombre": "Compresor ETR-50",
        "marca": "Compresor Cetec ETR-50",
        "horas_trabajo_activo": 1,
        "horas_trabajo_actual": 0.0,
        "observaciones": (
            "Mantenimiento por horas (ficha 1): "
            "B - cada 1000 hs: cambio de aceite. "
            "C - cada 2000 hs: limpieza de radiador, limpieza de válvula de purgado, cambio de filtro de aceite. "
            "D - cada 8000 hs: cambio de filtro separador. "
            "Repuestos críticos: correas 2 (juego, SPZ 1060 Lw), filtro de aire 1, filtro de aceite 1, aceite 5 litros."
        ),
        "programas": [
            ("Limpieza general", 3, "2026-04-01", "2026-07-01"),
            ("Limpieza de filtro de aire", 3, "2026-04-01", "2026-07-01"),
            ("Control de correas", 3, "2026-04-01", "2026-07-01"),
            ("Control de mangueras", 3, "2026-04-01", "2026-07-01"),
            ("Control de nivel de aceite", 3, "2026-04-01", "2026-07-01"),
            ("Control de puesta a tierra", 3, "2026-04-01", "2026-07-01"),
        ],
    },
    {
        "nombre": "Compresor ETR-80C",
        "marca": "Compresor Cetec ETR-80C",
        "horas_trabajo_activo": 1,
        "horas_trabajo_actual": 0.0,
        "observaciones": (
            "Mantenimiento por horas (ficha 2): "
            "B - cada 2000 hs: cambio de filtro de aceite y de aire, control y ajuste de correas. "
            "C - cada 4000 hs: control de módulo de comando, engrase de rodamientos de motor. "
            "D - cada 8000 hs: control eléctrico general, cambio de aceite, cambio de filtro separador, "
            "control/cambio de correas, sello mecánico, kit de válvula de aspiración y kit de mangueras. "
            "Repuestos críticos: correas 4 (juego, SPZ 1162 Lw), aceite 5 litros sintético, filtro de aceite 1, filtro de aire 1."
        ),
        "programas": [
            ("Limpieza general", 3, "2026-04-01", "2026-07-01"),
            ("Limpieza de filtro de aire", 3, "2026-04-01", "2026-07-01"),
            ("Control de válvula de seguridad", 3, "2026-04-01", "2026-07-01"),
            ("Control de correas y de aceite", 3, "2026-04-01", "2026-07-01"),
            ("Control de puesta a tierra", 3, "2026-04-01", "2026-07-01"),
        ],
    },
    {
        "nombre": "Transformadores",
        "marca": "Brenta 200 Kva y 1000 Kva",
        "observaciones": "",
        "programas": [
            ("Limpieza general de la cabina (realiza personal externo)", 12, "2025-09-01", "2026-09-01"),
        ],
    },
    {
        "nombre": "Durómetro Brinell",
        "marca": "",
        "observaciones": (
            "Equipo sin ficha de mantenimiento detallada; programa generado a partir del cronograma 2026."
        ),
        "programas": [
            ("Calibración / control del durómetro", 6, "2026-05-01", "2026-11-01"),
        ],
    },
    {
        "nombre": "Zaranda 1",
        "marca": "",
        "observaciones": "Repuestos críticos: correa motor-rotor 1 (B-39), correa motor-zaranda 1 (B-41).",
        "programas": [
            ("Revisión de correas", 4, "2026-04-01", "2026-08-01"),
            ("Control de puesta a tierra", 4, "2026-04-01", "2026-08-01"),
        ],
    },
    {
        "nombre": "Zaranda 2",
        "marca": "",
        "observaciones": "Repuestos críticos: correa motor-rotor 1 (B-39), correa motor-zaranda 1 (B-41).",
        "programas": [
            ("Revisión de correas", 4, "2026-04-01", "2026-08-01"),
            ("Control de puesta a tierra", 4, "2026-04-01", "2026-08-01"),
        ],
    },
    {
        "nombre": "Noyera N° 2",
        "marca": "",
        "observaciones": (
            "Ubicación: automática, perpendicular al pasillo. "
            "Repuestos críticos: microswitch 1, botonera 1, aceite SAE 120-140 0,5 l, electroválvula 1."
        ),
        "programas": [
            ("Limpieza completa", 4, "2026-03-01", "2026-07-01"),
            ("Control de puesta a tierra", 4, "2026-03-01", "2026-07-01"),
            ("Control de aceite de reductores", 4, "2026-03-01", "2026-07-01"),
            ("Revisar pistones", 8, "2026-03-01", "2026-11-01"),
        ],
    },
    {
        "nombre": "Noyera N° 3",
        "marca": "",
        "observaciones": (
            "Ubicación: manual, amarilla, chica. "
            "Repuestos críticos: microswitch 1, botonera 1, aceite SAE 120-140 0,5 l, electroválvula 1."
        ),
        "programas": [
            ("Limpieza completa", 4, "2026-05-01", "2026-09-01"),
            ("Revisar pistones", 8, "2026-09-01", "2027-05-01"),
        ],
    },
    {
        "nombre": "Cascarera",
        "marca": "",
        "observaciones": (
            "Repuestos críticos: botonera 1, cadena corta de 1/2\" por 37 eslabones 1, "
            "cadena larga de 1/2\" por 49,5 eslabones 1, eslabón de cierre y medio eslabón 1."
        ),
        "programas": [
            ("Limpieza completa", 3, "2026-04-01", "2026-07-01"),
            ("Control de aceite de los reductores", 3, "2026-04-01", "2026-07-01"),
            ("Control de puesta a tierra", 3, "2026-04-01", "2026-07-01"),
            ("Engrase general", 6, "2026-04-01", "2026-10-01"),
        ],
    },
    {
        "nombre": "Pegadora de Vacío 1",
        "marca": "",
        "observaciones": "Repuestos críticos: goma (cámara tractor Goodyear 16,9 - 28) 1.",
        "programas": [
            ("Limpieza completa", 4, "2026-04-01", "2026-08-01"),
            ("Limpieza de filtro", 4, "2026-04-01", "2026-08-01"),
            ("Control de puesta a tierra", 4, "2026-04-01", "2026-08-01"),
        ],
    },
    {
        "nombre": "Pegadora de Vacío 2",
        "marca": "",
        "observaciones": "Repuestos críticos: goma (cámara tractor Goodyear 16,9 - 28) 1.",
        "programas": [
            ("Limpieza completa", 4, "2026-04-01", "2026-08-01"),
            ("Limpieza de filtro", 4, "2026-04-01", "2026-08-01"),
            ("Control de puesta a tierra", 4, "2026-04-01", "2026-08-01"),
        ],
    },
    {
        "nombre": "Molino de Tierra",
        "marca": "Tecno",
        "observaciones": "Repuestos críticos: correas 3 (juego, C-62), correas 2 (juego, B-67).",
        "programas": [
            ("Control de correas (2 juegos)", 4, "2026-02-01", "2026-06-01"),
            ("Control de aceite de los 2 reductores", 4, "2026-02-01", "2026-06-01"),
            ("Control de puesta a tierra", 4, "2026-02-01", "2026-06-01"),
        ],
    },
    {
        "nombre": "Mezclador Continuo de Arena",
        "marca": "IMF T36/3",
        "observaciones": (
            "Próximo mantenimiento de inyectores: realizar procedimiento de limpieza de los inyectores. "
            "Repuestos críticos: set completo de adaptador central + rulemán SKF 6207-2RS1 + retén 9315 (ext 72 - int 35)."
        ),
        "programas": [
            ("Control de aceite de reductor", 4, "2026-02-01", "2026-06-01"),
            ("Limpieza de filtros de resina y catalizador", 4, "2026-02-01", "2026-06-01"),
            ("Control de puesta a tierra", 4, "2026-02-01", "2026-06-01"),
            ("Limpieza de picos inyectores (desarmar completos)", 4, "2026-02-01", "2026-06-01"),
        ],
    },
    {
        "nombre": "Montacargas Molino de Tierra",
        "marca": "",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm, 6,5 m.",
        "programas": [
            ("Control de aceite de reductor", 3, "2026-02-01", "2026-05-01"),
            ("Control de cable de acero", 3, "2026-02-01", "2026-05-01"),
            ("Verificar extremos de sujeción del cable de acero", 3, "2026-02-01", "2026-05-01"),
            ("Control de puesta a tierra", 3, "2026-02-01", "2026-05-01"),
        ],
    },
    {
        "nombre": "Monorriel Horno Recuperación de Arena",
        "marca": "",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm 6 metros, seguro del gancho.",
        "programas": checklist_programas(3, "2026-04-01", "2026-07-01"),
    },
    {
        "nombre": "Pluma Moldeo",
        "marca": "",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm 6 metros, seguro del gancho.",
        "programas": checklist_programas(1, "2026-03-01", "2026-04-01", pivote=True),
    },
    {
        "nombre": "Puente Grúa (Noyería)",
        "marca": "",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm 10 metros, seguro del gancho, correa 1 (B-40).",
        "programas": checklist_programas(3, "2026-04-01", "2026-07-01"),
    },
    {
        "nombre": "Puente Grúa (Sayos 500 Kg)",
        "marca": "",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm 12 metros, seguro del gancho, correa 1 (B-40).",
        "programas": checklist_programas(3, "2026-04-01", "2026-07-01"),
    },
    {
        "nombre": "Puente Grúa (Sayos 1000 Kg)",
        "marca": "",
        "observaciones": "Repuestos críticos: 28 m de cable de acero 6x36 de ⌀ 6 mm, seguro del gancho.",
        "programas": checklist_programas(2, "2026-04-01", "2026-06-01"),
    },
    {
        "nombre": "Aparejo Eléctrico Mezcladora de Arena",
        "marca": "",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm 6 metros, seguro del gancho.",
        "programas": checklist_programas(3, "2026-02-01", "2026-05-01"),
    },
    {
        "nombre": "Puente Grúa (Expedición)",
        "marca": "Ferro",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm 32 metros, seguro del gancho.",
        "programas": checklist_programas(3, "2026-04-01", "2026-07-01"),
    },
    {
        "nombre": "Sistema de Elevación de Arena Recuperada",
        "marca": "",
        "observaciones": (
            "Repuestos críticos: correa B-41 (1), cadena de 70 eslabones, corona de 50 dientes y diámetro "
            "de eje 45 mm; motor del extractor, reductor del extractor, conjunto extractor de arena tolva. "
            "El tipo C del cronograma no tiene detalle en la ficha; se cargó como revisión genérica."
        ),
        "programas": [
            ("Control y/o limpieza de la fosa", 2, "2026-03-01", "2026-05-01"),
            ("Revisar cañerías de elevación de arena", 2, "2026-03-01", "2026-05-01"),
            ("Revisar pérdidas en el lecho fluido", 2, "2026-03-01", "2026-05-01"),
            ("Controlar puesta a tierra (motores de ventiladores, sacudidores y sinfín)", 2, "2026-03-01", "2026-05-01"),
            ("Controlar aceite de reductores (válvula rotativa y sinfín)", 2, "2026-03-01", "2026-05-01"),
            ("Control de reductor del extractor de la tolva de arena", 6, "2026-01-01", "2026-07-01"),
            ("Revisar estado de las turbinas", 6, "2026-01-01", "2026-07-01"),
            ("Limpiar todas las cámaras de aire", 6, "2026-01-01", "2026-07-01"),
            ("Limpiar lecho fluido", 6, "2026-01-01", "2026-07-01"),
            ("Revisión adicional (tipo C, sin detalle específico en ficha)", 9, "2026-02-01", "2026-11-01"),
        ],
    },
    {
        "nombre": "Mangas Sistema Elevador de Arena",
        "marca": "",
        "observaciones": "",
        "programas": [
            ("Limpieza y control de mangas", 2, "2026-04-01", "2026-06-01"),
        ],
    },
    {
        "nombre": "Aparejo Eléctrico Zona de Amolado",
        "marca": "",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm 6 metros, seguro del gancho.",
        "programas": checklist_programas(3, "2026-02-01", "2026-05-01"),
    },
    {
        "nombre": "Lavador de Humos",
        "marca": "",
        "observaciones": (
            "Repuestos críticos: bomba 1 (Pedrollo HF/5 BM), correa juego de 2 (B43), 2 rodamientos UCP 208."
        ),
        "programas": [
            ("Engrase de rodamientos del ventilador", 1, "2026-06-01", "2026-07-01"),
            ("Verificar correas del ventilador", 1, "2026-06-01", "2026-07-01"),
            ("Limpieza completa (de ser necesario)", 3, "2026-04-01", "2026-07-01"),
            ("Control visual", 3, "2026-04-01", "2026-07-01"),
            ("Control de bomba (caudal: 20 lts)", 3, "2026-04-01", "2026-07-01"),
            ("Control del ventilador (engrase y correas)", 3, "2026-04-01", "2026-07-01"),
            ("Verificar focos de oxidación en el interior", 3, "2026-04-01", "2026-07-01"),
            ("Limpieza del tanque interno (sector chatarra)", 3, "2026-04-01", "2026-07-01"),
        ],
    },
    {
        "nombre": "Pluma Horno",
        "marca": "",
        "observaciones": "Repuestos críticos: cable de acero ⌀ 5 mm 6 metros, seguro del gancho.",
        "programas": checklist_programas(1, "2026-04-01", "2026-05-01", pivote=True),
    },
    {
        "nombre": "Horno Inducción",
        "marca": "",
        "observaciones": (
            "Repuestos críticos: filtro de aceite ERA32NCD (equiv. CID). "
            "Seguimiento adicional registrado en el cronograma: revisión periódica de mangueras hidráulicas "
            "(tapadas con manta) y componente PE 713.3."
        ),
        "programas": [
            ("Control de estado de mangueras", 1, "2026-04-01", "2026-05-01"),
            ("Limpieza general", 1, "2026-04-01", "2026-05-01"),
            ("Control de pérdidas de agua", 1, "2026-04-01", "2026-05-01"),
            ("Engrase general", 1, "2026-04-01", "2026-05-01"),
            ("Control de nivel de aceite hidráulico", 1, "2026-04-01", "2026-05-01"),
            ("Control de nivel de agua del tanque", 1, "2026-04-01", "2026-05-01"),
            ("Ajuste de abrazaderas del sistema de refrigeración", 1, "2026-04-01", "2026-05-01"),
            ("Limpieza de bomba hidráulica", 4, "2026-05-01", "2026-09-01"),
            ("Controlar estado de bujes", 4, "2026-05-01", "2026-09-01"),
            ("Control de filtros de aceite del sistema hidráulico", 4, "2026-05-01", "2026-09-01"),
            ("Controlar puesta a tierra", 4, "2026-05-01", "2026-09-01"),
        ],
    },
    {
        "nombre": "Radiador (PE713.1)",
        "marca": "",
        "observaciones": (
            "Equipo sin ficha de mantenimiento detallada; programas generados a partir de las notas del "
            "cronograma 2026 (componente del sistema de refrigeración del Horno de Inducción)."
        ),
        "programas": [
            ("Revisión y cambio de correas", 1, "2026-04-01", "2026-05-01"),
            ("Lavado de radiador externo con vinagre", 6, "2026-02-01", "2026-08-01"),
        ],
    },
    {
        "nombre": "Amoladoras",
        "marca": "Bosch",
        "observaciones": (
            "Según el cronograma 2026, no se realiza mantenimiento preventivo a estas máquinas; "
            "se incluyen solo para seguimiento."
        ),
        "programas": [],
    },
]


def main(commit: bool) -> None:
    if commit:
        backup_path = DB_PATH + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S")
        shutil.copy2(DB_PATH, backup_path)
        print(f"Backup creado en: {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        tipo_id = conn.execute(
            "SELECT id FROM tipos_equipo ORDER BY id LIMIT 1"
        ).fetchone()
        tipo_id = tipo_id["id"] if tipo_id else None

        existentes = {
            row["nombre"] for row in conn.execute("SELECT nombre FROM equipos")
        }

        total_equipos = 0
        total_programas = 0
        for equipo in EQUIPOS:
            nombre = equipo["nombre"]
            if nombre in existentes:
                print(f"OMITIDO (ya existe): {nombre}")
                continue

            print(f"Equipo: {nombre} -> {len(equipo['programas'])} programa(s)")
            for desc, freq, ult, prox in equipo["programas"]:
                print(f"    [{freq}m] {ult} -> {prox} | {desc[:90]}")

            total_equipos += 1
            total_programas += len(equipo["programas"])

            if not commit:
                continue

            cur = conn.execute(
                """
                INSERT INTO equipos
                    (nombre, tipo_id, marca, observaciones,
                     horas_trabajo_activo, horas_trabajo_actual)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    nombre,
                    tipo_id,
                    equipo.get("marca", ""),
                    equipo.get("observaciones", ""),
                    int(equipo.get("horas_trabajo_activo", 0)),
                    float(equipo.get("horas_trabajo_actual", 0.0)),
                ),
            )
            equipo_id = cur.lastrowid

            for desc, freq, ult, prox in equipo["programas"]:
                conn.execute(
                    """
                    INSERT INTO programas_mantenimiento
                        (equipo_id, descripcion, frecuencia_meses, ultima_ejecucion, proxima_ejecucion)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (equipo_id, desc, freq, ult, prox),
                )

        if commit:
            conn.commit()
            print(f"\nCOMMIT: {total_equipos} equipos, {total_programas} programas insertados.")
        else:
            print(f"\nDRY RUN: {total_equipos} equipos, {total_programas} programas se insertarían.")
            print("Ejecutá con --commit para escribir en la base de datos.")
    finally:
        conn.close()


if __name__ == "__main__":
    main(commit="--commit" in sys.argv)
