#!/usr/bin/env python3
"""
Traduce al español los menús de Sublime Text 4 (macOS).

Cómo funciona:
- Lee los menús originales del paquete interno "Default.sublime-package".
- Sustituye solo los textos visibles ("caption"); no toca comandos ni atajos.
- A las opciones que no traen texto (Copiar, Pegar, Deshacer, Mostrar barra
  lateral…) les añade uno en español, porque si no Sublime las muestra en inglés.
- Diccionario revisado con los menús reales de Sublime Text 4 (builds 4192 a 4215).
- Guarda las copias traducidas en tu carpeta de usuario de Sublime Text
  (Packages/Default), que Sublime usa por encima de las originales.
- No necesita permisos de administrador.

Uso:
    python3 traducir_sublime.py             # aplicar traducción
    python3 traducir_sublime.py --restaurar # volver al inglés

Tras una actualización de Sublime Text, vuelve a ejecutarlo para que los
menús recojan las opciones nuevas.
"""

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path

MANIFIESTO = "_traduccion_es.txt"

PAQUETES_CANDIDATOS = [
    "/Applications/Sublime Text.app/Contents/MacOS/Packages/Default.sublime-package",
    "~/Applications/Sublime Text.app/Contents/MacOS/Packages/Default.sublime-package",
]

USUARIO_CANDIDATOS = [
    "~/Library/Application Support/Sublime Text/Packages",
    "~/Library/Application Support/Sublime Text 3/Packages",
]

