#!/usr/bin/env python3
"""
Descarga Package Control, los paquetes y sus librerías en la carpeta offline/,
para poder instalar sublime-tools en un Mac sin conexión a internet.

Se ejecuta en un equipo CON internet (necesita git y python3):

    python3 herramientas/preparar_offline.py

Genera:
    offline/Package Control.sublime-package   Package Control, listo para copiar
    offline/packages/*.sublime-package        un archivo por paquete (y por variante de build)
    offline/libraries/*                       librerías Python que piden algunos paquetes
    offline/repository.json                   repositorio local para Package Control

Package Control lee offline/repository.json (lo configura install.sh) y elige él
mismo la versión de cada paquete y librería que corresponde al build de Sublime
Text y a la arquitectura del Mac (Intel o Apple Silicon), igual que haría por
internet.

Las fuentes son las mismas que usa Package Control: el canal oficial de paquetes
(github.com/wbond/package_control_channel) y el de librerías
(github.com/packagecontrol/channel).
"""

import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "offline"

CANAL_PAQUETES = "https://github.com/wbond/package_control_channel"
CANAL_LIBRERIAS = "https://github.com/packagecontrol/channel"
PACKAGE_CONTROL = "https://github.com/sublimehq/package_control"

# Builds de Sublime Text 4 que se cubren (las variantes más antiguas se ignoran)
BUILD_MINIMO = 4107

# Plataformas del Mac (Apple Silicon e Intel)
PLATAFORMAS_MAC = {"*", "osx", "osx-arm64", "osx-x64"}

# Versiones de Python de los plugin hosts de Sublime Text 4
PYTHONS = ["3.3", "3.8", "3.13", "3.14"]

# Mismo mapa que usa Package Control para nombres antiguos de dependencias
NOMBRES_LIBRERIAS = {
    "pymdownx": "pymdown-extensions",
    "python-jinja2": "Jinja2",
    "python-markdown": "Markdown",
    "pyyaml": "PyYAML",
}


def log(msg):
    print(msg, flush=True)


def git(*args, cwd=None):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def descargar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "sublime-tools"})
    with urllib.request.urlopen(req, timeout=120) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def leer_json_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sublime-tools"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def clonar(url, destino):
    git("clone", "-q", "--depth", "1", url, str(destino))


# --------------------------------------------------------------------------
# Versiones y rangos de builds (misma lógica que Package Control)
# --------------------------------------------------------------------------

def version_de(texto):
    m = re.fullmatch(r"v?(\d+(?:\.\d+)*)", texto)
    return tuple(int(x) for x in m.group(1).split(".")) if m else None


def tags_remotos(url):
    salida = git("ls-remote", "--tags", url)
    return sorted({l.split("refs/tags/")[1].removesuffix("^{}") for l in salida.splitlines()})


def ultimo_tag(url, prefijo):
    """Último tag estable con el prefijo dado (True = sin prefijo)."""
    prefijo = "" if prefijo is True else prefijo
    candidatos = []
    for t in tags_remotos(url):
        if not t.startswith(prefijo):
            continue
        v = version_de(t[len(prefijo):])
        if v:
            candidatos.append((v, t))
    if not candidatos:
        raise RuntimeError("Sin tags con prefijo %r en %s" % (prefijo, url))
    v, t = max(candidatos)
    return t, ".".join(map(str, v))


def rango_cubre_st4(rango):
    """¿El rango 'sublime_text' incluye algún build >= BUILD_MINIMO?"""
    rango = rango.replace(" ", "")
    if rango == "*":
        return True
    if rango.startswith(">="):
        return True
    if rango.startswith(">"):
        return True
    if rango.startswith("<="):
        return int(rango[2:]) >= BUILD_MINIMO
    if rango.startswith("<"):
        return int(rango[1:]) > BUILD_MINIMO
    if "-" in rango:
        return int(rango.split("-")[1]) >= BUILD_MINIMO
    return int(rango) >= BUILD_MINIMO


# --------------------------------------------------------------------------
# Paquetes
# --------------------------------------------------------------------------

def nombre_fichero(texto):
    return re.sub(r"[^\w.-]+", "_", texto)


def empaquetar(url, ref, nombre, destino):
    """Crea un .sublime-package (zip) a partir de un tag o rama de git."""
    with tempfile.TemporaryDirectory() as tmp:
        git("clone", "-q", "--depth", "1", "--branch", ref, url, tmp)
        fecha = git("log", "-1", "--format=%ct", cwd=tmp).strip()
        git(
            "archive", "--format=zip", "--prefix=%s/" % nombre,
            "-o", str(destino), "HEAD", cwd=tmp,
        )
    return datetime.fromtimestamp(int(fecha), timezone.utc)


def cargar_canal_paquetes(tmp):
    canal = tmp / "canal-paquetes"
    clonar(CANAL_PAQUETES, canal)
    paquetes = {}
    for f in sorted((canal / "repository").glob("*.json")):
        for p in json.loads(f.read_text(encoding="utf-8")).get("packages", []):
            nombre = p.get("name") or p["details"].rstrip("/").split("/")[-1]
            paquetes[nombre] = p
    return paquetes


