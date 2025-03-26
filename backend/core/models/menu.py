from typing import List, Optional, Dict
from pydantic import BaseModel

class MenuOption(BaseModel):
    id: int
    name: str
    price_adjustment: int = 0

class OptionCategory(BaseModel):
    id: int
    name: str
    options: List[MenuOption] = []

class MenuItem(BaseModel):
    id: int
    category_id: int
    name: str
    description: str
    base_price: int
    image_url: Optional[str] = None
    is_available: bool = True
    required_options: Dict[str, List[MenuOption]] = {}  # 필수 옵션
    optional_options: Dict[str, List[MenuOption]] = {}  # 선택 옵션

class MenuCategory(BaseModel):
    id: int
    name: str
    description: str
    items: List[MenuItem] = []

TEMPERATURE_OPTIONS = [
    MenuOption(id=1, name="핫", price_adjustment=0),
    MenuOption(id=2, name="아이스", price_adjustment=500),
]

SIZE_OPTIONS = [
    MenuOption(id=3, name="레귤러", price_adjustment=0),
    MenuOption(id=4, name="라지", price_adjustment=1000),
]

DECAF_OPTIONS = [
    MenuOption(id=5, name="일반", price_adjustment=0),
    MenuOption(id=6, name="디카페인", price_adjustment=500),
]

WHIPPED_CREAM_OPTIONS = [
    MenuOption(id=7, name="휘핑크림 없음", price_adjustment=0),
    MenuOption(id=8, name="휘핑크림 추가", price_adjustment=500),
]

MENU_DATA = [
    MenuCategory(
        id=1,
        name="커피",
        description="에스프레소 기반의 다양한 커피 메뉴",
        items=[
            MenuItem(
                id=1,
                category_id=1,
                name="아메리카노",
                description="깊고 진한 에스프레소의 맛을 느낄 수 있는 클래식한 커피",
                base_price=4500,
                image_url="/images/menu/americano.jpg",
                required_options={
                    "온도": TEMPERATURE_OPTIONS,
                    "크기": SIZE_OPTIONS,
                },
                optional_options={
                    "카페인": DECAF_OPTIONS,
                }
            ),
            MenuItem(
                id=2,
                category_id=1,
                name="카페라떼",
                description="부드러운 우유와 에스프레소의 완벽한 조화",
                base_price=5000,
                image_url="/images/menu/latte.jpg",
                required_options={
                    "온도": TEMPERATURE_OPTIONS,
                    "크기": SIZE_OPTIONS,
                },
                optional_options={
                    "카페인": DECAF_OPTIONS,
                }
            ),
        ]
    ),
    MenuCategory(
        id=2,
        name="티",
        description="다양한 프리미엄 티 메뉴",
        items=[
            MenuItem(
                id=3,
                category_id=2,
                name="그린티 라떼",
                description="고급 말차와 우유의 조화",
                base_price=5500,
                image_url="/images/menu/green-tea-latte.jpg",
                required_options={
                    "온도": TEMPERATURE_OPTIONS,
                    "크기": SIZE_OPTIONS,
                },
                optional_options={
                    "토핑": WHIPPED_CREAM_OPTIONS,
                }
            ),
            MenuItem(
                id=4,
                category_id=2,
                name="캐모마일",
                description="진정 효과가 있는 캐모마일 티",
                base_price=4000,
                image_url="/images/menu/chamomile.jpg",
                required_options={
                    "온도": TEMPERATURE_OPTIONS,
                    "크기": SIZE_OPTIONS,
                },
                optional_options={
                    "토핑": WHIPPED_CREAM_OPTIONS,
                }
            ),
        ]
    ),
    MenuCategory(
        id=3,
        name="디저트",
        description="신선한 베이커리와 디저트",
        items=[
            MenuItem(
                id=5,
                category_id=3,
                name="티라미수",
                description="이탈리아 전통 디저트",
                base_price=6500,
                image_url="/images/menu/tiramisu.jpg",
            ),
            MenuItem(
                id=6,
                category_id=3,
                name="치즈케이크",
                description="부드러운 뉴욕 치즈케이크",
                base_price=6000,
                image_url="/images/menu/cheesecake.jpg",
            ),
        ]
    ),
] 