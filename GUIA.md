# Guía de instalación y configuración paso a paso

Esta guía deja Sublime Text 4 en macOS con los menús en español, atajos de teclado como en Notepad++ y todos los paquetes del repositorio. Se tarda unos 10 minutos.

No hace falta ser administrador del equipo.

---

## Paso 1. Comprobar los requisitos

Abre la **Terminal** (⌘ Espacio, escribe `Terminal` e Intro) y ejecuta:

```bash
ls "/Applications/Sublime Text.app" >/dev/null && echo "Sublime Text: OK"
git --version
python3 --version
```

Deberías ver tres respuestas:

- `Sublime Text: OK`
- `git version …`
- `Python 3.…`

Si falla alguna:

| Falta | Qué hacer |
|---|---|
| Sublime Text | Descárgalo de [sublimetext.com](https://www.sublimetext.com/download) y arrástralo a **Aplicaciones**, o instálalo desde el catálogo de software de tu equipo |
| git o python3 | Ejecuta `xcode-select --install` y acepta, o instálalos desde el catálogo de software de tu equipo |

- [ ] Los tres comandos responden correctamente.

---

## Paso 2. Abrir Sublime Text una vez

1. Abre **Sublime Text** desde Aplicaciones.
2. Espera a que aparezca la ventana. Así se crea su carpeta de configuración.
3. Ciérralo del todo con **Sublime Text → Quit Sublime Text** (⌘Q).

> Es importante cerrarlo del todo y no solo la ventana: el instalador se niega a continuar si Sublime sigue abierto.

- [ ] Sublime Text se ha abierto y cerrado.

---

## Paso 3. Intercambiar Control y Comando (recomendado)

Los atajos de esta configuración están pensados para pulsarse con **Ctrl**, como en Windows. Para eso hay que intercambiar las teclas Control y Comando:

1. Abre **Ajustes del Sistema → Teclado**.
2. Pulsa **Atajos de teclado…** → **Teclas modificadoras**.
3. En **Seleccionar teclado**, elige tu teclado.
4. Cambia:
   - **Tecla Control (^)** → **⌘ Comando**
   - **Tecla Comando (⌘)** → **^ Control**
5. Pulsa **OK**.
6. Si usas varios teclados (el del portátil y uno externo), repite los pasos 3 a 5 con cada uno.

Prueba: Ctrl+C y Ctrl+V deberían copiar y pegar en cualquier aplicación.

Ten en cuenta que esto afecta a todo el sistema:

- Cambiar de aplicación pasa a ser **Ctrl+Tab**.
- Spotlight pasa a ser **Ctrl+Espacio**.
- En la Terminal, para interrumpir un proceso (el Ctrl+C de siempre) se pulsa la tecla física **⌘+C**.

Si prefieres no intercambiarlas, todo funciona igual, pero los atajos de esta guía se pulsan con **⌘** en vez de con Ctrl.

- [ ] Control y Comando intercambiados (o decidido no hacerlo).

---

## Paso 4. Descargar el repositorio

En la Terminal:

```bash
git clone https://github.com/pacoromerodev/sublime-tools.git ~/sublime-tools
cd ~/sublime-tools
```

Si `git clone` pide usuario y contraseña, es que no tienes acceso a GitHub configurado. Como alternativa, descarga el ZIP desde la página del repositorio (**Code → Download ZIP**), descomprímelo en tu carpeta personal, renombra la carpeta a `sublime-tools` y entra en ella con `cd ~/sublime-tools`.

- [ ] La carpeta `~/sublime-tools` existe.

---

## Paso 5. Ejecutar el instalador

Con Sublime Text **cerrado**:

```bash
./install.sh
```

Verás algo parecido a esto:

```
==> Copiando ajustes y atajos
 ✓ Default (OSX).sublime-keymap
 ✓ Default.sublime-commands
 ✓ JSON.sublime-settings
 ✓ Preferences.sublime-settings
 ✓ Pretty JSON.sublime-settings
 ✓ YAML.sublime-settings
 ✓ Package Control.sublime-settings (lista de paquetes añadida)
==> Descargando Package Control
 ✓ Package Control instalado
==> Traduciendo menús al español
Menús traducidos: …
==> Configurando el comando subl
 ✓ Añadido ~/bin al PATH en ~/.zshrc (abre una Terminal nueva)

 ✓ Listo.
```

Qué hace el instalador:

1. Guarda una copia de tus ajustes actuales de Sublime, por si quieres volver atrás.
2. Copia los ajustes y atajos del repositorio.
3. Añade los paquetes a la lista de Package Control, sin quitar los que ya tuvieras.
4. Descarga Package Control si no lo tenías.
5. Traduce los menús al español.
6. Configura el comando `subl` para abrir carpetas desde la Terminal.

Si aparece `permission denied`, ejecuta antes `chmod +x install.sh`.

- [ ] El instalador termina con **✓ Listo**.

---

## Paso 6. Primer arranque

1. Abre **Sublime Text**.
2. Espera **uno o dos minutos** sin cerrarlo: Package Control está descargando los paquetes. En la barra de estado (abajo) verás mensajes de progreso.
3. Si aparece algún aviso:
   - **MarkdownEditing** pregunta si desactivar el paquete Markdown de serie → responde **que sí**.
   - **Package Control** pide reiniciar → cierra con ⌘Q y vuelve a abrir.
4. Cierra Sublime Text (⌘Q) y vuelve a abrirlo para que cargue todo.

- [ ] Sublime se ha abierto, ha instalado los paquetes y se ha reiniciado.

---

## Paso 7. Comprobar que todo funciona

Haz estas pruebas una a una. Los atajos dan por hecho que intercambiaste Control y Comando en el paso 3.

### Menús en español
- [ ] La barra de menús muestra **Archivo, Editar, Selección, Buscar, Ver, Ir…**
- [ ] **Editar** muestra **Deshacer, Rehacer, Cortar, Copiar, Pegar**.
- [ ] Clic derecho en el texto muestra **Cortar, Copiar, Pegar…**, y en una pestaña **Cerrar pestaña, Cerrar las demás pestañas…**
- [ ] Al terminar, el instalador **no** muestra "Quedan … textos en inglés".

Algunas opciones las pone macOS y siempre salen en inglés: *Services*, *Hide*, *Quit*, el menú *Window* y, en Editar, *Start Dictation* y *Emoji & Symbols*.

### Paquetes instalados
1. Pulsa **Ctrl+Shift+P** (paleta de comandos).
2. Escribe `Package Control: List Packages` e Intro.
- [ ] Aparecen, entre otros, Pretty JSON, Pretty YAML, Case Conversion, Filter Lines y Compare Side-By-Side.

### Atajos al estilo Notepad++
Abre un archivo nuevo (Ctrl+N), escribe unas líneas y prueba:
- [ ] **Ctrl+H** abre Reemplazar (si oculta Sublime, usa **Ctrl+R**; ver Problemas frecuentes).
- [ ] **Ctrl+D** duplica la línea.
- [ ] **Ctrl+L** elimina la línea.
- [ ] **Ctrl+G** abre "Ir a la línea".
- [ ] **Ctrl+Shift+↑ / ↓** mueve la línea.
- [ ] **Ctrl+U** / **Ctrl+Shift+U** pasa a minúsculas / MAYÚSCULAS.

### JSON
Pega esto en un archivo nuevo:
```
{"nombre":"prueba","activo":true,"tags":["a","b"]}
```
1. Paleta (Ctrl+Shift+P) → **Pretty JSON: Format JSON**.
- [ ] Queda formateado con sangría de 2 espacios.

### Mayúsculas, snake_case, camelCase
Escribe `nombre_de_cliente` y selecciónalo:
1. Paleta → **Convert Case: camelCase**.
- [ ] Queda `nombreDeCliente`.

### Reemplazar por saltos de línea
Escribe `uno..dos..tres`:
1. **Ctrl+H** y activa el botón **.\*** (expresiones regulares), a la izquierda del panel.
2. Buscar: `\.\.` · Reemplazar: `\n` → **Replace All**.
- [ ] Queda una palabra por línea.

### Unir líneas
Selecciona las tres líneas anteriores y pulsa **Ctrl+J**.
- [ ] Quedan en una sola línea: `uno dos tres`.

### Árbol de carpetas
1. Abre una **nueva** Terminal (para que cargue el comando `subl`).
2. Ejecuta `subl ~/sublime-tools`.
- [ ] Sublime se abre con el árbol de carpetas a la izquierda y los iconos por tipo de fichero.

### Saltos de línea y espacios
- [ ] La barra de estado (abajo) muestra la codificación (UTF-8) y el tipo de salto de línea (Unix).
- [ ] Los espacios se ven como puntos y los tabuladores como líneas.

---

## Paso 8 (opcional). Personalizar

Toda la configuración está en `~/sublime-tools/User/`. Para cambiar algo:

1. Edita el archivo en `~/sublime-tools/User/`.
2. Vuelve a ejecutar `./install.sh` con Sublime cerrado.

| Quiero cambiar… | Archivo |
|---|---|
| Ajustes generales | `Preferences.sublime-settings` |
| Atajos de teclado | `Default (OSX).sublime-keymap` |
| Lista de paquetes | `Package Control.sublime-settings` |
| Sangría de JSON o YAML | `JSON.sublime-settings`, `YAML.sublime-settings` |
| Traducción de un menú | diccionario `T` en `traducir_sublime.py` |

También puedes cambiar ajustes directamente en Sublime (**Preferencias → Ajustes**), pero se perderán si vuelves a ejecutar el instalador.

---

## Actualizar

Cuando haya cambios en el repositorio, o después de actualizar Sublime Text:

```bash
cd ~/sublime-tools
git pull
./install.sh
```

---

## Desinstalar

Con Sublime cerrado:

```bash
cd ~/sublime-tools
./install.sh --restaurar
```

Esto devuelve los menús al inglés y recupera los ajustes que tenías antes de instalar. Los paquetes descargados se quedan; para quitarlos, abre la paleta → **Package Control: Remove Package**.

Para quitar también el comando `subl`: `rm ~/bin/subl`.

---

## Problemas frecuentes

| Problema | Solución |
|---|---|
| `Sublime Text está abierto. Ciérralo (⌘Q)` | Ciérralo con ⌘Q (no basta con cerrar la ventana) y vuelve a ejecutar `./install.sh` |
| `No se pudo descargar Package Control` | La red bloquea packagecontrol.io (proxy). Revisa la conexión y vuelve a ejecutar el instalador, o abre Sublime → paleta → **Install Package Control** |
| Los paquetes no se instalan | Paleta → **Package Control: Satisfy Libraries** y luego reinicia Sublime. Si sigue igual, revisa el registro en **Ver → Mostrar consola** |
| **Ctrl+H** oculta Sublime | macOS reserva ⌘H para ocultar aplicaciones. Usa **Ctrl+R**, que también abre Reemplazar |
| **F3** sube el brillo o el volumen | Pulsa **fn+F3**, o activa "Usar F1, F2, etc. como teclas de función estándar" en Ajustes del Sistema → Teclado |
| Algún menú sigue en inglés | Las opciones que añade macOS (Services, Hide, Quit, el menú Window, Start Dictation) siempre salen en inglés. Para el resto, el instalador lista al final los textos que no ha traducido: añádelos al diccionario `T` de `traducir_sublime.py` y vuelve a ejecutarlo |
| Tras actualizar Sublime, los menús vuelven al inglés | Ejecuta de nuevo `./install.sh` |
| `subl: command not found` | Abre una Terminal nueva. Si sigue, ejecuta `source ~/.zshrc` |
| `permission denied: ./install.sh` | Ejecuta `chmod +x install.sh` |
