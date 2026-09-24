coupledb = {}
# in memory storage


async def _get_lovers(cid: int):
    chat_data = coupledb.get(cid, {})
    if not isinstance(chat_data, dict):
        chat_data = {}
    lovers = chat_data.get("couple", {})
    return lovers if isinstance(lovers, dict) else {}


async def get_image(cid: int):
    chat_data = coupledb.get(cid, {})
    if not isinstance(chat_data, dict):
        return ""
    image = chat_data.get("img", "")
    return image if isinstance(image, str) else ""


async def get_couple(cid: int, date: str):
    lovers = await _get_lovers(cid)
    return lovers.get(date, False)


async def save_couple(cid: int, date: str, couple: dict, img: str):
    if not isinstance(coupledb.get(cid), dict):
        coupledb[cid] = {"couple": {}, "img": ""}
    if not isinstance(coupledb[cid].get("couple"), dict):
        coupledb[cid]["couple"] = {}
    coupledb[cid]["couple"][date] = couple
    coupledb[cid]["img"] = img
