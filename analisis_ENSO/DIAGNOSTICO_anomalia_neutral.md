# Diagnóstico: ¿por qué la fase Neutral muestra más anomalía que El Niño?

> **Versión actualizada.** Se rehízo con 2025 completo (364/365 días). En la
> primera versión faltaban 49 días de enero-abril de 2025 que estaban solo en
> la carpeta de Descargas y no en el disco externo. Ahora entran los 60 meses,
> sin descartar ninguno por baja cobertura.

**Respuesta corta:** no es una señal ENSO. Son tres cosas superpuestas — una
métrica engañosa, una confusión estacional estructural, y por debajo de todo,
un efecto de año (2025) disfrazado de efecto de fase.

---

## 1. La columna que estás leyendo no es comparable entre fases

En `wwlln_por_fase_enso.csv`:

| Fase | `anomalia_pct_media` | `z_medio` |
|---|---|---|
| El Niño | +5.28% | +0.112 |
| La Niña | +3.00% | +0.065 |
| Neutral | **−5.62%** | −0.121 |

La anomalía porcentual promedia porcentajes calculados sobre bases muy
distintas. La climatología de julio es de ~73,000 rayos; la de febrero,
~1,244,000 — **17 veces más**. Una misma fluctuación absoluta produce un
porcentaje enorme en un mes seco y uno pequeño en un mes húmedo:

| Año | Mes | Anomalía absoluta | Anomalía % |
|---|---|---|---|
| 2024 | Feb | **+416,541** rayos | +30.5% |
| 2022 | Jul | +88,529 rayos | **+121.0%** |

Julio 2022 aporta un quinto de los rayos que febrero 2024, pero cuadruplica su
porcentaje.

**En el z-score el orden ya es el esperable: El Niño > La Niña > Neutral.**
Solo la columna porcentual exagera la magnitud.

## 2. La fase Neutral está cargada de meses secos (y no por azar)

| Fase | Meses lluviosos | Meses secos | % seca |
|---|---|---|---|
| La Niña | 18 | 6 | 25.0% |
| El Niño | 7 | 5 | 41.7% |
| Neutral | 10 | **14** | **58.3%** |

Esto es estructural: el ONI cruza cero durante la primavera y el verano boreal
(la barrera de predictibilidad de primavera), y los eventos ENSO maduran entre
noviembre y enero. En Perú eso significa que los meses clasificados como
Neutral caen preferentemente en la temporada seca.

Al reponderar todas las fases a una misma mezcla estacional:

| Fase | Anomalía % cruda | Reponderada |
|---|---|---|
| La Niña | +3.00% | +6.10% |
| El Niño | +5.28% | +5.28% |
| Neutral | −5.62% | −4.54% |

Con los datos completos la reponderación explica menos que antes (la brecha
sigue en −4.5%), lo que apunta a que el peso real está en el punto 3.

## 3. Lo que de verdad manda es 2025, no la fase ENSO

**Los doce meses de 2025 son negativos, todos, sin excepción**, con z entre
−0.24 y −1.70. Ningún modo de variabilidad climática produce un déficit
monótono en todos los meses del año.

| Año | z medio |
|---|---|
| 2021 | +0.077 |
| 2022 | +0.550 |
| 2023 | +0.218 |
| 2024 | +0.107 |
| **2025** | **−0.951** |

2025 aporta 9 de los 24 meses Neutral. El efecto sobre la fase:

| | z medio Neutral |
|---|---|
| Con 2025 (n=24) | −0.121 |
| **Sin 2025 (n=15)** | **+0.343** |

Quitando un solo año, Neutral pasa de estar por debajo de El Niño a estar muy
por encima. La comparación entre fases está midiendo, en buena parte, "2025
fue un año bajo".

## 4. ¿El déficit de 2025 es real o es problema de datos?

**Es real.** Contando eventos globales sin filtrar (muestra de ~60 días por
año, todo el planeta):

| Año | Global/día | Perú/día | Perú por millón global |
|---|---|---|---|
| 2023 | 722,092 | 24,833 | 34,390 |
| 2024 | 688,545 | 24,124 | 35,036 |
| 2025 | 650,054 | 16,635 | **25,589** |

Cambio de 2025 respecto al promedio 2023-24:

- Global: **−7.8%**
- Perú: **−32.0%**
- Participación de Perú en el total global: **−26.3%**

Si fuera pérdida de archivos o degradación de la red, el conteo global caería
en la misma proporción que el de Perú. No lo hace: Perú cae cuatro veces más.
Además la calidad de detección en 2025 fue igual o mejor que en años previos
(7.61 estaciones por evento contra 7.24-7.44; residual 11.85 km contra
12.0-12.2 km).

Conclusión: **2025 fue genuinamente un año de baja actividad eléctrica en
Perú**, y eso contamina la comparación por fases porque 2025 es casi todo
Neutral y La Niña.

## 5. Y por debajo de todo: hay un solo evento El Niño

Del diagnóstico de seis pruebas (`diagnostico_enso.py`):

- n nominal = 60 meses, pero **n efectivo (Bretherton) ≈ 31** por
  autocorrelación mensual.
- Bloques ENSO contiguos: 3 La Niña, 3 Neutral, **1 solo El Niño** (2023-24).
- Jackknife dejando un año fuera: la media por fase se mueve entre **0.46 y
  0.82 z** — más que cualquiera de las diferencias que se están interpretando.
- Correlación con rezagos de 0 a 6 meses: perfil plano, |r| ≤ 0.18 en todos
  los rezagos. No hay señal que extraer con esta ventana.

Con un solo evento El Niño no se puede afirmar nada estadístico sobre "el
efecto de El Niño"; a lo sumo describir el caso 2023-24.

---

## Qué haría a continuación

1. **Extender la ventana a 2010-2025.** Es lo único que resuelve de fondo los
   puntos 3 y 5: da varios eventos de cada fase y una climatología que no
   depende del evento que quieres estudiar.
2. **Usar el z-score logarítmico, no la anomalía porcentual.** Los conteos de
   rayos son multiplicativos; el log estabiliza la varianza entre estación
   seca y húmeda. Ya está en `diagnostico_metricas_por_fase.csv`.
3. **Estratificar por temporada** o incluir el mes como covariable, en vez de
   promediar meses secos y húmedos juntos.
4. **Separar por subregión.** Costa, sierra y Amazonía pueden responder con
   signos opuestos y cancelarse en el promedio del dominio.
5. **Investigar 2025 por separado.** El déficit del 26% en participación global
   es un hallazgo en sí mismo, independiente de ENSO, y vale la pena mirarlo
   contra precipitación y otras variables.

## Archivos de este diagnóstico

| Archivo | Qué contiene |
|---|---|
| `diagnostico_composicion_estacional.csv` | Meses secos/lluviosos por fase |
| `diagnostico_metricas_por_fase.csv` | Comparación de métricas (%, z, z leave-one-out, z log) |
| `diagnostico_composicion.png` | Los puntos 1 y 2 en gráfico |
| `conteo_global_2023/24/25.csv` | Conteos globales vs Perú que sustentan el punto 4 |
| `diagnostico_enso.py` | Diagnóstico crítico de seis pruebas |
| `../diagnostico_confusion_estacional.py` | Script que genera el diagnóstico estacional |
