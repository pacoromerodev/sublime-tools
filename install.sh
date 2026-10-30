#!/usr/bin/env bash
# Instala la configuración de sublime-tools en Sublime Text (macOS).
# No necesita permisos de administrador.
#
# Uso:
#   ./install.sh               instalar
#   ./install.sh --restaurar   quitar la traducción y volver a los ajustes anteriores

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="${SUBLIME_APP:-/Applications/Sublime Text.app}"
DATA="${SUBLIME_DATA:-$HOME/Library/Application Support/Sublime Text}"
USER_DIR="$DATA/Packages/User"
INSTALLED="$DATA/Installed Packages"
BACKUP_DIR="$DATA/sublime-tools-backup"
PC_URL="https://packagecontrol.io/Package%20Control.sublime-package"

info()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m ✓\033[0m %s\n' "$*"; }
aviso() { printf '\033[1;33m !\033[0m %s\n' "$*"; }

if pgrep -xq "Sublime Text" 2>/dev/null; then
    aviso "Sublime Text está abierto. Ciérralo (⌘Q) antes de continuar."
    exit 1
fi

if [[ "${1:-}" == "--restaurar" ]]; then
    info "Restaurando menús en inglés"
    python3 -I "$REPO_DIR/traducir_sublime.py" --usuario "$DATA/Packages" --restaurar
    if [[ -d "$BACKUP_DIR" ]]; then
        info "Recuperando ajustes anteriores"
        if [[ -f "$BACKUP_DIR/.nuevos" ]]; then
            while IFS= read -r nombre; do
                [[ -n "$nombre" ]] && rm -f "$USER_DIR/$nombre"
            done < "$BACKUP_DIR/.nuevos"
        fi
        cp -p "$BACKUP_DIR"/* "$USER_DIR"/ 2>/dev/null || true
        rm -rf "$BACKUP_DIR"
        ok "Ajustes anteriores recuperados"
    fi
    exit 0
fi

if [[ ! -d "$APP" ]]; then
    aviso "No encuentro Sublime Text en $APP. Instala Sublime Text 4 y vuelve a ejecutar este script."
    exit 1
fi

mkdir -p "$USER_DIR" "$INSTALLED"

# 1. Ajustes y atajos (con copia de seguridad de lo que hubiera)
info "Copiando ajustes y atajos"
mkdir -p "$BACKUP_DIR"
for f in "$REPO_DIR"/User/*; do
    nombre="$(basename "$f")"
    [[ "$nombre" == "Package Control.sublime-settings" ]] && continue
    if [[ ! -f "$BACKUP_DIR/$nombre" ]] && ! grep -qxF "$nombre" "$BACKUP_DIR/.nuevos" 2>/dev/null; then
        if [[ -f "$USER_DIR/$nombre" ]]; then
            cp -p "$USER_DIR/$nombre" "$BACKUP_DIR/$nombre"
        else
            echo "$nombre" >> "$BACKUP_DIR/.nuevos"
        fi
    fi
    cp "$f" "$USER_DIR/$nombre"
    ok "$nombre"
done

# Lista de paquetes: se añade a la que ya hubiera, sin borrar ninguno
PCS="$USER_DIR/Package Control.sublime-settings"
if [[ -f "$PCS" && ! -f "$BACKUP_DIR/Package Control.sublime-settings" ]]; then
    cp -p "$PCS" "$BACKUP_DIR/"
elif [[ ! -f "$PCS" ]] && ! grep -qxF "Package Control.sublime-settings" "$BACKUP_DIR/.nuevos" 2>/dev/null; then
    echo "Package Control.sublime-settings" >> "$BACKUP_DIR/.nuevos"
fi
python3 -I - "$REPO_DIR/User/Package Control.sublime-settings" "$PCS" <<'PY'
import json, re, sys
def cargar(p):
    try:
        t = open(p, encoding="utf-8").read()
    except FileNotFoundError:
        return {}
    t = re.sub(r'^\s*//.*$', '', t, flags=re.M)
    t = re.sub(r',(\s*[\]}])', r'\1', t)
    return json.loads(t or "{}")
nuevo, actual = cargar(sys.argv[1]), cargar(sys.argv[2])
lista = actual.get("installed_packages", [])
for p in nuevo["installed_packages"]:
    if p not in lista:
        lista.append(p)
actual["installed_packages"] = lista
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(actual, indent="\t") + "\n")
PY
ok "Package Control.sublime-settings (Pretty JSON y Case Conversion añadidos)"

# 2. Package Control (instalará Pretty JSON y Case Conversion al abrir Sublime)
if [[ -f "$INSTALLED/Package Control.sublime-package" ]]; then
    ok "Package Control ya estaba instalado"
else
    info "Descargando Package Control"
    if curl -fsSL "$PC_URL" -o "$INSTALLED/Package Control.sublime-package"; then
        ok "Package Control instalado"
    else
        rm -f "$INSTALLED/Package Control.sublime-package"
        aviso "No se pudo descargar Package Control (revisa la conexión o el proxy)."
        aviso "Instálalo a mano: abre Sublime → paleta de comandos → Install Package Control."
    fi
fi

# 3. Menús en español
info "Traduciendo menús al español"
python3 -I "$REPO_DIR/traducir_sublime.py" --paquete "$APP/Contents/MacOS/Packages/Default.sublime-package" --usuario "$DATA/Packages"

# 4. Comando 'subl' para abrir carpetas desde la Terminal
info "Configurando el comando subl"
mkdir -p "$HOME/bin"
ln -sf "$APP/Contents/SharedSupport/bin/subl" "$HOME/bin/subl"
if ! grep -qs 'HOME/bin' "$HOME/.zshrc"; then
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
    ok "Añadido ~/bin al PATH en ~/.zshrc (abre una Terminal nueva)"
else
    ok "~/bin ya estaba en el PATH"
fi

echo
ok "Listo. Abre Sublime Text: la primera vez tardará unos segundos en instalar Pretty JSON y Case Conversion."
