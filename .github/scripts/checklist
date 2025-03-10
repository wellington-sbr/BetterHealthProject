import os
import requests
from datetime import datetime, timedelta
import calendar
import yaml
import json

# Configuración
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "usuario/repositorio"  # Cambiar por tu repositorio
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"

# Encabezados para la API de GitHub
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_devops_phases():
    """Obtener las fases de DevOps desde las etiquetas (labels) de GitHub"""
    try:
        response = requests.get(f"{GITHUB_API_URL}/labels", headers=headers)
        response.raise_for_status()
        
        # Filtrar solo etiquetas relacionadas con DevOps
        all_labels = response.json()
        devops_labels = [label["name"] for label in all_labels if "devops" in label["name"].lower()]
        
        # Si no hay etiquetas específicas de DevOps, usar un conjunto predeterminado
        if not devops_labels:
            devops_labels = [
                "Plan", "Code", "Build", "Test", 
                "Release", "Deploy", "Operate", "Monitor"
            ]
        
        return devops_labels
    except Exception as e:
        print(f"Error al obtener etiquetas de GitHub: {e}")
        # Devolver fases predeterminadas en caso de error
        return [
            "Plan", "Code", "Build", "Test", 
            "Release", "Deploy", "Operate", "Monitor"
        ]

def get_completed_issues_by_week(phase, start_date, end_date):
    """Obtener issues completados para una fase en un rango de fechas"""
    try:
        # Formatear fechas para la API de GitHub
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Consultar issues cerrados con la etiqueta específica en el rango de fechas
        query = f"repo:{GITHUB_REPO} label:\"{phase}\" closed:{start_date_str}..{end_date_str}"
        response = requests.get(
            "https://api.github.com/search/issues",
            headers=headers,
            params={"q": query}
        )
        response.raise_for_status()
        
        return response.json()["total_count"]
    except Exception as e:
        print(f"Error al obtener issues para {phase}: {e}")
        return 0

def generate_month_checklist(year, month):
    """Generar datos de checklist para un mes específico"""
    # Obtener fases de DevOps
    devops_phases = get_devops_phases()
    
    # Calcular fechas para las semanas del mes
    first_day = datetime(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    last_day = datetime(year, month, last_day_num)
    
    # Dividir el mes en 4 semanas (aproximadamente)
    days_in_month = (last_day - first_day).days + 1
    days_per_week = days_in_month // 4
    
    weeks = []
    for i in range(4):
        start = first_day + timedelta(days=(i * days_per_week))
        end = first_day + timedelta(days=((i + 1) * days_per_week) - 1)
        if i == 3:  # Para la última semana, asegurarse de que incluya el último día
            end = last_day
        weeks.append((start, end))
    
    # Crear estructura del checklist
    checklist_data = {
        "month": datetime(year, month, 1).strftime('%B %Y'),
        "phases": {}
    }
    
    # Obtener datos para cada fase
    for phase in devops_phases:
        phase_data = {
            "week1": {
                "completed": False,
                "issues_count": get_completed_issues_by_week(phase, weeks[0][0], weeks[0][1])
            },
            "week2": {
                "completed": False,
                "issues_count": get_completed_issues_by_week(phase, weeks[1][0], weeks[1][1])
            },
            "week3": {
                "completed": False,
                "issues_count": get_completed_issues_by_week(phase, weeks[2][0], weeks[2][1])
            },
            "week4": {
                "completed": False,
                "issues_count": get_completed_issues_by_week(phase, weeks[3][0], weeks[3][1])
            }
        }
        
        # Calcular total de issues
        total_issues = sum([phase_data[f"week{i+1}"]["issues_count"] for i in range(4)])
        phase_data["total_issues"] = total_issues
        
        checklist_data["phases"][phase] = phase_data
    
    return checklist_data

def save_checklist_to_yaml(checklist_data, output_file):
    """Guardar datos del checklist en formato YAML"""
    with open(output_file, 'w') as file:
        yaml.dump(checklist_data, file, default_flow_style=False)
    print(f"Checklist guardado en {output_file}")

def generate_markdown_table(checklist_data):
    """Generar tabla de markdown para visualizar el checklist"""
    month = checklist_data["month"]
    phases = checklist_data["phases"]
    
    markdown = f"# DevOps Checklist - {month}\n\n"
    markdown += "| Fase | Semana 1 | Semana 2 | Semana 3 | Semana 4 | Total Issues |\n"
    markdown += "|------|---------|---------|---------|---------|-------------|\n"
    
    for phase, data in phases.items():
        week1 = "✅" if data["week1"]["completed"] else "⬜"
        week2 = "✅" if data["week2"]["completed"] else "⬜"
        week3 = "✅" if data["week3"]["completed"] else "⬜"
        week4 = "✅" if data["week4"]["completed"] else "⬜"
        total = data["total_issues"]
        
        markdown += f"| {phase} | {week1} ({data['week1']['issues_count']}) | {week2} ({data['week2']['issues_count']}) | {week3} ({data['week3']['issues_count']}) | {week4} ({data['week4']['issues_count']}) | {total} |\n"
    
    return markdown

def generate_monthly_checklist():
    """Función principal para generar checklist del mes actual"""
    now = datetime.now()
    year = now.year
    month = now.month
    
    # Generar datos del checklist
    checklist_data = generate_month_checklist(year, month)
    
    # Guardar en YAML
    output_file = f"devops_checklist_{year}_{month:02d}.yml"
    save_checklist_to_yaml(checklist_data, output_file)
    
    # Generar markdown para visualización
    markdown = generate_markdown_table(checklist_data)
    with open(f"devops_checklist_{year}_{month:02d}.md", 'w') as file:
        file.write(markdown)
    
    return checklist_data

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("Error: Debes configurar GITHUB_TOKEN como variable de entorno")
        print("Ejemplo: export GITHUB_TOKEN=ghp_abc123...")
        exit(1)
    
    generate_monthly_checklist()