def preparar_paquete(nombre, info, carpeta):
    url = info["details"].rstrip("/")
    releases = []
    for rel in info["releases"]:
        rango = rel.get("sublime_text", "*")
        if not rango_cubre_st4(rango):
            continue
        if rel.get("platforms") and not set(rel["platforms"]) & PLATAFORMAS_MAC:
            continue
        if "branch" in rel:
            ref = rel["branch"]
            version = None
        else:
            ref, version = ultimo_tag(url, rel.get("tags", True))
        fichero = carpeta / ("%s-%s.sublime-package" % (nombre_fichero(nombre), nombre_fichero(ref)))
        fecha = empaquetar(url, ref, nombre, fichero)
        if version is None:
            # Igual que Package Control con ramas: versión a partir de la fecha
            version = fecha.strftime("%Y.%m.%d.%H.%M.%S")
        release = {
            "sublime_text": rango,
            "version": version,
            "date": fecha.strftime("%Y-%m-%d %H:%M:%S"),
            "url": "./packages/" + fichero.name,
            "sha256": sha256(fichero),
        }
        if rel.get("platforms"):
            release["platforms"] = rel["platforms"]
        releases.append(release)
        log("   %s %s (Sublime %s)" % (nombre, version, rango))
    return releases


def librerias_de(fichero_paquete):
    """Librerías que pide un paquete en su dependencies.json (cualquier build)."""
    import zipfile

    nombres = set()
    with zipfile.ZipFile(fichero_paquete) as z:
        for n in z.namelist():
            if n.count("/") == 1 and n.endswith("/dependencies.json"):
                datos = json.loads(z.read(n).decode("utf-8"))
                for por_plataforma in datos.values():
                    for lista in por_plataforma.values():
                        nombres.update(lista)
    return nombres


# --------------------------------------------------------------------------
# Librerías
# --------------------------------------------------------------------------

def expandir(asset, py):
    return asset.replace("${py_version}", py.replace(".", ""))


def patron_a_regex(patron):
    patron = patron.replace(".", r"\.").replace("?", ".").replace("*", ".*?")
    return re.compile(patron)


def pypi_asset(base, asset, py):
    """Último wheel de PyPI que encaja con el patrón y la versión de Python."""
    partes = base.rstrip("/").split("/project/")[1].split("/")
    nombre, version_fija = partes[0], (partes[1] if len(partes) > 1 else None)
    regex = patron_a_regex(expandir(asset, py))
    if version_fija:
        datos = leer_json_url("https://pypi.org/pypi/%s/%s/json" % (nombre, version_fija))
        candidatas = {version_fija: datos["urls"]}
    else:
        candidatas = leer_json_url("https://pypi.org/pypi/%s/json" % nombre)["releases"]

    def clave(v):
        return version_de(v) or ()

    for version in sorted(candidatas, key=clave, reverse=True):
        if not version_de(version):
            continue  # descarta betas y rc
        for f in candidatas[version]:
            if f["packagetype"] != "bdist_wheel" or f["yanked"]:
                continue
            if not regex.match(f["filename"]):
                continue
            if not cumple_requires_python(f.get("requires_python"), py):
                continue
            return version, f["url"], f["filename"]
    raise RuntimeError("Sin wheel para %s (Python %s, %s)" % (nombre, py, asset))


def cumple_requires_python(spec, py):
    if not spec:
        return True
    v = version_de(py)
    for parte in spec.split(","):
        parte = parte.strip()
        m = re.fullmatch(r"(>=|<=|==|!=|>|<|~=)\s*([\d.*]+)", parte)
        if not m:
            continue
        op, ref = m.groups()
        if "*" in ref:
            pref = tuple(int(x) for x in ref.rstrip(".*").split("."))
            igual = v[: len(pref)] == pref
            if (op == "==" and not igual) or (op == "!=" and igual):
                return False
            continue
        r = tuple(int(x) for x in ref.split("."))
        n = max(len(v), len(r))
        a, b = v + (0,) * (n - len(v)), r + (0,) * (n - len(r))
        ok = {
            ">=": a >= b, "<=": a <= b, ">": a > b, "<": a < b,
            "==": a == b, "!=": a != b, "~=": a >= b,
        }[op]
        if not ok:
            return False
    return True


def github_asset(base, tag, asset):
    """Fichero adjunto a una release de GitHub (por ejemplo, un wheel)."""
    version = tag.split("-", 1)[1] if re.match(r"^[a-z]+\d*-", tag) else tag.lstrip("v")
    nombre = asset.replace("*", version)
    return "%s/releases/download/%s/%s" % (base.rstrip("/"), tag, nombre), nombre