# --------------------------------------------------------------------------
# Diccionario (clave en inglés SIN '&' y SIN puntos suspensivos finales)
# --------------------------------------------------------------------------
T = {
    # Menús principales
    "File": "Archivo", "Edit": "Editar", "Selection": "Selección",
    "Find": "Buscar", "View": "Ver", "Goto": "Ir", "Tools": "Herramientas",
    "Project": "Proyecto", "Preferences": "Preferencias", "Settings": "Ajustes",
    "Help": "Ayuda", "Window": "Ventana",

    # Menú de la app (macOS)
    "About Sublime Text": "Acerca de Sublime Text",
    "Check for Updates": "Buscar actualizaciones",
    "Services": "Servicios",
    "Hide Sublime Text": "Ocultar Sublime Text",
    "Hide Others": "Ocultar otros",
    "Show All": "Mostrar todo",
    "Quit Sublime Text": "Salir de Sublime Text",
    "Quit": "Salir", "Exit": "Salir",

    # Archivo
    "New File": "Nuevo archivo", "New Window": "Nueva ventana",
    "Open": "Abrir", "Open File": "Abrir archivo", "Open Folder": "Abrir carpeta",
    "Open Recent": "Abrir reciente", "Reopen Closed File": "Reabrir archivo cerrado",
    "Clear Items": "Borrar lista", "Reopen with Encoding": "Reabrir con codificación",
    "New View into File": "Nueva vista del archivo",
    "Save": "Guardar", "Save with Encoding": "Guardar con codificación",
    "Save As": "Guardar como", "Save Copy As": "Guardar una copia como",
    "Save All": "Guardar todo", "Revert File": "Revertir archivo",
    "Close File": "Cerrar archivo", "Close Window": "Cerrar ventana",
    "Close All Files": "Cerrar todos los archivos", "Close Folder": "Cerrar carpeta",
    "Close": "Cerrar", "Close All": "Cerrar todo",
    "Close Tab": "Cerrar pestaña", "Close Other Tabs": "Cerrar las demás pestañas",
    "Close Tabs to the Right": "Cerrar pestañas a la derecha",
    "Close Unmodified Tabs": "Cerrar pestañas sin cambios",
    "Close Unmodified Tabs to the Right": "Cerrar pestañas sin cambios a la derecha",
    "Close Deleted Files": "Cerrar archivos eliminados",
    "Encoding": "Codificación",
    "Copy File Path": "Copiar ruta del archivo",
    "Copy File Name": "Copiar nombre del archivo",
    "Copy Path": "Copiar ruta", "Copy Name": "Copiar nombre",
    "Reveal in Finder": "Mostrar en Finder",
    "Reveal in Side Bar": "Mostrar en la barra lateral",
    "Open Containing Folder": "Abrir carpeta contenedora",
    "Show in Finder": "Mostrar en Finder",

    # Editar
    "Undo": "Deshacer", "Redo": "Rehacer", "Repeat": "Repetir",
    "Undo Selection": "Deshacer selección", "Redo Selection": "Rehacer selección",
    "Soft Undo": "Deshacer suave", "Soft Redo": "Rehacer suave",
    "Copy": "Copiar", "Cut": "Cortar", "Paste": "Pegar",
    "Paste and Indent": "Pegar con sangría", "Paste from History": "Pegar desde el historial",
    "Copy as HTML": "Copiar como HTML", "Delete": "Eliminar",
    "Line": "Línea", "Indent": "Aumentar sangría", "Unindent": "Reducir sangría",
    "Reindent": "Rehacer sangría", "Swap Line Up": "Subir línea",
    "Swap Line Down": "Bajar línea", "Duplicate Line": "Duplicar línea",
    "Delete Line": "Eliminar línea", "Join Lines": "Unir líneas",
    "Insert Line Before": "Insertar línea antes", "Insert Line After": "Insertar línea después",
    "Comment": "Comentario", "Toggle Comment": "Comentar/descomentar",
    "Toggle Block Comment": "Comentar/descomentar bloque",
    "Text": "Texto", "Delete Word Forward": "Borrar palabra siguiente",
    "Delete Word Backward": "Borrar palabra anterior",
    "Delete to End": "Borrar hasta el final", "Delete to Beginning": "Borrar hasta el principio",
    "Delete Line Contents": "Borrar contenido de la línea",
    "Transpose": "Transponer",
    "Tag": "Etiqueta", "Close Tag": "Cerrar etiqueta",
    "Expand Selection to Tag": "Expandir selección a la etiqueta",
    "Wrap Selection With Tag": "Envolver selección con etiqueta",
    "Mark": "Marca", "Set Mark": "Poner marca", "Select to Mark": "Seleccionar hasta la marca",
    "Delete to Mark": "Borrar hasta la marca", "Swap with Mark": "Intercambiar con la marca",
    "Clear Mark": "Quitar marca", "Yank": "Recuperar (yank)",
    "Code Folding": "Plegado de código", "Fold": "Plegar", "Unfold": "Desplegar",
    "Fold All": "Plegar todo", "Unfold All": "Desplegar todo",
    "Fold Tag Attributes": "Plegar atributos de etiquetas",
    "Convert Case": "Mayúsculas/minúsculas", "Title Case": "Tipo Título",
    "Upper Case": "MAYÚSCULAS", "Lower Case": "minúsculas",
    "Swap Case": "Invertir mayúsculas/minúsculas",
    "Wrap": "Ajustar", "Wrap Paragraph at Ruler": "Ajustar párrafo a la regla",
    "Show Completions": "Mostrar autocompletado",
    "Sort Lines": "Ordenar líneas",
    "Sort Lines (Case Sensitive)": "Ordenar líneas (distinguir mayúsculas)",
    "Permute Lines": "Permutar líneas", "Permute Selections": "Permutar selecciones",
    "Reverse": "Invertir orden", "Unique": "Eliminar duplicados", "Shuffle": "Mezclar",
    "Sort Selections": "Ordenar selecciones",
    "Start Dictation": "Iniciar dictado", "Emoji & Symbols": "Emoji y símbolos",

    # Selección
    "Split into Lines": "Dividir en líneas",
    "Add Previous Line": "Añadir línea anterior", "Add Next Line": "Añadir línea siguiente",
    "Single Selection": "Selección única", "Invert Selection": "Invertir selección",
    "Select All": "Seleccionar todo",
    "Expand Selection": "Expandir selección",
    "Expand Selection to Line": "Expandir selección a la línea",
    "Expand Selection to Word": "Expandir selección a la palabra",
    "Expand Selection to Paragraph": "Expandir selección al párrafo",
    "Expand Selection to Scope": "Expandir selección al ámbito",
    "Expand Selection to Brackets": "Expandir selección a los corchetes",
    "Expand Selection to Indentation": "Expandir selección a la sangría",
    "Expand Selection to Quotes": "Expandir selección a las comillas",

    # Buscar
    "Find Next": "Buscar siguiente", "Find Previous": "Buscar anterior",
    "Find All": "Buscar todo", "Incremental Find": "Búsqueda incremental",
    "Replace": "Reemplazar", "Replace Next": "Reemplazar siguiente",
    "Replace All": "Reemplazar todo",
    "Quick Find": "Búsqueda rápida", "Quick Find All": "Búsqueda rápida (todas)",
    "Quick Add Next": "Añadir siguiente coincidencia",
    "Quick Skip Next": "Saltar siguiente coincidencia",
    "Use Selection for Find": "Usar selección para buscar",
    "Use Selection for Replace": "Usar selección para reemplazar",
    "Find in Files": "Buscar en archivos", "Find in Folder": "Buscar en la carpeta",
    "Find in Project": "Buscar en el proyecto",
    "Find Results": "Resultados de búsqueda",
    "Show Results Panel": "Mostrar panel de resultados",
    "Next Result": "Resultado siguiente", "Previous Result": "Resultado anterior",

    # Ver
    "Side Bar": "Barra lateral", "Show Side Bar": "Mostrar barra lateral",
    "Hide Side Bar": "Ocultar barra lateral",
    "Show Open Files": "Mostrar archivos abiertos", "Hide Open Files": "Ocultar archivos abiertos",
    "Show Minimap": "Mostrar minimapa", "Hide Minimap": "Ocultar minimapa",
    "Show Tabs": "Mostrar pestañas", "Hide Tabs": "Ocultar pestañas",
    "Show Status Bar": "Mostrar barra de estado", "Hide Status Bar": "Ocultar barra de estado",
    "Show Menu": "Mostrar menú", "Hide Menu": "Ocultar menú",
    "Show Console": "Mostrar consola", "Hide Console": "Ocultar consola",
    "Enter Full Screen": "Pantalla completa", "Exit Full Screen": "Salir de pantalla completa",
    "Enter Distraction Free Mode": "Modo sin distracciones",
    "Exit Distraction Free Mode": "Salir del modo sin distracciones",
    "Layout": "Distribución", "Single": "Única",
    "Groups": "Grupos", "Focus Group": "Activar grupo", "Move File To Group": "Mover archivo al grupo",
    "New Group": "Nuevo grupo", "Close Group": "Cerrar grupo",
    "Next": "Siguiente", "Previous": "Anterior",
    "Syntax": "Sintaxis", "Open all with current extension as": "Abrir todos con esta extensión como",
    "Indentation": "Sangría", "Indent Using Spaces": "Sangrar con espacios",
    "Guess Settings From Buffer": "Deducir ajustes del contenido",
    "Convert Indentation to Spaces": "Convertir sangría a espacios",
    "Convert Indentation to Tabs": "Convertir sangría a tabulaciones",
    "Line Endings": "Finales de línea",
    "Word Wrap": "Ajuste de línea", "Word Wrap Column": "Columna de ajuste",
    "Automatic": "Automático", "Ruler": "Regla", "None": "Ninguna",
    "Spell Check": "Revisión ortográfica",
    "Next Misspelling": "Siguiente error ortográfico",
    "Prev Misspelling": "Error ortográfico anterior",
    "Dictionary": "Diccionario",

    # Ir
    "Goto Anything": "Ir a cualquier elemento", "Goto Symbol": "Ir a símbolo",
    "Goto Symbol in Project": "Ir a símbolo en el proyecto",
    "Goto Definition": "Ir a la definición", "Goto Reference": "Ir a referencia",
    "Goto Line": "Ir a la línea",
    "Jump Back": "Volver atrás", "Jump Forward": "Ir adelante",
    "Switch File": "Cambiar de archivo", "Next File": "Archivo siguiente",
    "Previous File": "Archivo anterior",
    "Next File in Stack": "Archivo siguiente (recientes)",
    "Previous File in Stack": "Archivo anterior (recientes)",
    "Switch Header/Implementation": "Alternar cabecera/implementación",
    "Scroll": "Desplazamiento", "Scroll to Selection": "Desplazar a la selección",
    "Line Up": "Línea arriba", "Line Down": "Línea abajo",
    "Bookmarks": "Marcadores", "Toggle Bookmark": "Poner/quitar marcador",
    "Next Bookmark": "Marcador siguiente", "Prev Bookmark": "Marcador anterior",
    "Clear Bookmarks": "Borrar marcadores",
    "Select All Bookmarks": "Seleccionar todos los marcadores",
    "Jump to Matching Bracket": "Ir al corchete correspondiente",
    "Next Modification": "Siguiente modificación",
    "Previous Modification": "Modificación anterior",

    # Herramientas
    "Command Palette": "Paleta de comandos", "Snippets": "Fragmentos",
    "Build System": "Sistema de compilación", "Build": "Compilar",
    "Build With": "Compilar con", "Cancel Build": "Cancelar compilación",
    "Build Results": "Resultados de compilación",
    "Show Build Results": "Mostrar resultados de compilación",
    "Save All on Build": "Guardar todo al compilar",
    "New Build System": "Nuevo sistema de compilación",
    "Record Macro": "Grabar macro", "Stop Recording Macro": "Detener grabación de macro",
    "Playback Macro": "Reproducir macro", "Save Macro": "Guardar macro",
    "Macros": "Macros", "Developer": "Desarrollador",
    "New Plugin": "Nuevo plugin", "New Snippet": "Nuevo fragmento",
    "New Syntax": "Nueva sintaxis", "Show Scope Name": "Mostrar nombre de ámbito",
    "Install Package Control": "Instalar Package Control",

    # Proyecto
    "Open Project": "Abrir proyecto", "Switch Project": "Cambiar de proyecto",
    "Quick Switch Project": "Cambio rápido de proyecto",
    "Save Project As": "Guardar proyecto como", "Close Project": "Cerrar proyecto",
    "Edit Project": "Editar proyecto",
    "New Workspace for Project": "Nuevo espacio de trabajo para el proyecto",
    "Save Workspace As": "Guardar espacio de trabajo como",
    "Add Folder to Project": "Añadir carpeta al proyecto",
    "Remove all Folders from Project": "Quitar todas las carpetas del proyecto",
    "Remove Folder from Project": "Quitar carpeta del proyecto",
    "Refresh Folders": "Actualizar carpetas",

    # Barra lateral
    "Rename": "Renombrar", "Delete File": "Eliminar archivo",
    "New Folder": "Nueva carpeta", "Delete Folder": "Eliminar carpeta",
    "Duplicate": "Duplicar", "Open Git Repository": "Abrir repositorio Git",
    "File History": "Historial del archivo", "Folder History": "Historial de la carpeta",
    "Blame File": "Autoría del archivo (blame)",

    # Preferencias / Ajustes
    "Browse Packages": "Explorar paquetes",
    "Settings – Syntax Specific": "Ajustes – por sintaxis",
    "Settings - Syntax Specific": "Ajustes - por sintaxis",
    "Settings – Distraction Free": "Ajustes – sin distracciones",
    "Settings - Distraction Free": "Ajustes - sin distracciones",
    "Key Bindings": "Atajos de teclado", "Mouse Bindings": "Atajos del ratón",
    "Color Scheme": "Esquema de colores", "Select Color Scheme": "Elegir esquema de colores",
    "Customize Color Scheme": "Personalizar esquema de colores",
    "Theme": "Tema", "Select Theme": "Elegir tema", "Customize Theme": "Personalizar tema",
    "Font": "Fuente", "Larger": "Más grande", "Smaller": "Más pequeña", "Reset": "Restablecer",
    "Package Settings": "Ajustes de paquetes",

    # Ayuda
    "Documentation": "Documentación", "Changelog": "Registro de cambios",
    "Indexing Status": "Estado de la indexación",
    "Purchase License": "Comprar licencia", "Upgrade License": "Mejorar licencia",
    "Enter License": "Introducir licencia", "Remove License": "Quitar licencia",
    "Search": "Buscar",

    # Ventana
    "Minimize": "Minimizar", "Zoom": "Zoom", "Bring All to Front": "Traer todo al frente",

    # Añadidos tras revisar los menús reales de Sublime Text 4 (builds 4192-4215)
    "Print": "Imprimir", "Remove Deleted": "Quitar elementos eliminados",
    "Reopen File as Image": "Reabrir archivo como imagen",
    "Reopen File as Text": "Reabrir archivo como texto",
    "Set Encoding": "Establecer codificación",
    "Expand Selection to Block": "Expandir selección al bloque",
    "Expand Selection to Line Upward": "Expandir selección a la línea hacia arriba",
    "Wrap Paragraph": "Ajustar párrafo",
    "Sort": "Ordenar", "Sort (Case Sensitive)": "Ordenar (distinguir mayúsculas)",
    "Cancel Find in Files": "Cancelar búsqueda en archivos",
    "Move File to Group": "Mover archivo al grupo",
    "Move File to New Group": "Mover archivo a un grupo nuevo",
    "Split View": "Dividir vista",
    "Tab Selection": "Selección de pestañas",
    "Select to Left": "Seleccionar hacia la izquierda",
    "Select to Right": "Seleccionar hacia la derecha",
    "Unselect Current": "Deseleccionar la actual",
    "Unselect Others": "Deseleccionar las demás",
    "Unselect to Left": "Deseleccionar hacia la izquierda",
    "Unselect to Right": "Deseleccionar hacia la derecha",
    "Focus to Left": "Activar la de la izquierda",
    "Focus to Right": "Activar la de la derecha",
    "Close Selected Tabs": "Cerrar pestañas seleccionadas",
    "Close Unselected Tabs": "Cerrar pestañas no seleccionadas",
    "Close Tabs Below": "Cerrar pestañas de abajo",
    "Close Unmodified Tabs Below": "Cerrar pestañas sin cambios de abajo",
    "Close Tabs With Deleted Files": "Cerrar pestañas de archivos eliminados",
    "Choose": "Elegir", "Reset Size": "Restablecer tamaño",
    "Enable Package Control": "Activar Package Control",
    "View Package File": "Ver archivo de un paquete",
    "Licenses and Attribution": "Licencias y atribuciones",
    "Report a Bug": "Informar de un error",
    "Open Terminal Here": "Abrir terminal aquí",
    "Open in Browser": "Abrir en el navegador",
    "Line History": "Historial de la línea",
    "Revert Diff Hunk": "Revertir bloque de cambios",
    "Reveal Link Source": "Mostrar origen del enlace",

    # Buscar en archivos (menú del botón "…" junto a "Where")
    "Clear": "Limpiar", "Add Folder": "Añadir carpeta",
    "Add Open Folders": "Añadir carpetas abiertas", "Add Open Files": "Añadir archivos abiertos",
    "Add Current File": "Añadir archivo actual",
    "Add Include Filter": "Añadir filtro de inclusión",
    "Add Exclude Filter": "Añadir filtro de exclusión",
    "Add Project Filters": "Añadir filtros del proyecto",

    # Finales de línea
    "Windows Line Endings (CRLF)": "Finales de línea Windows (CRLF)",
    "Unix Line Endings (LF)": "Finales de línea Unix (LF)",
    "Mac OS 9 Line Endings (CR)": "Finales de línea Mac OS 9 (CR)",
}

