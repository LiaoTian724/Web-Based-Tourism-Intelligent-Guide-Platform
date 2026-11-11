"""美食和文创图片的来源与版权信息。"""

from urllib.parse import quote


COMMONS_URL = "https://commons.wikimedia.org/wiki/File:"


def create_credit(label, filename, author, license_name, license_url):
    """生成图片版权信息。"""

    return {
        "label": label,
        "source_url": COMMONS_URL + quote(filename.replace(" ", "_")),
        "author": author,
        "license": license_name,
        "license_url": license_url,
        "changes": "缩放并重新编码为 WebP",
    }


PHOTO_CREDITS = {
    "noodles": create_credit(
        "门面实拍",
        "Largo do Senado Wong Chi Kei 25-03-2023.jpg",
        "LN9267",
        "CC BY-SA 4.0",
        "https://creativecommons.org/licenses/by-sa/4.0/",
    ),

    "tart": create_credit(
        "葡式蛋挞实拍",
        "MargaretCafe PasteisDeNata.JPG",
        "Jpatokal",
        "CC BY-SA 3.0",
        "https://creativecommons.org/licenses/by-sa/3.0/",
    ),

    "meal": create_credit(
        "门面实拍",
        "Near A-Ma Temple A Lorcha 05-10-2024.jpg",
        "LN9267",
        "CC BY-SA 4.0",
        "https://creativecommons.org/licenses/by-sa/4.0/",
    ),

    "curry": create_credit(
        "店内实拍",
        "MC 澳門 Macau Rua de Cinco de Outubro (Macao) restaurant 牛記咖喱美食 Nau Kee Curry Cuisine March 2025 R12S 08.jpg",
        "Mama AXunLong08",
        "CC0 1.0",
        "https://creativecommons.org/publicdomain/zero/1.0/",
    ),

    "bun": create_credit(
        "猪扒包实拍",
        "PorkChopBun.jpg",
        "Glio",
        "作者释入公有领域",
        COMMONS_URL + "PorkChopBun.jpg",
    ),

    "coffee": create_credit(
        "西多士与菠萝包实拍",
        "Food NAM PENG CAFE, Macau, 法蘭西多士, 菠蘿飽, 南屏雅敘, 茶餐廳, 新馬路, 澳門 (17308936702).jpg",
        "bryan...",
        "CC BY-SA 2.0",
        "https://creativecommons.org/licenses/by-sa/2.0/",
    ),
}


# 文创图片是 SVG，其他图片使用 WebP。
SVG_IMAGE_KEYS = {
    "postcards",
    "stamp",
    "tile",
}