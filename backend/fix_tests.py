#!/usr/bin/env python3
"""
Script para actualizar los tests con el nuevo formato de datos
"""

import re
import os

def update_test_file(file_path):
    """Actualiza un archivo de test con el nuevo formato"""
    print(f"Actualizando {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patrón para encontrar visitor_data con formato antiguo
    old_pattern = r"visitor_data = \{\s*'name': '[^']*',\s*'dni': '[^']*',\s*'age': \d+,\s*'clothing_size': '[^']*',\s*'terms_accepted': (?:True|False)\s*\}"
    
    def replace_visitor_data(match):
        # Extraer valores del match
        name_match = re.search(r"'name': '([^']*)'", match.group())
        dni_match = re.search(r"'dni': '([^']*)'", match.group())
        age_match = re.search(r"'age': (\d+)", match.group())
        clothing_match = re.search(r"'clothing_size': '([^']*)'", match.group())
        terms_match = re.search(r"'terms_accepted': (True|False)", match.group())
        
        name = name_match.group(1) if name_match else "Test User"
        dni = dni_match.group(1) if dni_match else "12345678"
        age = age_match.group(1) if age_match else "25"
        clothing = clothing_match.group(1) if clothing_match else "M"
        terms = terms_match.group(1) if terms_match else "True"
        
        return f"""visitor_data = {{
                'participants': [{{
                    'name': '{name}',
                    'dni': '{dni}',
                    'age': {age},
                    'clothing_size': '{clothing}'
                }}],
                'terms_accepted': {terms},
                'participants_count': 1
            }}"""
    
    # Reemplazar todos los patrones encontrados
    new_content = re.sub(old_pattern, replace_visitor_data, content, flags=re.MULTILINE | re.DOTALL)
    
    # También actualizar patrones sin clothing_size
    old_pattern_no_clothing = r"visitor_data = \{\s*'name': '[^']*',\s*'dni': '[^']*',\s*'age': \d+,\s*'terms_accepted': (?:True|False)\s*\}"
    
    def replace_visitor_data_no_clothing(match):
        name_match = re.search(r"'name': '([^']*)'", match.group())
        dni_match = re.search(r"'dni': '([^']*)'", match.group())
        age_match = re.search(r"'age': (\d+)", match.group())
        terms_match = re.search(r"'terms_accepted': (True|False)", match.group())
        
        name = name_match.group(1) if name_match else "Test User"
        dni = dni_match.group(1) if dni_match else "12345678"
        age = age_match.group(1) if age_match else "25"
        terms = terms_match.group(1) if terms_match else "True"
        
        return f"""visitor_data = {{
                'participants': [{{
                    'name': '{name}',
                    'dni': '{dni}',
                    'age': {age},
                    'clothing_size': None
                }}],
                'terms_accepted': {terms},
                'participants_count': 1
            }}"""
    
    new_content = re.sub(old_pattern_no_clothing, replace_visitor_data_no_clothing, new_content, flags=re.MULTILINE | re.DOTALL)
    
    # Escribir el archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ {file_path} actualizado")

def main():
    """Función principal"""
    test_files = [
        'test_service.py',
        'test_integration.py'
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            update_test_file(test_file)
        else:
            print(f"❌ {test_file} no encontrado")

if __name__ == "__main__":
    main()