# Textos que se dejan igual a propósito (nombres propios, formatos, números)
NO_TRADUCIR = {
    "Windows", "Unix", "Mac OS 9", "Twitter", "Hexadecimal", "DOS (CP 437)",
    "UTF-8", "UTF-16 LE", "UTF-16 BE",
    "snake_case", "kebab-case", "lowerCamelCase", "UpperCamelCase",
}

# Regiones de las codificaciones: "Western (Windows 1252)" -> "Occidental (Windows 1252)"
REGIONES = {
    "Western": "Occidental", "Central European": "Centroeuropeo", "Cyrillic": "Cirílico",
    "Greek": "Griego", "Turkish": "Turco", "Hebrew": "Hebreo", "Arabic": "Árabe",
    "Baltic": "Báltico", "Vietnamese": "Vietnamita", "Nordic": "Nórdico",
    "Celtic": "Celta", "Romanian": "Rumano", "Estonian": "Estonio", "Chinese": "Chino",
    "Japanese": "Japonés", "Korean": "Coreano", "Thai": "Tailandés",
}

# Opciones que en el menú original no tienen texto: Sublime les pone el nombre
# del comando en inglés. Aquí se les da un texto fijo en español.
# Clave: comando, o (comando, argumento, valor) cuando depende de los argumentos.
COMANDOS = {
    "undo": "Deshacer", "redo_or_repeat": "Rehacer", "redo": "Rehacer",
    "soft_undo": "Deshacer suave", "soft_redo": "Rehacer suave",
    "copy": "Copiar", "cut": "Cortar", "paste": "Pegar",
    "paste_and_indent": "Pegar con sangría", "select_all": "Seleccionar todo",
    "indent": "Aumentar sangría", "unindent": "Reducir sangría", "reindent": "Rehacer sangría",
    "swap_line_up": "Subir línea", "swap_line_down": "Bajar línea",
    "duplicate_line": "Duplicar línea", "join_lines": "Unir líneas",
    "transpose": "Transponer", "close_tag": "Cerrar etiqueta",
    "set_mark": "Poner marca", "yank": "Recuperar (yank)",
    "fold": "Plegar", "unfold": "Desplegar",
    "single_selection": "Selección única",
    "find_next": "Buscar siguiente", "replace_next": "Reemplazar siguiente",
    "next_result": "Resultado siguiente",
    "toggle_bookmark": "Poner/quitar marcador", "next_bookmark": "Marcador siguiente",
    "prev_bookmark": "Marcador anterior", "clear_bookmarks": "Borrar marcadores",
    "select_all_bookmarks": "Seleccionar todos los marcadores",
    "next_misspelling": "Siguiente error ortográfico",
    "prev_misspelling": "Error ortográfico anterior",
    "revert_hunk": "Revertir bloque de cambios",
    "revert_modification": "Revertir modificación",
    "toggle_inline_diff": "Mostrar/ocultar diferencias en línea",
    "toggle_side_bar": "Mostrar/ocultar barra lateral",
    "toggle_show_open_files": "Mostrar/ocultar archivos abiertos",
    "toggle_minimap": "Mostrar/ocultar minimapa",
    "toggle_tabs": "Mostrar/ocultar pestañas",
    "toggle_status_bar": "Mostrar/ocultar barra de estado",
    "toggle_menu": "Mostrar/ocultar menú",
    "toggle_full_screen": "Pantalla completa (activar/desactivar)",
    "toggle_distraction_free": "Modo sin distracciones (activar/desactivar)",
    "toggle_record_macro": "Grabar/detener macro",
    ("show_panel", "panel", "console"): "Mostrar/ocultar consola",
    ("show_panel", "panel", "output.find_results"): "Mostrar panel de resultados",
    "build": "Compilar", "show_scope_name": "Mostrar nombre de ámbito",
    "profile_plugins": "Analizar rendimiento de plugins",
    "convert_syntax": "Convertir a .sublime-syntax",
    "purchase_license": "Comprar licencia", "upgrade_license": "Mejorar licencia",
    "remove_license": "Quitar licencia",
}