def preparar_libreria(nombre, info, carpeta, pythons):
    releases = []
    for rel in info["releases"]:
        pys = [p for p in rel["python_versions"] if p in pythons]
        if not pys:
            continue
        plataformas = rel.get("platforms", ["*"])
        if isinstance(plataformas, str):
            plataformas = [plataformas]
        if not set(plataformas) & PLATAFORMAS_MAC:
            continue
        base = rel["base"].rstrip("/")
        asset = rel.get("asset")

        # Un wheel por versión de Python cuando el nombre depende de ella
        grupos = [[p] for p in pys] if asset and "${py_version}" in asset else [pys]
        if "pypi.org" in base:
            grupos = [[p] for p in pys]

        for grupo in grupos:
            py = grupo[0]
            if "pypi.org" in base:
                version, url, fichero = pypi_asset(base, asset, py)
                destino = carpeta / fichero
                if not destino.exists():
                    descargar(url, destino)
            elif asset:
                tag, version = ultimo_tag(base, rel.get("tags", True))
                url, fichero = github_asset(base, tag, asset)
                destino = carpeta / fichero
                if not destino.exists():
                    descargar(url, destino)
            else:
                tag, version = ultimo_tag(base, rel.get("tags", True))
                destino = carpeta / ("%s-%s.zip" % (nombre_fichero(nombre), nombre_fichero(tag)))
                if not destino.exists():
                    empaquetar(base, tag, nombre_fichero(nombre), destino)
            release = {
                "python_versions": grupo,
                "version": version,
                "url": "./libraries/" + destino.name,
                "sha256": sha256(destino),
            }
            if plataformas != ["*"]:
                release["platforms"] = plataformas
            releases.append(release)
            log("   %s %s (Python %s, %s)" % (nombre, version, ", ".join(grupo), ", ".join(plataformas)))
    return releases


# --------------------------------------------------------------------------

def normalizar(nombre):
    """Nombre de librería sin mayúsculas ni diferencias entre '-', '_' y '.'."""
    return re.sub(r"[-_.]+", "-", nombre).lower()


def paquetes_de_la_lista():
    texto = (RAIZ / "User" / "Package Control.sublime-settings").read_text(encoding="utf-8")
    texto = re.sub(r"^\s*//.*$", "", texto, flags=re.M)
    texto = re.sub(r",(\s*[\]}])", r"\1", texto)
    return json.loads(texto)["installed_packages"]


def main():
    if shutil.which("git") is None:
        sys.exit("Hace falta git para preparar la carpeta offline.")

    nombres = paquetes_de_la_lista()
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    (SALIDA / "packages").mkdir(parents=True)
    (SALIDA / "libraries").mkdir()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        log("==> Package Control")
        tag, version = ultimo_tag(PACKAGE_CONTROL, True)
        empaquetar(PACKAGE_CONTROL, tag, "Package Control", SALIDA / "Package Control.sublime-package")
        log("   Package Control %s" % version)

        log("==> Leyendo el canal de paquetes")
        canal = cargar_canal_paquetes(tmp)

        log("==> Paquetes")
        repo_paquetes = []
        librerias = set()
        for nombre in nombres:
            if nombre == "Package Control":
                continue
            if nombre not in canal:
                sys.exit("El paquete %r no está en el canal de Package Control." % nombre)
            info = canal[nombre]
            releases = preparar_paquete(nombre, info, SALIDA / "packages")
            for r in releases:
                librerias |= librerias_de(SALIDA / r["url"][2:])
            autor = info.get("author") or info["details"].rstrip("/").split("/")[-2]
            entrada = {
                "name": nombre,
                "author": autor,
                "homepage": info.get("homepage") or info["details"],
                "issues": info.get("issues") or info["details"].rstrip("/") + "/issues",
                "releases": releases,
            }
            repo_paquetes.append(entrada)

        log("==> Leyendo el canal de librerías")
        canal_libs = tmp / "canal-librerias"
        clonar(CANAL_LIBRERIAS, canal_libs)
        todas = {
            normalizar(l["name"]): l
            for l in json.loads((canal_libs / "repository.json").read_text(encoding="utf-8"))["libraries"]
        }

        log("==> Librerías")
        repo_libs = []
        pedidas = {normalizar(NOMBRES_LIBRERIAS.get(n, n)): NOMBRES_LIBRERIAS.get(n, n) for n in librerias}
        for _, nombre in sorted(pedidas.items()):
            info = todas.get(normalizar(nombre))
            if info is None:
                if nombre.lower() == "typing":
                    continue  # ya viene con Python 3.8 o posterior
                sys.exit("La librería %r no está en el canal de librerías." % nombre)
            releases = preparar_libreria(info["name"], info, SALIDA / "libraries", PYTHONS)
            if releases:
                repo_libs.append({
                    "name": info["name"],
                    "description": info.get("description", ""),
                    "author": info.get("author") or "desconocido",
                    "issues": info.get("issues") or info["releases"][0]["base"],
                    "releases": releases,
                })

    repositorio = {
        "schema_version": "4.0.0",
        "packages": repo_paquetes,
        "libraries": repo_libs,
    }
    (SALIDA / "repository.json").write_text(
        json.dumps(repositorio, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8"
    )
    log("\nListo: %s" % SALIDA)


if __name__ == "__main__":
    main()
