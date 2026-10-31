"""Deterministic artwork from the private seed. The seed is hashed first, so the art does not reveal it,
and nothing about the student or institution goes into the image (NFT-05)."""
import hashlib


def render_svg(art_seed: str) -> str:
    d = hashlib.sha256(("disha-art-v1:" + art_seed).encode()).digest()
    hue = d[0] * 360 // 256
    bg = f"hsl({(hue + 180) % 360},35%,14%)"
    fg = f"hsl({hue},70%,60%)"
    accent = f"hsl({(hue + 40) % 360},75%,70%)"
    cells = []
    bits = int.from_bytes(d[1:9], "big")
    for row in range(5):
        for col in range(3):  # mirror columns 0-1 onto 4-3 for symmetry
            if (bits >> (row * 3 + col)) & 1:
                colour = accent if (row + col) % 4 == 0 else fg
                for c in {col, 4 - col}:
                    cells.append(f'<rect x="{40 + c * 24}" y="{40 + row * 24}" width="22" height="22" rx="4" fill="{colour}"/>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">'
        f'<rect width="200" height="200" rx="24" fill="{bg}"/>' + "".join(cells) + "</svg>"
    )