# Textos con números u otras partes variables
REGLAS = [
    (r"^Tab Width: (\d+)$", r"Ancho de tabulación: \1"),
    (r"^Columns: (\d+)$", r"Columnas: \1"),
    (r"^Rows: (\d+)$", r"Filas: \1"),
    (r"^Grid: (\d+)$", r"Cuadrícula: \1"),
    (r"^Max Columns: (\d+)$", r"Máximo de columnas: \1"),
    (r"^Wrap [Pp]aragraph at (\d+) characters$", r"Ajustar párrafo a \1 caracteres"),
    (r"^Ruler: (\d+)$", r"Regla: \1"),
    (r"^Group (\d+)$", r"Grupo \1"),
    (r"^Fold Level (\d+)$", r"Plegar nivel \1"),
    (r"^Focus Selected Tab (\d+)$", r"Activar pestaña seleccionada \1"),
    (r"^(UTF-\d+(?: [LB]E)?) with BOM$", r"\1 con BOM"),
    (r"^\d+$", r"\g<0>"),
]

SUFIJOS = ("…", "...")
RE_REGION = re.compile(r"^(%s) (\(.+\))$" % "|".join(map(re.escape, REGIONES)))


def traducir_texto(original, sin_traducir):
    texto = original.replace("&", "")
    sufijo = ""
    for s in SUFIJOS:
        if texto.endswith(s):
            texto, sufijo = texto[: -len(s)], s
            break
    if texto in T:
        return T[texto] + sufijo
    if texto in NO_TRADUCIR:
        return texto + sufijo
    m = RE_REGION.match(texto)
    if m:
        return f"{REGIONES[m.group(1)]} {m.group(2)}" + sufijo
    for patron, reemplazo in REGLAS:
        if re.match(patron, texto):
            return re.sub(patron, reemplazo, texto) + sufijo
    if texto.strip() and texto != "-":
        sin_traducir.add(original)
    return original


