#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import json
import re

def normalize_icon_extension(icon):
    """Заменяет расширение .blp/.BLP на .png для иконок"""
    if not icon:
        return icon
    # Обрабатываем оба варианта: .blp и .BLP
    icon_lower = icon.lower()
    if icon_lower.endswith('.blp'):
        return icon[:-4] + '.png'
    return icon

def get_direct_icon(name):
    """Возвращает иконку напрямую для определенных предметов"""
    # Прямое назначение иконок
    direct_icons = {
        'Сырный Двигатель': 'BTNCheese.png',
    }
    return direct_icons.get(name, None)

def get_name_mapping(name):
    """Возвращает альтернативное название для поиска в craft.json по специальным правилам"""
    # Специальные правила сопоставления названий
    name_mappings = {
        'Корпус "Буро"': 'Корпус Буро',
        'Полуфилософский камень': 'Полу-философский камень',
        'Огнемет': 'Огнемёт',
        'Руна': 'Древняя Руна',
        'Зелье магии': 'Магическое Зелье',
        'Зелье интеллекта': 'Зелье интелекта',
    }
    return name_mappings.get(name, name)

def normalize_name_for_search(name):
    """Нормализует имя для поиска: приводит к нижнему регистру и заменяет похожие символы"""
    if not name:
        return name
    name_lower = name.lower()
    # Заменяем латинские символы на кириллические для унификации
    # a -> а, e -> е, o -> о, p -> р, c -> с, x -> х, y -> у
    replacements = {
        'a': 'а',  # латинская a -> кириллическая а
        'e': 'е',  # латинская e -> кириллическая е
        'o': 'о',  # латинская o -> кириллическая о
        'p': 'р',  # латинская p -> кириллическая р
        'c': 'с',  # латинская c -> кириллическая с
        'x': 'х',  # латинская x -> кириллическая х
        'y': 'у',  # латинская y -> кириллическая у
    }
    normalized = ''
    for char in name_lower:
        normalized += replacements.get(char, char)
    return normalized

def get_relic_base_name(name):
    """Извлекает базовое имя реликвария (без номера в скобках)"""
    if not name.startswith('Реликварий'):
        return None
    # Ищем скобку с номером в конце
    match = re.match(r'^(Реликварий .+?)\(\d+\)$', name)
    if match:
        return match.group(1)
    return None

def fill_relic_icons(result):
    """Заполняет отсутствующие иконки реликвариев из других версий с тем же базовым именем"""
    # Создаем словарь: базовое имя -> иконка
    relics_with_icons = {}
    relics_without_icons = []
    
    for item in result:
        base_name = get_relic_base_name(item['name'])
        if base_name:
            if item['icon']:
                # У этого реликвария есть иконка - сохраняем её для базового имени
                if base_name not in relics_with_icons:
                    relics_with_icons[base_name] = item['icon']
            else:
                # У этого реликвария нет иконки
                relics_without_icons.append((item, base_name))
    
    # Заполняем отсутствующие иконки
    for item, base_name in relics_without_icons:
        if base_name in relics_with_icons:
            item['icon'] = relics_with_icons[base_name]

def load_craft_json(filename):
    """Загружает craft.json и создает словарь для поиска по имени (без учета регистра и похожих символов)"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Создаем словарь: нормализованное имя -> иконка
    name_to_icon = {}
    for item in data:
        name = item.get('name', '').strip()
        src = item.get('src', '').strip()
        if name and src:
            # Нормализуем расширение иконки и используем нормализованное имя как ключ
            normalized_name = normalize_name_for_search(name)
            name_to_icon[normalized_name] = normalize_icon_extension(src)
    
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
                
                # Если иконка не указана, ищем по имени в craft.json (без учета регистра и похожих символов)
                if not icon and name:
                    # Сначала проверяем прямое назначение иконок
                    direct_icon = get_direct_icon(name)
                    if direct_icon:
                        icon = direct_icon
                    else:
                        # Затем проверяем специальные правила сопоставления
                        mapped_name = get_name_mapping(name)
                        normalized_name = normalize_name_for_search(mapped_name)
                        icon = name_to_icon.get(normalized_name, "")
                
                # Нормализуем расширение иконки (.blp -> .png)
                icon = normalize_icon_extension(icon)
                
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
    
    # Заполняем отсутствующие иконки реликвариев из других версий
    fill_relic_icons(result)
    
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

