# sublime-tools

Configuración de Sublime Text 4 para macOS: menús en español y un comportamiento parecido a Notepad++, con soporte para JSON y conversión de mayúsculas, snake_case o camelCase.

No necesita permisos de administrador, así que funciona también en equipos gestionados.

## Qué incluye

| Archivo | Qué hace |
|---|---|
| `traducir_sublime.py` | Traduce al español los menús (Archivo, Editar, Selección, Buscar, Ver, Ir, Herramientas, Proyecto, Preferencias, Ayuda y la barra lateral) |
| `User/Preferences.sublime-settings` | Ajustes al estilo Notepad++: recuerda los archivos abiertos, muestra espacios y saltos de línea, usa LF por defecto y deja la barra lateral solo con el árbol de carpetas |
| `User/Default (OSX).sublime-keymap` | Atajos de teclado al estilo Notepad++ (ver tabla más abajo) |
| `User/Package Control.sublime-settings` | Instala automáticamente **Pretty JSON** y **Case Conversion** |
| `install.sh` | Lo instala todo y, además, configura el comando `subl` para la Terminal |

## Instalación

1. Instala **Sublime Text 4**, ábrelo una vez y ciérralo con ⌘Q.
2. En la Terminal:

   ```bash
   git clone https://github.com/pacoromerodev/sublime-tools.git ~/sublime-tools
   cd ~/sublime-tools
   ./install.sh
   ```

3. Abre Sublime Text. La primera vez tarda unos segundos en instalar los paquetes.

Si el instalador no puede descargar Package Control (por ejemplo, por un proxy), revisa la conexión y vuelve a ejecutarlo. También puedes instalarlo a mano desde la paleta de comandos con **Install Package Control**.

### Actualizar

```bash
cd ~/sublime-tools && git pull && ./install.sh
```

Vuelve a ejecutarlo también tras actualizar Sublime Text, para que los menús nuevos se traduzcan.

### Desinstalar

```bash
cd ~/sublime-tools && ./install.sh --restaurar
```

Devuelve los menús al inglés y recupera los ajustes que tenías antes de instalar. Los paquetes instalados (Pretty JSON y Case Conversion) se quedan; si quieres quitarlos, usa **Package Control: Remove Package**.

## Atajos al estilo Notepad++

Todos los atajos de esta guía dan por hecho que tienes **Control y Comando intercambiados** en Ajustes del Sistema → Teclado → Teclas modificadoras, de modo que se pulsan con Ctrl como en Windows.

| Atajo | Acción |
|---|---|
| **Ctrl+F** | Buscar |
| **Ctrl+H** o **Ctrl+R** | Reemplazar |
| **F3** / **Shift+F3** | Coincidencia siguiente / anterior |
| **Ctrl+Shift+F** | Buscar en archivos |
| **Ctrl+A** | Seleccionar todo |
| **Ctrl+G** | Ir a la línea |
| **Ctrl+B** | Ir a la llave o corchete correspondiente |
| **Ctrl+D** | Duplicar línea |
| **Ctrl+L** | Eliminar línea |
| **Ctrl+Shift+↑ / ↓** | Mover la línea arriba / abajo |
| **Ctrl+J** | Unir líneas |
| **Ctrl+U** / **Ctrl+Shift+U** | minúsculas / MAYÚSCULAS |
| **Ctrl+/** | Comentar o descomentar |

Al sustituirlos, se pierden estos atajos de serie de Sublime en Mac: ⌘D (seleccionar la siguiente coincidencia, sigue disponible en Buscar → Añadir siguiente coincidencia), ⌘R (ir a símbolo, en Ir → Ir a símbolo), ⌘L (expandir selección a la línea), ⌘B (compilar) y ⌘U (deshacer suave).

En los MacBook, F3 puede ser una tecla multimedia: púlsala junto con **fn**, o activa "Usar F1, F2, etc. como teclas de función estándar" en Ajustes del Sistema → Teclado.

## Chuleta de uso

| Quiero… | Cómo |
|---|---|
| Abrir la paleta de comandos | **Ctrl+Shift+P** |
| Ver el árbol de carpetas | Abre una carpeta (Archivo → Abrir…) o `subl .` desde la Terminal. Mostrar u ocultar con **Ctrl+K, Ctrl+B** |
| Formatear JSON | Paleta → **Pretty JSON: Format JSON** (también *Minify* y *Validate*) |
| MAYÚSCULAS / minúsculas | Editar → Mayúsculas/minúsculas |
| snake_case, camelCase, PascalCase… | Paleta → **Convert Case** y eliges el formato |
| Cambiar saltos de línea (LF / CRLF) | Ver → Finales de línea |
| Reemplazar `..` por un salto de línea | Ctrl+H, activa el botón **.\*** (regex), busca `\.\.` y reemplaza por `\n` |
| Unir varias líneas en una | Selecciónalas y pulsa **Ctrl+J** (une con espacios). Con otro separador: Ctrl+H con regex, busca `\n` y reemplaza por `,` |

## Limitaciones

- Solo se traducen los menús. El panel de buscar, la paleta de comandos y los mensajes internos están dentro de la propia aplicación y no se pueden traducir.
- Si algún menú queda en inglés, el script lo indica al terminar. Basta con añadir el texto al diccionario `T` de `traducir_sublime.py`.
- En macOS, ⌘H (físicamente Ctrl+H) es el atajo del sistema para ocultar la aplicación. Si en tu equipo **Ctrl+H** oculta Sublime en lugar de abrir Reemplazar, usa **Ctrl+R**, que hace lo mismo.