def texto_comando(item):
    """Texto en español para una opción sin "caption", o None si no se conoce."""
    cmd = item.get("command")
    if not cmd or cmd.startswith("$"):
        return None  # listas dinámicas (sintaxis, macros, archivos recientes…)
    args = item.get("args") or {}
    for clave, valor in COMANDOS.items():
        if isinstance(clave, tuple) and clave[0] == cmd and args.get(clave[1]) == clave[2]:
            return valor
    return COMANDOS.get(cmd)


def quitar_comentarios(texto):
    """Convierte el JSON de Sublime (con comentarios y comas finales) en JSON estándar."""
    salida, i, n, en_cadena = [], 0, len(texto), False
    while i < n:
        c = texto[i]
        if en_cadena:
            salida.append(c)
            if c == "\\" and i + 1 < n:
                salida.append(texto[i + 1])
                i += 2
                continue
            if c == '"':
                en_cadena = False
        elif c == '"':
            en_cadena = True
            salida.append(c)
        elif texto.startswith("//", i):
            while i < n and texto[i] != "\n":
                i += 1
            continue
        elif texto.startswith("/*", i):
            fin = texto.find("*/", i + 2)
            i = n if fin == -1 else fin + 2
            continue
        else:
            salida.append(c)
        i += 1
    return re.sub(r",(\s*[\]}])", r"\1", "".join(salida))


