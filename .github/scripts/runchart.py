import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import locale
import os

# Establecer la localización a español para los nombres de mes
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# Datos del repositorio público
REPO_OWNER = 'ainhprzz'
REPO_NAME = 'BetterHealthProject'
url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues?state=all&per_page=100'

# Solicitud GET a la API de GitHub
response = requests.get(url)
issues = response.json()

def week_of_month(fecha):
    return (fecha.day - 1) // 7 + 1

# Crear carpeta para guardar gráficos organizados por semana
fecha_actual = datetime.now()
semana_actual = f"Semana_{fecha_actual.isocalendar()[1]}"
directorio = f'grafico_historial/{semana_actual}'
os.makedirs(directorio, exist_ok=True)

# Diccionarios para agrupar datos
open_issues_daily = {}
closed_issues_daily = {}
open_issues_monthly = {}
closed_issues_monthly = {}
open_issues_weekly_custom = {}
closed_issues_weekly_custom = {}

# Procesar issues
for issue in issues:
    created_at_str = issue.get('created_at')
    if created_at_str:
        created_at = datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%SZ').date()
        open_issues_daily[created_at] = open_issues_daily.get(created_at, 0) + 1
        month_key = created_at.strftime('%Y-%m')
        open_issues_monthly[month_key] = open_issues_monthly.get(month_key, 0) + 1
        key_custom = (created_at.year, created_at.month, week_of_month(created_at))
        open_issues_weekly_custom[key_custom] = open_issues_weekly_custom.get(key_custom, 0) + 1
    
    closed_at_str = issue.get('closed_at')
    if closed_at_str:
        closed_at = datetime.strptime(closed_at_str, '%Y-%m-%dT%H:%M:%SZ').date()
        closed_issues_daily[closed_at] = closed_issues_daily.get(closed_at, 0) + 1
        month_key_closed = closed_at.strftime('%Y-%m')
        closed_issues_monthly[month_key_closed] = closed_issues_monthly.get(month_key_closed, 0) + 1
        key_custom_closed = (closed_at.year, closed_at.month, week_of_month(closed_at))
        closed_issues_weekly_custom[key_custom_closed] = closed_issues_weekly_custom.get(key_custom_closed, 0) + 1

# Semana actual
start_week = fecha_actual.date() - timedelta(days=fecha_actual.weekday())
dias_semana = [start_week + timedelta(days=i) for i in range(7)]
open_weekly = [open_issues_daily.get(dia, 0) for dia in dias_semana]
closed_weekly = [closed_issues_daily.get(dia, 0) for dia in dias_semana]
fecha_str = fecha_actual.strftime('%Y-%m-%d')

# Gráfico semanal
fig1 = plt.figure(figsize=(10, 5))
plt.plot(dias_semana, open_weekly, label='Issues Abiertas', color='blue')
plt.plot(dias_semana, closed_weekly, label='Issues Cerradas', color='green')
plt.xlabel('Día de la Semana')
plt.ylabel('Cantidad de Issues')
plt.title(f'Progresión Semanal - Semana {semana_actual}')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f'{directorio}/grafico_semanal_{fecha_str}.png')
plt.close(fig1)

# Gráfico mensual
todos_meses = sorted(set(list(open_issues_monthly.keys()) + list(closed_issues_monthly.keys())))
open_monthly = [open_issues_monthly.get(mes, 0) for mes in todos_meses]
closed_monthly = [closed_issues_monthly.get(mes, 0) for mes in todos_meses]
fig2 = plt.figure(figsize=(10, 5))
plt.plot(todos_meses, open_monthly, label='Issues Abiertas', color='blue')
plt.plot(todos_meses, closed_monthly, label='Issues Cerradas', color='green')
plt.xlabel('Mes')
plt.ylabel('Cantidad de Issues')
plt.title('Progresión Global de Issues (por Mes)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f'{directorio}/grafico_global_mensual_{fecha_str}.png')
plt.close(fig2)

# Gráfico semanal global
keys_custom = sorted(set(open_issues_weekly_custom.keys()) | set(closed_issues_weekly_custom.keys()))
labels_custom = [f"Week {k[2]} - {datetime(k[0], k[1], 1).strftime('%B')}" for k in keys_custom]
open_custom = [open_issues_weekly_custom.get(k, 0) for k in keys_custom]
closed_custom = [closed_issues_weekly_custom.get(k, 0) for k in keys_custom]
fig3 = plt.figure(figsize=(10, 5))
plt.plot(range(len(labels_custom)), open_custom, label='Issues Abiertas', color='blue', marker='o')
plt.plot(range(len(labels_custom)), closed_custom, label='Issues Cerradas', color='green', marker='o')
plt.xlabel('Semana')
plt.ylabel('Cantidad de Issues')
plt.title('Progresión Global de Issues (por Semana)')
plt.xticks(range(len(labels_custom)), labels_custom, rotation=45)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(f'{directorio}/grafico_global_semanal_{fecha_str}.png')
plt.close(fig3) 
