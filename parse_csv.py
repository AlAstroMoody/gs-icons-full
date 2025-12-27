#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import json

def load_craft_json(filename):
    """Загружает craft.json и создает словарь для поиска по имени"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Создаем словарь: имя -> иконка
    name_to_icon = {}
    for item in data:
        name = item.get('name', '').strip()
        src = item.get('src', '').strip()
        if name and src:
            name_to_icon[name] = src
    
    return name_to_icon

def parse_csv_to_json(csv_filename, craft_json_filename, output_filename):
    """Парсит CSV файл и конвертирует в JSON"""
    
    # Загружаем справочник иконок из craft.json
    name_to_icon = load_craft_json(craft_json_filename)
    
    result = []
    
    with open(csv_filename, 'r', encoding='utf-8') as f:
        # Используем csv.reader для правильной обработки многострочных записей
        reader = csv.reader(f)
        
        # Пропускаем заголовки (первые 2 строки)
        next(reader, None)  # Пропускаем первую строку с заголовками
        next(reader, None)  # Пропускаем вторую строку с подзаголовком "Иконка"
        
        current_item = None
        desc_parts = []
        
        for row in reader:
            # Пропускаем полностью пустые строки
            if not row or all(not cell.strip() for cell in row):
                continue
            
            # Проверяем, есть ли имя в первой колонке (начало новой записи)
            name = row[0].strip() if len(row) > 0 and row[0] else ""
            
            if name:
                # Сохраняем предыдущий элемент
                if current_item and current_item['name']:
                    # Объединяем части описания
                    current_item['desc'] = '\n'.join(desc_parts).strip()
                    result.append(current_item)
                
                # Начинаем новую запись
                level = row[1].strip() if len(row) > 1 and row[1] else ""
                desc = row[3].strip() if len(row) > 3 and row[3] else ""
                icon = row[4].strip() if len(row) > 4 and row[4] else ""
                
                # Если иконка не указана, ищем по имени в craft.json
                if not icon and name:
                    icon = name_to_icon.get(name, "")
                
                # Инициализируем новую запись
                desc_parts = [desc] if desc else []
                current_item = {
                    'name': name,
                    'level': level,
                    'desc': '',  # Будет заполнено при сохранении
                    'icon': icon
                }
            else:
                # Это продолжение описания предыдущего элемента
                if current_item and len(row) > 3:
                    additional_desc = row[3].strip() if row[3] else ""
                    if additional_desc:
                        desc_parts.append(additional_desc)
        
        # Сохраняем последний элемент
        if current_item and current_item['name']:
            current_item['desc'] = '\n'.join(desc_parts).strip()
            result.append(current_item)
    
    # Сохраняем результат в JSON
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Обработано {len(result)} элементов")
    print(f"Результат сохранен в {output_filename}")

if __name__ == '__main__':
    csv_file = 'craft1_6.csv'
    craft_json_file = 'craft.json'
    output_file = 'craft1_6.json'
    
    parse_csv_to_json(csv_file, craft_json_file, output_file)

