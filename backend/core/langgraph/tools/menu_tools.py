from typing import Dict, List, Any, Optional
import logging
from ...db import get_menu_categories, get_menu_by_id, get_menu_by_name

logger = logging.getLogger("menu_tools")

def get_menu_info(menu_name: str = None) -> Dict[str, Any]:
    """
    메뉴 이름으로 메뉴 정보 가져오기
    
    Args:
        menu_name: 메뉴 이름 (ex. '아메리카노', '카페라떼')
    
    Returns:
        메뉴 정보 딕셔너리 (이름, 가격, 옵션 등)
    """
    try:
        logger.info(f"메뉴 정보 조회: {menu_name}")
        
        if not menu_name:
            return {"status": "error", "message": "메뉴 이름이 필요합니다."}
        
        menu = get_menu_by_name(menu_name)
        
        if not menu:
            all_menus = []
            categories = get_menu_categories()
            for category in categories:
                all_menus.extend(category["items"])
            
            matched_menus = []
            for item in all_menus:
                if menu_name.lower() in item["name"].lower():
                    matched_menus.append(item)
            
            if matched_menus:
                menu = min(matched_menus, key=lambda x: len(x["name"]))
                logger.info(f"부분 일치 메뉴 발견: {menu['name']}")
            else:
                return {"status": "error", "message": f"'{menu_name}' 메뉴를 찾을 수 없습니다."}
        
        logger.info(f"메뉴 정보 조회 결과: {menu}")
        return {"status": "success", "menu": menu}
        
    except Exception as e:
        logger.error(f"메뉴 정보 조회 오류: {str(e)}")
        return {"status": "error", "message": f"메뉴 정보 조회 중 오류 발생: {str(e)}"}

def get_all_menus() -> Dict[str, Any]:
    """
    모든 메뉴 정보 가져오기
    
    Returns:
        카테고리별 메뉴 목록
    """
    try:
        logger.info("전체 메뉴 목록 조회")
        
        categories = get_menu_categories()
        logger.info(f"메뉴 카테고리 {len(categories)}개 조회 완료")
        
        return {"status": "success", "categories": categories}
        
    except Exception as e:
        logger.error(f"전체 메뉴 목록 조회 오류: {str(e)}")
        return {"status": "error", "message": f"메뉴 목록 조회 중 오류 발생: {str(e)}"}

def get_menu_options(menu_name: str) -> Dict[str, Any]:
    """
    메뉴의 옵션 정보 가져오기
    
    Args:
        menu_name: 메뉴 이름
    
    Returns:
        메뉴 옵션 정보 (필수 옵션, 선택 옵션 등)
    """
    try:
        logger.info(f"메뉴 옵션 조회: {menu_name}")
        
        # 메뉴 정보 가져오기
        menu_info = get_menu_info(menu_name)
        
        if menu_info["status"] == "error":
            return menu_info
        
        menu = menu_info["menu"]
        
        required_options = {}
        optional_options = {}
        
        if "required_options" in menu:
            required_options = menu["required_options"]
        else:
            if "coffee" in menu.get("category", "").lower() or "티" in menu.get("category", "").lower():
                required_options = {
                    "온도": [
                        {"name": "핫", "price_adjustment": 0},
                        {"name": "아이스", "price_adjustment": 500}
                    ],
                    "크기": [
                        {"name": "레귤러", "price_adjustment": 0},
                        {"name": "라지", "price_adjustment": 1000}
                    ]
                }
        
        if "optional_options" in menu:
            optional_options = menu["optional_options"]
        else:
            if "커피" in menu.get("category", "").lower():
                optional_options = {
                    "카페인": [
                        {"name": "일반", "price_adjustment": 0},
                        {"name": "디카페인", "price_adjustment": 500}
                    ]
                }
            elif "티" in menu.get("category", "").lower():
                optional_options = {
                    "토핑": [
                        {"name": "휘핑크림 없음", "price_adjustment": 0},
                        {"name": "휘핑크림 추가", "price_adjustment": 500}
                    ]
                }
        
        logger.info(f"필수 옵션: {required_options}")
        logger.info(f"선택 옵션: {optional_options}")
        
        return {
            "status": "success", 
            "required_options": required_options,
            "optional_options": optional_options,
            "base_price": menu.get("base_price", 0)
        }
        
    except Exception as e:
        logger.error(f"메뉴 옵션 조회 오류: {str(e)}")
        return {"status": "error", "message": f"메뉴 옵션 조회 중 오류 발생: {str(e)}"} 