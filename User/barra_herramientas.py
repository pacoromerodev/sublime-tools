"""
Barra de herramientas con pestañas (estilo cinta) para Sublime Text 4.

Sublime Text no permite añadir barras propias a la ventana, así que la barra es
una pestaña HTML en una fila fina encima del editor:

    ┌──────────────────────────────────────────────────────────┐
    │ Inicio  Buscar  Líneas  Texto  Formato  Codificar  …     │  ← pestañas
    │ [Nuevo] [Abrir] [Guardar] │ [Deshacer] [Rehacer] …       │  ← herramientas
    ├──────────────────────────────────────────────────────────┤
    │ (tus archivos)                                           │

Las herramientas se aplican al último archivo en el que estabas.
Pestañas, botones y opciones: "Barra de herramientas.sublime-settings".
Mostrar u ocultar: Ver → Barra de herramientas, o la paleta de comandos.
"""

import html
import json

import sublime
import sublime_plugin

AJUSTES = "Barra de herramientas.sublime-settings"
NOMBRE_HOJA = "Herramientas"

# Claves en los ajustes de cada ventana
K_GRUPO = "barra_herramientas_grupo"
K_PESTANA = "barra_herramientas_pestana"
K_VISTA = "barra_herramientas_vista"
K_OCULTA = "barra_herramientas_oculta"


def ajustes():
    return sublime.load_settings(AJUSTES)


def pestanas():
    return ajustes().get("pestanas", []) or []


# --------------------------------------------------------------------------
# Disposición de la ventana: una fila arriba para la barra
# --------------------------------------------------------------------------

def grupo_barra(window):
    """Índice del grupo de la barra, o None si la ventana no la tiene."""
    g = window.settings().get(K_GRUPO)
    if g is None:
        return None
    layout = window.get_layout()
    cells = layout["cells"]
    ancho = len(layout["cols"]) - 1
    if g < len(cells) and list(cells[g]) == [0, 0, ancho, 1] and len(layout["rows"]) > 2:
        return g
    window.settings().erase(K_GRUPO)
    return None


def fraccion_altura(window):
    """Altura de la fila de la barra, como fracción de la ventana."""
    px = ajustes().get("altura", 110)
    vista = window.active_view()
    if vista is not None:
        alto_vista = vista.viewport_extent()[1]
        layout = window.get_layout()
        g = window.get_view_index(vista)[0]
        if 0 <= g < len(layout["cells"]):
            c = layout["cells"][g]
            fila = layout["rows"][c[3]] - layout["rows"][c[1]]
            if fila > 0 and alto_vista > 0:
                # sumamos la barra de pestañas del grupo (~30 px)
                total = (alto_vista + 30) / fila
                return min(max(px / total, 0.05), 0.4)
    return 0.12


def anadir_fila(window):
    layout = window.get_layout()
    rows, cols, cells = layout["rows"], layout["cols"], layout["cells"]
    h = fraccion_altura(window)
    nuevas_filas = [0.0, h] + [h + r * (1 - h) for r in rows[1:]]
    nuevas_celdas = [[c[0], c[1] + 1, c[2], c[3] + 1] for c in cells]
    nuevas_celdas.append([0, 0, len(cols) - 1, 1])
    window.set_layout({"cols": cols, "rows": nuevas_filas, "cells": nuevas_celdas})
    return len(nuevas_celdas) - 1


def quitar_fila(window, g):
    layout = window.get_layout()
    rows, cols, cells = layout["rows"], layout["cols"], layout["cells"]
    h = rows[1]
    nuevas_filas = [0.0] + [(r - h) / (1 - h) for r in rows[2:]]
    nuevas_celdas = [[c[0], c[1] - 1, c[2], c[3] - 1] for i, c in enumerate(cells) if i != g]
    window.set_layout({"cols": cols, "rows": nuevas_filas, "cells": nuevas_celdas})


def hoja_barra(window, g):
    for hoja in window.sheets_in_group(g):
        if isinstance(hoja, sublime.HtmlSheet):
            return hoja
    return None


# --------------------------------------------------------------------------
# HTML de la barra
# --------------------------------------------------------------------------

CSS = """
body {
    margin: 0;
    padding: 0.2rem 0.4rem;
    font-size: 0.95rem;
}
.pestanas {
    padding-bottom: 0.25rem;
    border-bottom: 1px solid color(var(--foreground) alpha(0.15));
}
.pestana {
    color: color(var(--foreground) alpha(0.7));
    text-decoration: none;
    padding: 0.15rem 0.6rem;
    border-radius: 0.25rem;
}
.pestana.activa {
    color: var(--background);
    background-color: var(--accent);
    font-weight: bold;
}
.herramientas {
    padding-top: 0.35rem;
}
.boton {
    color: var(--foreground);
    text-decoration: none;
    padding: 0.15rem 0.5rem;
    border-radius: 0.25rem;
    background-color: color(var(--foreground) alpha(0.08));
}
.separador {
    color: color(var(--foreground) alpha(0.3));
    padding: 0 0.2rem;
}
"""


def href(**args):
    # Comillas simples en el atributo y JSON (comillas dobles) dentro, sin escapar:
    # los argumentos son solo números y palabras fijas
    return "subl:barra_herramientas " + json.dumps(args)


