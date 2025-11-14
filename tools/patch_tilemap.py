#!/usr/bin/env python3
import json
from pathlib import Path

TILEMAP_PATH = Path("generative_agents/frontend/static/assets/village/tilemap/tilemap.json")
OUTPUT_PATH = TILEMAP_PATH.with_name("tilemap_patched.json")


def load_tilemap(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_tilemap(data, path: Path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)


def get_layer(tilemap, name: str):
    for layer in tilemap.get("layers", []):
        if layer.get("name") == name:
            return layer
    raise KeyError(f"Layer '{name}' not found")


def fill_rect_on_layer(layer, width: int, gid: int, x0: int, y0: int, w: int, h: int):
    data = layer.get("data")
    if not isinstance(data, list):
        raise ValueError(f"Layer '{layer.get('name')}' has no 'data' array")
    for y in range(y0, y0 + h):
        row_index = y * width
        for x in range(x0, x0 + w):
            idx = row_index + x
            data[idx] = gid


def main():
    tilemap = load_tilemap(TILEMAP_PATH)
    width = tilemap.get("width")
    height = tilemap.get("height") or tilemap.get("layers", [{}])[0].get("height")

    # 定义中心广场区域（居中，大小 14x14）
    cx, cy = width // 2, height // 2
    plaza_w, plaza_h = 14, 14
    x0, y0 = max(0, cx - plaza_w // 2), max(0, cy - plaza_h // 2)

    # 基础地面：使用全局 gid=2（CuteRPG_Field_B 的第2号瓦片，常见草地/地面）
    ground_gid = 2

    # 清理建筑/装饰/前景，移除碰撞
    target_clear_layers = [
        "Wall",
        "Interior Furniture L1",
        "Interior Furniture L2 ",
        "Foreground L1",
        "Foreground L2",
        "Collisions",
        "Object Interaction Blocks",
    ]

    # 在外部地面层铺设统一地面
    exterior_ground = get_layer(tilemap, "Exterior Ground")
    fill_rect_on_layer(exterior_ground, width, ground_gid, x0, y0, plaza_w, plaza_h)

    # 清理指定图层方块：用 0 清空
    for lname in target_clear_layers:
        layer = get_layer(tilemap, lname)
        fill_rect_on_layer(layer, width, 0, x0, y0, plaza_w, plaza_h)

    # 可选：在广场周围布置简单边框碰撞（blocks 的 firstgid=32125），此处仅示例在广场外围一圈设置碰撞
    try:
        collisions = get_layer(tilemap, "Collisions")
        border_gid = 32125
        # 顶边和底边
        for x in range(x0, x0 + plaza_w):
            collisions["data"][y0 * width + x] = 0  # 顶边清空，留出入口
            collisions["data"][((y0 + plaza_h - 1) * width) + x] = border_gid
        # 左右边
        for y in range(y0, y0 + plaza_h):
            collisions["data"][y * width + x0] = border_gid
            collisions["data"][y * width + (x0 + plaza_w - 1)] = border_gid
    except KeyError:
        pass

    save_tilemap(tilemap, OUTPUT_PATH)
    print(f"Patched tilemap saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()