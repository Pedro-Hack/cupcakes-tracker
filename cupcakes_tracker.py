import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os
from datetime import datetime

# --- Colores ANSI ---
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"

# --- Función para barra de progreso con color ---
def barra_progreso(actual, total, largo=25):
    porcentaje = actual / total if total else 0
    bloques = int(porcentaje * largo)
    
    if porcentaje < 0.5:
        color = RED
    elif porcentaje < 0.8:
        color = YELLOW
    else:
        color = GREEN
    
    barra = color + "█" * bloques + RESET + "░" * (largo - bloques)
    return f"[{barra}] {actual}/{total} ({porcentaje:.0%})"

# --- Conexión a Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Abrir por URL
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1FaQmnl3SWNjaY8eYsHBflpY8rYMl2ZSuHuCszDlzO64/edit?usp=sharingOJA_AQUI").sheet1

# --- Variables para velocidad ---
inicio = datetime.now()
progreso_inicial = None

while True:
    # Leer datos
    sabores = sheet.col_values(2)[1:]   # Columna Sabor
    estados = sheet.col_values(3)[1:]   # Columna Estado

    # Calcular totales
    total_chocolate = sabores.count("Chocolate")
    total_limon = sabores.count("Limón con amapola")

    ok_chocolate = sum(1 for sabor, estado in zip(sabores, estados) if sabor == "Chocolate" and estado == "OK")
    ok_limon = sum(1 for sabor, estado in zip(sabores, estados) if sabor == "Limón con amapola" and estado == "OK")

    # Totales generales
    total_producido = ok_chocolate + ok_limon
    total_objetivo = total_chocolate + total_limon

    if progreso_inicial is None:
        progreso_inicial = total_producido

    # Calcular velocidad y tiempo estimado
    tiempo_transcurrido = (datetime.now() - inicio).total_seconds() / 60  # min
    cupcakes_producidos = total_producido - progreso_inicial
    velocidad = cupcakes_producidos / tiempo_transcurrido if tiempo_transcurrido > 0 else 0
    cupcakes_restantes = total_objetivo - total_producido
    tiempo_estimado = cupcakes_restantes / velocidad if velocidad > 0 else 0

    # Limpiar pantalla y mostrar
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{BOLD}{CYAN}📊 PROGRESO DE PRODUCCIÓN - CUPCAKES{RESET}\n")
    print(f"   Chocolate         {barra_progreso(ok_chocolate, total_chocolate)}")
    print(f"   Limón con amapola {barra_progreso(ok_limon, total_limon)}")
    print("\n─────────────────────────────────────────")
    print(f"   Total general:    {barra_progreso(total_producido, total_objetivo)}")
    print(f"   Velocidad: {GREEN if velocidad > 0 else RED}{velocidad:.2f} cupcakes/min{RESET}")
    print(f"   Tiempo estimado restante: {YELLOW}{tiempo_estimado:.1f} min{RESET}" if velocidad > 0 else f"{RED}   Tiempo estimado: --{RESET}")
    print("─────────────────────────────────────────")

    # Esperar antes de refrescar
    time.sleep(5)
