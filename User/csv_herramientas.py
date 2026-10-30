"""
Utilidades para CSV que complementan a Rainbow CSV:

- csv_cambiar_separador: cambia el separador del archivo (coma, punto y coma,
  tabulador, barra vertical) respetando los campos entre comillas. Útil para
  los CSV de Excel en español, que usan punto y coma.
- csv_a_json: abre en una pestaña nueva el CSV convertido a JSON (una lista de
  objetos, usando la primera fila como nombres de columna).

Si hay texto seleccionado, trabajan solo con la selección.
"""

import csv
import io
import json

import sublime
import sublime_plugin

SEPARADORES = [
    (",", "Coma  ,"),
    (";", "Punto y coma  ;"),
    ("\t", "Tabulador"),
    ("|", "Barra vertical  |"),
]


def region_de_trabajo(view):
    sel = [r for r in view.sel() if not r.empty()]
    if len(sel) == 1:
        return sel[0]
    return sublime.Region(0, view.size())


def detectar_separador(texto):
    muestra = "\n".join(texto.splitlines()[:50])
    try:
        return csv.Sniffer().sniff(muestra, delimiters=",;\t|").delimiter
    except csv.Error:
        primera = texto.splitlines()[0] if texto else ""
        return max(",;\t|", key=primera.count)


def salto_de_linea(view):
    return {"windows": "\r\n", "cr": "\r"}.get(view.line_endings().lower(), "\n")


def leer_filas(texto):
    sep = detectar_separador(texto)
    return sep, list(csv.reader(io.StringIO(texto, newline=""), delimiter=sep))


class CsvCambiarSeparadorCommand(sublime_plugin.TextCommand):

    def run(self, edit, separador=None):
        if separador is None:
            self.view.window().show_quick_panel(
                [nombre for _, nombre in SEPARADORES],
                lambda i: i >= 0 and self.view.run_command(
                    "csv_cambiar_separador", {"separador": SEPARADORES[i][0]}),
                placeholder="Nuevo separador",
            )
            return

        region = region_de_trabajo(self.view)
        texto = self.view.substr(region)
        if not texto.strip():
            return
        origen, filas = leer_filas(texto)
        if origen == separador:
            sublime.status_message("El archivo ya usa ese separador")
            return

        salida = io.StringIO(newline="")
        csv.writer(salida, delimiter=separador, lineterminator=salto_de_linea(self.view),
                   quoting=csv.QUOTE_MINIMAL).writerows(filas)
        nuevo = salida.getvalue()
        if not texto.endswith(("\n", "\r")):
            nuevo = nuevo.rstrip("\r\n")
        self.view.replace(edit, region, nuevo)
        sublime.status_message("Separador cambiado: {} filas".format(len(filas)))


class CsvAJsonCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        texto = self.view.substr(region_de_trabajo(self.view))
        if not texto.strip():
            return
        _, filas = leer_filas(texto)
        filas = [f for f in filas if any(c.strip() for c in f)]
        if not filas:
            return
        cabecera, datos = filas[0], filas[1:]
        objetos = []
        for fila in datos:
            obj = {}
            for i, valor in enumerate(fila):
                clave = cabecera[i] if i < len(cabecera) and cabecera[i] else "columna_{}".format(i + 1)
                obj[clave] = valor
            objetos.append(obj)

        resultado = json.dumps(objetos, indent=2, ensure_ascii=False) + "\n"
        nueva = self.view.window().new_file()
        nombre = self.view.file_name() or self.view.name() or "datos"
        nueva.set_name(nombre.replace("\\", "/").split("/")[-1].rsplit(".", 1)[0] + ".json")
        nueva.assign_syntax("Packages/JSON/JSON.sublime-syntax")
        nueva.run_command("append", {"characters": resultado})
        sublime.status_message("{} filas convertidas a JSON".format(len(objetos)))
