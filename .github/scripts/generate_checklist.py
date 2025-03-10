import os
import calendar
import yaml
from datetime import datetime, timedelta


def get_devops_phases():
    """Obtener las fases predeterminadas de DevOps"""
    # Usar un conjunto predeterminado de fases DevOps
    devops_phases = [
        "Plan", "Code", "Build", "Test",
        "Release", "Deploy", "Operate", "Monitor"
    ]

    return devops_phases


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

    # Crear datos para cada fase con valores iniciales
    for phase in devops_phases:
        phase_data = {
            "week1": {
                "completed": False,
                "issues_count": 0
            },
            "week2": {
                "completed": False,
                "issues_count": 0
            },
            "week3": {
                "completed": False,
                "issues_count": 0
            },
            "week4": {
                "completed": False,
                "issues_count": 0
            },
            "total_issues": 0
        }

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
    markdown_file = "health_checklist.md"
    with open(markdown_file, 'w') as file:
        file.write(markdown)

    print(f"Markdown guardado en {markdown_file}")

    return checklist_data


if __name__ == "__main__":
    generate_monthly_checklist()