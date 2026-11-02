// Captura una página en un Chromium headless por DevTools Protocol, en tiempo real: a diferencia de
// --screenshot, aquí sí corren los IntersectionObserver, las animaciones ligadas al scroll y las View
// Transitions. Sirve para revisar la página interactiva del despiece (paso 6). Requiere Node 22 o más
// (fetch y WebSocket globales) y Edge, Chrome o Chromium instalado.
//
// Uso:   node capturar-cdp.mjs <salida.png|-> <ancho> <alto> <url> [js] [espera-ms]
//   salida  PNG que se escribe; «-» no captura y solo imprime lo que devuelve el js (para comprobar estado)
//   js      expresión que se evalúa tras cargar (p. ej. "scrollTo({top: 1800, behavior: 'instant'})": la página usa scroll suave); admite promesas
//   espera  ms entre el js y la captura (por defecto 1800)
// Entorno: NAVEGADOR=<ruta>  TEMA=light|dark (light por defecto)  MOVIMIENTO=reduce  SIN_JS=1
//   PUERTO=<n> fija el puerto de depuración; sin él, el navegador elige uno libre y se pueden lanzar capturas en paralelo
// Parámetros de la página interactiva: ?p=0..1 (explosión de la portada), ?paso=N (flujo),
//   ?abrir=<id> (tarjeta del nivel 2 abierta), ?tema=light|dark; y #ancla para ir a una sección.
// Salida: 0 bien · 1 la página lanzó errores de JavaScript (van a stderr) · 2 argumentos o navegador.
// Ejemplo: node capturar-cdp.mjs portada.png 1240 900 "file:///C:/tmp/despiece/index.html?p=1"
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const args = process.argv.slice(2);
const pideAyuda = args.includes('--help') || args.includes('-h');
if (pideAyuda || args.length < 4) {
  const ayuda = readFileSync(new URL(import.meta.url), 'utf8').split('\n').filter(l => l.startsWith('//')).map(l => l.slice(3)).join('\n');
  (pideAyuda ? console.log : console.error)(ayuda);
  process.exit(pideAyuda ? 0 : 2);
}
const [salida, ancho, alto, url, js = '', espera = '1800'] = args;
if (typeof WebSocket === 'undefined') {
  console.error(`ERROR: hace falta Node 22 o superior (usa WebSocket global) y este es ${process.version}. Actualizá Node.`);
  process.exit(2);
}

const CANDIDATOS = {
  win32: ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Google/Chrome/Application/chrome.exe'],
  darwin: ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium'],
  linux: ['/usr/bin/microsoft-edge', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium'],
};
const navegador = process.env.NAVEGADOR || (CANDIDATOS[process.platform] || []).find(existsSync);
if (!navegador) {
  console.error('ERROR: no encuentro Edge, Chrome ni Chromium. Indicá la ruta con NAVEGADOR=<ruta del ejecutable>.');
  process.exit(2);
}
// Puerto 0: el navegador elige uno libre y lo escribe en DevToolsActivePort, dentro del perfil temporal
const PUERTO_FIJO = process.env.PUERTO ? +process.env.PUERTO : 0;
const perfil = mkdtempSync(join(tmpdir(), 'despiece-cdp-'));
const proceso = spawn(navegador, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  `--remote-debugging-port=${PUERTO_FIJO}`, `--user-data-dir=${perfil}`, 'about:blank'], { stdio: 'ignore' });
const dormir = ms => new Promise(r => setTimeout(r, ms));
const errores = [];
let ws;
try {
  let destino, puerto = PUERTO_FIJO;
  for (let i = 0; i < 60 && !destino; i++) {
    if (!puerto) try { puerto = +readFileSync(join(perfil, 'DevToolsActivePort'), 'utf8').split('\n')[0]; } catch {}
    if (puerto) try { destino = (await (await fetch(`http://127.0.0.1:${puerto}/json/list`)).json()).find(t => t.type === 'page'); } catch {}
    if (!destino) await dormir(250);
  }
  if (!destino) throw new Error(PUERTO_FIJO ? `el navegador no abrió el puerto ${PUERTO_FIJO}: ¿hay otro usándolo? Probar sin PUERTO` : 'el navegador no abrió el puerto de depuración en 15 s');
  ws = new WebSocket(destino.webSocketDebuggerUrl);
  await new Promise((ok, mal) => { ws.addEventListener('open', ok, { once: true }); ws.addEventListener('error', mal, { once: true }); });
  let n = 0; const pendientes = new Map();
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pendientes.has(m.id)) { pendientes.get(m.id)(m); pendientes.delete(m.id); return; }
    if (m.method === 'Runtime.exceptionThrown') errores.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errores.push(m.params.args.map(a => a.value ?? a.description).join(' '));
  });
  const cdp = (method, params = {}) => new Promise(r => { const id = ++n; pendientes.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
  await cdp('Runtime.enable');
  await cdp('Emulation.setDeviceMetricsOverride', { width: +ancho, height: +alto, deviceScaleFactor: 1, mobile: +ancho < 600 });
  // Tema claro salvo que se pida otro: si no, el headless hereda el del sistema y las capturas cambian de una máquina a otra
  const media = [{ name: 'prefers-color-scheme', value: process.env.TEMA || 'light' }];
  if (process.env.MOVIMIENTO) media.push({ name: 'prefers-reduced-motion', value: process.env.MOVIMIENTO });
  await cdp('Emulation.setEmulatedMedia', { features: media });
  if (process.env.SIN_JS) await cdp('Emulation.setScriptExecutionDisabled', { value: true });
  await cdp('Page.enable');
  await cdp('Page.navigate', { url });
  await dormir(3200);
  let valor;
  if (js) {
    const r = await cdp('Runtime.evaluate', { expression: js, awaitPromise: true, returnByValue: true });
    if (r.result?.exceptionDetails) throw new Error('el js falló: ' + JSON.stringify(r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text));
    valor = r.result?.result?.value;
  }
  if (salida === '-') {
    console.log(JSON.stringify(valor, null, 1));
  } else {
    await dormir(+espera);
    const r = await cdp('Page.captureScreenshot', { format: 'png' });
    writeFileSync(salida, Buffer.from(r.result.data, 'base64'));
    console.log(JSON.stringify({ salida, ancho: +ancho, alto: +alto }));
  }
} catch (e) {
  console.error('ERROR: ' + (e.message || e));
  process.exitCode = 2;
} finally {
  ws?.close();
  proceso.kill();
  await dormir(400);
  try { rmSync(perfil, { recursive: true, force: true }); } catch {}
}
for (const err of errores) console.error('ERROR de la página: ' + err);
if (errores.length && !process.exitCode) process.exitCode = 1;
