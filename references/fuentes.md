# De dónde sale cada regla

Leer cuando se quiera saber por qué la skill exige algo o ampliar el método. Research del 2026-11-01
(tres líneas: la skill `anatomy`, las skills de explicación visual mejor valoradas y la bibliografía de
despiece y explicación).

## Skills de terceros estudiadas y qué se tomó de cada una

| Skill | Qué se copió | Qué se descartó |
|---|---|---|
| [wheresryan22/anatomy](https://github.com/wheresryan22/anatomy) (23,6k ★) | La correspondencia concepto ↔ mecanismo en una frase; un único modelo de verdad del que sale todo; lista de piezas antes del dibujo; reglas de la vista explotada; una pieza destacada | Inventar una máquina para cada concepto (analogías forzadas); prohibir cajas y flechas; su coste (Node + Chrome, 2–4 h por figura) |
| [nicobailon/visual-explainer](https://github.com/nicobailon/visual-explainer) (10,7k ★) | Una afirmación por figura; tabla contenido → tipo de figura; evals A/B con juez ciego | Mega-skill de 10 comandos; fuentes prohibidas que chocan con la marca |
| [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) (5,1k ★) | Elegir el patrón visual por la relación (fan-out, ciclo, convergencia); test de isomorfismo; bucle dibujar → revisar → corregir | Atarse a un formato |
| [zarazhangrui/codebase-to-course](https://github.com/zarazhangrui/codebase-to-course) (5,8k ★) | Primero lo general, después el zoom; el «por qué importa» antes del «cómo» | Una metáfora por módulo, siempre |
| [mattpocock/skills → teach](https://github.com/mattpocock/skills) | Prohibido explicar sin fuente; perfil del lector antes de empezar | — |
| [bentossell/visualise](https://github.com/bentossell/visualise) | El verbo de la pregunta elige el visual; tope de nodos con vista general + subflujos | — |
| [elvarofficial/teardown](https://github.com/elvarofficial/teardown) | Modos de corte por capas | Simulador 3D |
| [analyticalmonk/explain-this](https://github.com/analyticalmonk/explain-this) | Aprobar el índice (aquí, el encuadre) antes de seguir | — |

Ninguna de las revisadas encuadra antes de empezar ni comprueba que el lector entendió: de ahí el paso 1
y las puertas de comprensión.

## Bibliografía del método

- **Vistas explotadas y montaje**: Agrawala, Phan, Heiser et al., *Designing Effective Step-By-Step
  Assembly Instructions* (SIGGRAPH 2003): una pieza significativa por paso, lo nuevo visible, −35 % de
  tiempo y −50 % de errores. Li, Agrawala, Curless, Salesin, *Automated Generation of Interactive 3D
  Exploded View Diagrams* (SIGGRAPH 2008): direcciones sin bloqueo, separación mínima, subconjuntos antes
  que piezas, contenedores cortados por un plano. Stephen Biesty, *Incredible Cross-Sections*: el objeto
  abierto sigue siendo reconocible.
- **Sistemas**: IDEF0 (FIPS 183); C4 model (Simon Brown); FAST (Bytheway); Donella Meadows, *Thinking in
  Systems*; [alex/what-happens-when](https://github.com/alex/what-happens-when).
- **Ideas**: Barbara Minto, *The Pyramid Principle* (MECE); Novak y Cañas, *The Theory Underlying Concept
  Maps*; técnica de Feynman; Bret Victor, *Up and Down the Ladder of Abstraction*.
- **Explicadores**: 3Blue1Brown (lo concreto antes que lo abstracto); Nicky Case (empezar por una
  pregunta; «pero / por tanto», no «y luego»); Bartosz Ciechanowski (seguir el flujo de energía, una pieza
  por figura, colores constantes); Hohman et al. en Distill (hacer predecir antes de revelar); Julia
  Evans, [*Patterns in confusing explanations*](https://jvns.ca/blog/confusing-explanations/).
- **Cognición**: Mayer, *Multimedia Learning* (coherencia, señalización, contigüidad, segmentación,
  preentrenamiento); Sweller (carga cognitiva, inversión de pericia); Tufte (tinta de datos, small
  multiples); Shneiderman (*overview first, zoom and filter, details on demand*).

## Correspondencia regla → fuente

| Regla de la skill | Fuente |
|---|---|
| Encuadre con pregunta foco y lector | Novak (pregunta foco), teach (perfil), explain-this (aprobar antes) |
| Nombrar las piezas antes del mecanismo | Mayer, preentrenamiento |
| 3–7 por nivel, ≤ 6 nuevas por figura | Sweller; visualise; IDEF0 (3–6 cajas) |
| Título afirmativo, una idea por figura | visual-explainer; Tufte |
| Orden de montaje al revés, subconjuntos antes | Agrawala 2003, Li 2008 |
| Seguir el flujo de entrada a salida | Ciechanowski; what-happens-when |
| Cada pieza con fuente o marcada como supuesto | teach; la regla de no inventar arquitectura que no se leyó |
| Tres frases y pregunta de predicción | Feynman; Distill |
| Metáfora solo si cabe en una frase | Evans (analogías forzadas); contraste con anatomy |
| Delegar el trazo y revisar con isomorfismo | excalidraw-diagram-skill |
