import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models.menu import MenuCategory, MenuItem, MenuOption, MENU_DATA

DB_PATH = Path("data/menu.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS menu_options")
    cursor.execute("DROP TABLE IF EXISTS menu_items")
    cursor.execute("DROP TABLE IF EXISTS categories")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY,
        category_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        base_price INTEGER NOT NULL,
        image_url TEXT,
        is_available BOOLEAN DEFAULT 1,
        required_options TEXT DEFAULT '{}',
        optional_options TEXT DEFAULT '{}',
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_item_id INTEGER,
        name TEXT NOT NULL,
        price_adjustment INTEGER DEFAULT 0,
        FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
    )
    """)
    
    conn.commit()
    conn.close()

def populate_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM menu_options")
    cursor.execute("DELETE FROM menu_items")
    cursor.execute("DELETE FROM categories")
    
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='menu_options'")
    except sqlite3.OperationalError:
        pass
    
    for category in MENU_DATA:
        cursor.execute(
            "INSERT INTO categories (id, name, description) VALUES (?, ?, ?)",
            (category.id, category.name, category.description)
        )
        
        for item in category.items:
            required_options_json = "{}"
            optional_options_json = "{}"
            
            if hasattr(item, 'required_options') and item.required_options:
                required_options_dict = {}
                for key, options in item.required_options.items():
                    required_options_dict[key] = [{"id": opt.id, "name": opt.name, "price_adjustment": opt.price_adjustment} for opt in options]
                required_options_json = json.dumps(required_options_dict, ensure_ascii=False)
            
            if hasattr(item, 'optional_options') and item.optional_options:
                optional_options_dict = {}
                for key, options in item.optional_options.items():
                    optional_options_dict[key] = [{"id": opt.id, "name": opt.name, "price_adjustment": opt.price_adjustment} for opt in options]
                optional_options_json = json.dumps(optional_options_dict, ensure_ascii=False)
            
            cursor.execute(
                """
                INSERT INTO menu_items 
                (id, category_id, name, description, base_price, image_url, is_available, required_options, optional_options)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (item.id, item.category_id, item.name, item.description,
                 item.base_price, item.image_url, item.is_available, 
                 required_options_json, optional_options_json)
            )
            
            all_options = []
            
            if hasattr(item, 'required_options'):
                for options_list in item.required_options.values():
                    all_options.extend(options_list)
            
            if hasattr(item, 'optional_options'):
                for options_list in item.optional_options.values():
                    all_options.extend(options_list)
            
            if hasattr(item, 'options') and item.options:
                all_options.extend(item.options)
            
            for option in all_options:
                cursor.execute(
                    """
                    INSERT INTO menu_options 
                    (menu_item_id, name, price_adjustment)
                    VALUES (?, ?, ?)
                    """,
                    (item.id, option.name, option.price_adjustment)
                )
    
    conn.commit()
    conn.close()

def get_menu_categories() -> List[MenuCategory]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # dict 형태
    cursor = conn.cursor()
    
    categories = []
    
    cursor.execute("SELECT id, name, description FROM categories")
    for category_row in cursor.fetchall():
        cat_id = category_row['id']
        items = []
        
        cursor.execute(
            """
            SELECT id, name, description, base_price, image_url, is_available, 
                   required_options, optional_options
            FROM menu_items
            WHERE category_id = ?
            """,
            (cat_id,)
        )
        
        for item_row in cursor.fetchall():
            item_id = item_row['id']
            
            required_options = {}
            optional_options = {}
            
            if item_row['required_options']:
                try:
                    required_options_data = json.loads(item_row['required_options'])
                    for category_name, options_data in required_options_data.items():
                        required_options[category_name] = [
                            MenuOption(id=opt['id'], name=opt['name'], price_adjustment=opt['price_adjustment'])
                            for opt in options_data
                        ]
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing required options: {e}")
            
            if item_row['optional_options']:
                try:
                    optional_options_data = json.loads(item_row['optional_options'])
                    for category_name, options_data in optional_options_data.items():
                        optional_options[category_name] = [
                            MenuOption(id=opt['id'], name=opt['name'], price_adjustment=opt['price_adjustment'])
                            for opt in options_data
                        ]
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing optional options: {e}")
            
            options = []
            cursor.execute(
                """
                SELECT id, name, price_adjustment
                FROM menu_options
                WHERE menu_item_id = ?
                """,
                (item_id,)
            )
            for opt_row in cursor.fetchall():
                options.append(MenuOption(
                    id=opt_row['id'],
                    name=opt_row['name'],
                    price_adjustment=opt_row['price_adjustment']
                ))
            
            menu_item = MenuItem(
                id=item_row['id'],
                category_id=cat_id,
                name=item_row['name'],
                description=item_row['description'],
                base_price=item_row['base_price'],
                image_url=item_row['image_url'],
                is_available=bool(item_row['is_available']),
                options=options
            )
            
            menu_item.required_options = required_options
            menu_item.optional_options = optional_options
            
            items.append(menu_item)
        
        categories.append(MenuCategory(
            id=cat_id,
            name=category_row['name'],
            description=category_row['description'],
            items=items
        ))
    
    conn.close()
    return categories