def traducir_menu(contenido, sin_traducir):
    """Devuelve (menú traducido en JSON, número de textos cambiados)."""
    menu = json.loads(quitar_comentarios(contenido))
    contador = 0

    def recorrer(items):
        nonlocal contador
        for item in items:
            if not isinstance(item, dict):
                continue
            if "caption" in item:
                nuevo = traducir_texto(item["caption"], sin_traducir)
                if nuevo != item["caption"]:
                    item["caption"] = nuevo
                    contador += 1
            else:
                nuevo = texto_comando(item)
                if nuevo:
                    item["caption"] = nuevo
                    contador += 1
            recorrer(item.get("children", []))

    recorrer(menu)
    return json.dumps(menu, ensure_ascii=False, indent="\t") + "\n", contador


def buscar(candidatos, es_dir=False):
    for c in candidatos:
        p = Path(os.path.expanduser(c))
        if (p.is_dir() if es_dir else p.is_file()):
            return p
    return None


def aplicar(paquete, destino):
    destino.mkdir(parents=True, exist_ok=True)
    sin_traducir = set()
    escritos, total = [], 0
    with zipfile.ZipFile(paquete) as z:
        menus = [n for n in z.namelist() if n.endswith(".sublime-menu") and "/" not in n]
        for nombre in sorted(menus):
            original = z.read(nombre).decode("utf-8")
            traducido, n = traducir_menu(original, sin_traducir)
            if n == 0:
                continue
            ruta = destino / nombre
            if ruta.exists() and not (destino / MANIFIESTO).exists():
                ruta.rename(ruta.with_suffix(ruta.suffix + ".bak"))
            ruta.write_text(traducido, encoding="utf-8")
            escritos.append(nombre)
            total += n
    (destino / MANIFIESTO).write_text("\n".join(escritos) + "\n", encoding="utf-8")
    print(f"Menús traducidos: {len(escritos)} archivos, {total} textos.")
    print(f"Guardados en: {destino}")
    if sin_traducir:
        print(f"\nQuedan {len(sin_traducir)} textos en inglés (no estaban en el diccionario):")
        for t in sorted(sin_traducir):
            print(f"  - {t}")
    print("\nCierra y vuelve a abrir Sublime Text para ver los menús en español.")


