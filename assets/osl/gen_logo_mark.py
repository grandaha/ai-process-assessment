# Generate a transparent PNG of the OSL dot-mark from logo-mark.svg coords. Stdlib only.
# Supersampled for clean anti-aliased edges. Painter order matches the SVG (orange then blue).
import struct, zlib, sys

OUT = 3          # output scale (100x102 -> 300x306)
SS = 4           # supersample factor for anti-aliasing
W, H, R = 100 * OUT, 102 * OUT, 9 * OUT
ORANGE = (217, 110, 58)   # #D96E3A
BLUE = (3, 77, 116)       # #034D74
CIRCLES = ([(c[0]*OUT, c[1]*OUT, ORANGE) for c in
            [(50,15),(50,33),(50,69),(50,87),(34.41,42),(65.59,42),
             (65.59,60),(18.82,33),(81.18,33),(81.18,69)]]
           + [(c[0]*OUT, c[1]*OUT, BLUE) for c in [(34.41,60),(18.82,69)]])

hw, hh = W * SS, H * SS
hi = bytearray(hw * hh * 4)            # hi-res RGBA, binary coverage
for cx, cy, col in CIRCLES:
    rr = (R * SS) ** 2
    x0, x1 = int((cx-R)*SS), int((cx+R)*SS)+1
    y0, y1 = int((cy-R)*SS), int((cy+R)*SS)+1
    for y in range(max(0, y0), min(hh, y1)):
        for x in range(max(0, x0), min(hw, x1)):
            dx, dy = x + 0.5 - cx*SS, y + 0.5 - cy*SS
            if dx*dx + dy*dy <= rr:
                i = (y*hw + x) * 4
                hi[i], hi[i+1], hi[i+2], hi[i+3] = col[0], col[1], col[2], 255

raw = bytearray()
n = SS * SS
for y in range(H):
    raw.append(0)                      # PNG filter byte (None) per scanline
    for x in range(W):
        sr = sg = sb = sa = 0
        for yy in range(SS):
            base = ((y*SS + yy) * hw + x*SS) * 4
            for xx in range(SS):
                i = base + xx*4
                if hi[i+3]:
                    sr += hi[i]; sg += hi[i+1]; sb += hi[i+2]; sa += 1
        if sa:
            raw += bytes((sr//sa, sg//sa, sb//sa, sa*255//n))
        else:
            raw += b"\x00\x00\x00\x00"

def _chunk(typ, data):
    c = typ + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)

png = (b"\x89PNG\r\n\x1a\n"
       + _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
       + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
       + _chunk(b"IEND", b""))
open(sys.argv[1], "wb").write(png)
print(f"wrote {sys.argv[1]} ({W}x{H}, {len(png)} bytes)")