def generar_html(window):
    lista = pestanas()
    activa = window.settings().get(K_PESTANA, 0)
    if not 0 <= activa < len(lista):
        activa = 0

    partes = ["<body id='barra-herramientas'><style>", CSS, "</style>", "<div class='pestanas'>"]
    for i, p in enumerate(lista):
        clase = "pestana activa" if i == activa else "pestana"
        partes.append("<a class='{}' href='{}'>{}</a> ".format(
            clase, href(accion="pestana", indice=i),
            html.escape(p.get("nombre", "?"))))
    partes.append("</div><div class='herramientas'>")

    if lista:
        for j, h in enumerate(lista[activa].get("herramientas", [])):
            if h == "-" or (isinstance(h, dict) and h.get("texto") == "-"):
                partes.append("<span class='separador'>│</span> ")
                continue
            titulo = h.get("descripcion", "")
            partes.append("<a class='boton' href='{}' title='{}'>{}</a> ".format(
                href(accion="ejecutar", pestana=activa, indice=j),
                html.escape(titulo, quote=True),
                html.escape(h.get("texto", "?"))))
    partes.append("</div></body>")
    return "".join(partes)


def pintar(window):
    g = grupo_barra(window)
    if g is None:
        return
    contenido = generar_html(window)
    hoja = hoja_barra(window, g)
    if hoja is None:
        activa = window.active_sheet()
        window.new_html_sheet(NOMBRE_HOJA, contenido, group=g)
        if activa is not None:
            window.focus_sheet(activa)
    else:
        hoja.set_contents(contenido)


# --------------------------------------------------------------------------
# Mostrar / ocultar
# --------------------------------------------------------------------------

def mostrar(window):
    if grupo_barra(window) is None:
        activa = window.active_sheet()
        window.settings().set(K_GRUPO, anadir_fila(window))
        if activa is not None:
            window.focus_sheet(activa)
    window.settings().erase(K_OCULTA)
    pintar(window)


def ocultar(window):
    g = grupo_barra(window)
    if g is None:
        return
    hoja = hoja_barra(window, g)
    if hoja is not None:
        hoja.close()
    quitar_fila(window, g)
    window.settings().erase(K_GRUPO)
    window.settings().set(K_OCULTA, True)


def preparar_ventana(window):
    """Al arrancar o abrir ventana: mostrar la barra si toca."""
    if grupo_barra(window) is not None:
        pintar(window)  # la fila se restauró con la sesión; falta la hoja
    elif ajustes().get("mostrar_al_iniciar", True) and not window.settings().get(K_OCULTA):
        mostrar(window)


def vista_destino(window):
    """Último archivo en el que estaba el usuario (fuera de la barra)."""
    g_barra = grupo_barra(window)
    vid = window.settings().get(K_VISTA)
    for v in window.views():
        if v.id() == vid:
            return v
    for g in range(window.num_groups()):
        if g != g_barra:
            v = window.active_view_in_group(g)
            if v is not None:
                return v
    return None


# --------------------------------------------------------------------------
# Comandos y eventos
# --------------------------------------------------------------------------

class BarraHerramientasCommand(sublime_plugin.WindowCommand):
    """accion: alternar | mostrar | ocultar | pestana (indice) | ejecutar (pestana, indice)"""

    def run(self, accion="alternar", indice=0, pestana=0):
        w = self.window
        if accion == "alternar":
            if grupo_barra(w) is None:
                mostrar(w)
            else:
                ocultar(w)
        elif accion == "mostrar":
            mostrar(w)
        elif accion == "ocultar":
            ocultar(w)
        elif accion == "pestana":
            w.settings().set(K_PESTANA, indice)
            pintar(w)
            self.volver_al_archivo()
        elif accion == "ejecutar":
            self.ejecutar(pestana, indice)

    def volver_al_archivo(self):
        v = vista_destino(self.window)
        if v is not None:
            self.window.focus_view(v)
        return v

    def ejecutar(self, pestana, indice):
        try:
            h = pestanas()[pestana]["herramientas"][indice]
        except (IndexError, KeyError, TypeError):
            return
        comando = h.get("comando")
        if not comando:
            return
        self.volver_al_archivo()
        # window.run_command pasa los comandos de texto al archivo activo
        self.window.run_command(comando, h.get("args") or {})

    def is_checked(self, accion="alternar", **kwargs):
        return accion == "alternar" and grupo_barra(self.window) is not None

    def description(self, accion="alternar", **kwargs):
        return "Barra de herramientas"


class BarraHerramientasEventos(sublime_plugin.EventListener):

    def on_activated(self, view):
        w = view.window()
        if w is None or view.settings().get("is_widget"):
            return
        g_barra = grupo_barra(w)
        if g_barra is None:
            return
        g, _ = w.get_view_index(view)
        if g == g_barra:
            # Un archivo se ha abierto en la fila de la barra: llevarlo al editor
            sublime.set_timeout(lambda: self.mover_al_editor(w, view, g_barra), 0)
        else:
            w.settings().set(K_VISTA, view.id())

    @staticmethod
    def mover_al_editor(w, view, g_barra):
        destino = 0 if g_barra != 0 else 1
        anterior = w.settings().get(K_VISTA)
        for v in w.views():
            if v.id() == anterior:
                destino = w.get_view_index(v)[0]
                break
        w.set_view_index(view, destino, len(w.views_in_group(destino)))
        w.focus_view(view)

    def on_new_window(self, window):
        sublime.set_timeout(lambda: preparar_ventana(window), 100)


def al_cambiar_ajustes():
    for w in sublime.windows():
        pintar(w)


def plugin_loaded():
    ajustes().clear_on_change("barra_herramientas")
    ajustes().add_on_change("barra_herramientas", al_cambiar_ajustes)
    # Esperar a que Sublime restaure las ventanas de la sesión
    sublime.set_timeout(lambda: [preparar_ventana(w) for w in sublime.windows()], 500)


def plugin_unloaded():
    ajustes().clear_on_change("barra_herramientas")