def get_menu_item(item_id: int) -> Optional[MenuItem]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, category_id, name, description, base_price, image_url, is_available,
               required_options, optional_options
        FROM menu_items
        WHERE id = ?
        """,
        (item_id,)
    )
    
    item_row = cursor.fetchone()
    if not item_row:
        conn.close()
        return None
    
    required_options = {}
    optional_options = {}
    
    if item_row['required_options']:
        try:
            required_options_data = json.loads(item_row['required_options'])
            for category_name, options_data in required_options_data.items():
                required_options[category_name] = [
                    MenuOption(id=opt['id'], name=opt['name'], price_adjustment=opt['price_adjustment'])
                    for opt in options_data
                ]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing required options: {e}")
    
    if item_row['optional_options']:
        try:
            optional_options_data = json.loads(item_row['optional_options'])
            for category_name, options_data in optional_options_data.items():
                optional_options[category_name] = [
                    MenuOption(id=opt['id'], name=opt['name'], price_adjustment=opt['price_adjustment'])
                    for opt in options_data
                ]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing optional options: {e}")
    
    cursor.execute(
        """
        SELECT id, name, price_adjustment
        FROM menu_options
        WHERE menu_item_id = ?
        """,
        (item_id,)
    )
    
    options = [
        MenuOption(id=opt_row['id'], name=opt_row['name'], price_adjustment=opt_row['price_adjustment'])
        for opt_row in cursor.fetchall()
    ]
    
    conn.close()
    
    menu_item = MenuItem(
        id=item_row['id'],
        category_id=item_row['category_id'],
        name=item_row['name'],
        description=item_row['description'],
        base_price=item_row['base_price'],
        image_url=item_row['image_url'],
        is_available=bool(item_row['is_available']),
        options=options
    )
    
    menu_item.required_options = required_options
    menu_item.optional_options = optional_options
    
    return menu_item

def get_menu_by_name(menu_name: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, category_id, name, description, base_price, image_url, is_available,
               required_options, optional_options
        FROM menu_items
        WHERE name LIKE ?
        """,
        (f"%{menu_name}%",)
    )
    
    item_row = cursor.fetchone()
    if not item_row:
        conn.close()
        return None
    
    cursor.execute(
        """
        SELECT name
        FROM categories
        WHERE id = ?
        """,
        (item_row['category_id'],)
    )
    
    cat_result = cursor.fetchone()
    category_name = cat_result['name'] if cat_result else "기타"
    
    cursor.execute(
        """
        SELECT id, name, price_adjustment
        FROM menu_options
        WHERE menu_item_id = ?
        """,
        (item_row['id'],)
    )
    
    options = [
        {
            "id": opt_row['id'],
            "name": opt_row['name'],
            "price_adjustment": opt_row['price_adjustment']
        }
        for opt_row in cursor.fetchall()
    ]
    
    required_options = {}
    optional_options = {}
    
    if item_row['required_options'] and item_row['required_options'] != '{}':
        try:
            required_options = json.loads(item_row['required_options'])
        except json.JSONDecodeError:
            print(f"Error parsing required options JSON: {item_row['required_options']}")
    
    if item_row['optional_options'] and item_row['optional_options'] != '{}':
        try:
            optional_options = json.loads(item_row['optional_options'])
        except json.JSONDecodeError:
            print(f"Error parsing optional options JSON: {item_row['optional_options']}")
    
    conn.close()
    
    return {
        "id": item_row['id'],
        "name": item_row['name'],
        "description": item_row['description'],
        "base_price": item_row['base_price'],
        "image_url": item_row['image_url'],
        "is_available": bool(item_row['is_available']),
        "category": category_name,
        "options": options,
        "required_options": required_options,
        "optional_options": optional_options
    }

def get_menu_by_id(item_id: int) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, category_id, name, description, base_price, image_url, is_available
        FROM menu_items
        WHERE id = ?
        """,
        (item_id,)
    )
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return None
    
    item_id, cat_id, name, desc, base_price, image_url, is_available = result
    
    cursor.execute(
        """
        SELECT name
        FROM categories
        WHERE id = ?
        """,
        (cat_id,)
    )
    
    cat_result = cursor.fetchone()
    category_name = cat_result[0] if cat_result else "기타"
    
    cursor.execute(
        """
        SELECT id, name, price_adjustment
        FROM menu_options
        WHERE menu_item_id = ?
        """,
        (item_id,)
    )
    
    options = [
        {"name": opt_name, "price_adjustment": price_adj}
        for opt_id, opt_name, price_adj in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        "id": item_id,
        "name": name,
        "description": desc,
        "price": base_price,
        "category": category_name,
        "image_url": image_url,
        "is_available": bool(is_available),
        "options": options
    } 