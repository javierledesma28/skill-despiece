<div align="center">

[**← README**](../README.md) · [**Demo**](demo.md) · [**Interactiva**](interactivo.md) · [**Explorador**](explorador.md) · **Instalación** · [**Changelog**](../CHANGELOG.md) · [**Licencia**](../LICENSE)

</div>

# Instalar `despiece`

Cinco minutos, sin compilar nada. La skill es una carpeta con un `SKILL.md` y unos scripts de Python que no
necesitan pip. Elegí tu sistema y seguí los pasos en orden.

## Qué necesitás

| | Para qué | Cómo comprobarlo |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | Es donde vive la skill | Abrí una terminal y escribí `claude --version` |
| Python 3.10 o superior | Valida el modelo, dibuja la vista explotada y arma la página | `python3 --version` en macOS/Linux · `python --version` en Windows |
| Git (opcional) | Para clonar y actualizar con un comando | `git --version`. Si no lo tenés, más abajo hay un camino sin Git |
| Edge o Chrome (opcional) | Solo para capturar la página en PNG | Ya lo tenés si navegás por Internet |
| Node 22 o superior (opcional) | Solo para capturar la [página interactiva](interactivo.md) | `node --version` |

Si Python no está: en macOS, `brew install python` o el instalador de [python.org](https://www.python.org/downloads/);
en Windows, el instalador de [python.org](https://www.python.org/downloads/windows/) marcando **«Add python.exe to
PATH»**, o `winget install Python.Python.3.12`.

## macOS y Linux

**1. Cloná la skill en la carpeta de skills personales de Claude Code.**

```bash
git clone https://github.com/javierledesma28/skill-despiece.git ~/.claude/skills/despiece
```

**2. Comprobá que los scripts corren.**

```bash
python3 -I ~/.claude/skills/despiece/scripts/validar_modelo.py ~/.claude/skills/despiece/assets/ejemplo-fisico.json
```

Tiene que terminar con `"ok": true`.

**3. Abrí Claude Code (o reinicialo si ya estaba abierto) y escribí `/despiece`.** Si aparece en el autocompletado, está
instalada.

## Windows

**1. Abrí PowerShell** (botón derecho en Inicio → *Terminal*).

**2. Cloná la skill en la carpeta de skills personales de Claude Code.**

```powershell
git clone https://github.com/javierledesma28/skill-despiece.git "$env:USERPROFILE\.claude\skills\despiece"
```

**3. Comprobá que los scripts corren.**

```powershell
python -I "$env:USERPROFILE\.claude\skills\despiece\scripts\validar_modelo.py" "$env:USERPROFILE\.claude\skills\despiece\assets\ejemplo-fisico.json"
```

Tiene que terminar con `"ok": true`.

**4. Abrí Claude Code (o reinicialo si ya estaba abierto) y escribí `/despiece`.** Si aparece en el autocompletado,
está instalada.

## Sin Git

1. En [la página del repo](https://github.com/javierledesma28/skill-despiece), botón verde **Code → Download ZIP**.
2. Descomprimí el ZIP. Sale una carpeta llamada `skill-despiece-main`: **renombrala a `despiece`**. Claude Code usa
   el nombre de la carpeta, y tiene que coincidir con el de la skill.
3. Movela a la carpeta de skills personales:
   - macOS: en Finder, `Cmd + Shift + G` y pegá `~/.claude/skills` (si no existe, creala).
   - Windows: en el Explorador, pegá `%USERPROFILE%\.claude\skills` en la barra de direcciones (si no existe, creala).
4. Comprobá que dentro quedó `despiece/SKILL.md`, no `despiece/skill-despiece-main/SKILL.md`.
5. Reiniciá Claude Code y escribí `/despiece`.

## Tu primer despiece

Dentro de Claude Code, en el proyecto que quieras:

```
/despiece el túnel VPN entre la oficina y la nube
```

o con tus palabras: *«no entiendo cómo funciona por dentro un SSD NVMe, desmenuzámelo»*. La skill pregunta como
mucho tres cosas (qué tenés que poder hacer después, quién lo lee, hasta dónde bajar) y deja una carpeta
`despiece-<objeto>/` con `modelo.json`, las figuras y `index.html`. Si querés algo corto, pedilo («en dos párrafos»)
y responde en texto sin montar la página.

## Actualizar

```bash
cd ~/.claude/skills/despiece && git pull
```

En Windows, `cd "$env:USERPROFILE\.claude\skills\despiece"; git pull`. Sin Git, volvé a bajar el ZIP y reemplazá la
carpeta. Los cambios de cada versión están en el [changelog](../CHANGELOG.md).

## Desinstalar

Borrá la carpeta `~/.claude/skills/despiece` (en Windows, `%USERPROFILE%\.claude\skills\despiece`). No deja nada
más en el sistema.

## Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `/despiece` no aparece en Claude Code | La carpeta no se llama `despiece`, o `SKILL.md` no está en su raíz | Revisá la ruta: tiene que existir `~/.claude/skills/despiece/SKILL.md`. Reiniciá Claude Code |
| En Windows, `python` abre la Microsoft Store | Python no está instalado o el alias de la Store lo tapa | Instalá Python desde python.org con «Add to PATH», o desactivá el alias en *Configuración → Aplicaciones → Alias de ejecución de aplicaciones* |
| `python: command not found` en macOS | Solo existe `python3` | Usá `python3`. La skill lo acepta igual: Claude Code usa el que tengas |
| `SyntaxError` al correr un script | Python anterior a 3.10 | `python3 --version`; actualizá a 3.10 o superior |
| La captura PNG no sale | Edge o Chrome no están en la ruta esperada | Es opcional: abrí `index.html` en el navegador. Para capturar, usá la ruta completa del ejecutable |
| `capturar-cdp.mjs` dice «hace falta Node 22» | Node anterior a 22 | Actualizá Node (`brew upgrade node`, `winget upgrade OpenJS.NodeJS`) o abrí la página en el navegador |
| `--interactivo` escribe la página estática | El modelo no es de tipo físico o no tiene `geometria` | Es lo esperado: la interactiva solo existe para hardware con geometría (ver [Interactiva](interactivo.md)) |
| En el explorador, la transición se queda a medias | La pestaña está oculta: el navegador pausa las View Transitions | Ponela en primer plano, o revisalo con `capturar-cdp.mjs` (ver [Explorador](explorador.md)) |
| La página sale sin marca | Es lo esperado | La skill no trae la marca de nadie. Pasá `--marca ruta/a/tu-marca.json` (ver [el README](../README.md#tu-marca-en-un-fichero)) |

¿Otra cosa? [Abrí un issue](https://github.com/javierledesma28/skill-despiece/issues) con tu sistema, la versión
de Python y el mensaje exacto.

---

<div align="center">

Un desarrollo de [**Think28**](https://t28.io) · hecho con Claude Code y amor

</div>