def restaurar(destino):
    manifiesto = destino / MANIFIESTO
    if not manifiesto.exists():
        print("No hay traducción aplicada; no hay nada que restaurar.")
        return
    for nombre in manifiesto.read_text(encoding="utf-8").splitlines():
        if not nombre.strip():
            continue
        ruta = destino / nombre
        if ruta.exists():
            ruta.unlink()
        bak = ruta.with_suffix(ruta.suffix + ".bak")
        if bak.exists():
            bak.rename(ruta)
    manifiesto.unlink()
    try:
        destino.rmdir()  # solo si ha quedado vacía
    except OSError:
        pass
    print("Menús restaurados al inglés. Reinicia Sublime Text.")


def main():
    ap = argparse.ArgumentParser(description="Traduce los menús de Sublime Text al español.")
    ap.add_argument("--restaurar", action="store_true", help="volver a los menús en inglés")
    ap.add_argument("--paquete", help="ruta a Default.sublime-package (opcional)")
    ap.add_argument("--usuario", help="ruta a la carpeta Packages del usuario (opcional)")
    args = ap.parse_args()

    usuario = Path(os.path.expanduser(args.usuario)) if args.usuario else buscar(USUARIO_CANDIDATOS, es_dir=True)
    if not usuario:
        sys.exit("No encuentro la carpeta de usuario de Sublime Text. Abre Sublime una vez y vuelve a probar.")
    destino = usuario / "Default"

    if args.restaurar:
        restaurar(destino)
        return

    paquete = Path(os.path.expanduser(args.paquete)) if args.paquete else buscar(PAQUETES_CANDIDATOS)
    if not paquete:
        sys.exit("No encuentro Default.sublime-package. ¿Está Sublime Text en /Applications?")
    aplicar(paquete, destino)


if __name__ == "__main__":
    main()
