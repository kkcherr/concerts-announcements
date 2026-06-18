#!/usr/bin/env python3
"""Furniture layout plans for 3-floor house."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec

C = {
    'wall':     '#252525', 'floor':    '#F2F0EB', 'eaves':    '#E0DDD4',
    'bath_rm':  '#DDE8F0', 'utility':  '#EEEEEE',
    'bed':      '#C4D8EC', 'pillow':   '#E2EDF7', 'headboard':'#7FA8C4',
    'sofa':     '#A8C4A8', 'desk':     '#C8B8E0', 'wardrobe': '#E0CCAA',
    'table':    '#EED9A8', 'chair':    '#E0C898', 'storage':  '#D4C4B0',
    'bath':     '#CCDEE8', 'kitchen':  '#E8E4DC', 'island':   '#D8D4CC',
    'rug':      '#C8BEB2', 'tv':       '#888888', 'plant':    '#7CB87C',
    'window':   '#AED6F1', 'stair':    '#D4C8A4',
}

def R(ax, x, y, w, h, c, ec='#555555', lw=0.7, z=3, alpha=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.04',
                                fc=c, ec=ec, lw=lw, zorder=z, alpha=alpha))

def T(ax, x, y, s, fs=5.5, col='#333333', bold=False, z=20, ha='center', va='center'):
    ax.text(x, y, s, fontsize=fs, color=col,
            fontweight='bold' if bold else 'normal',
            ha=ha, va=va, zorder=z, multialignment='center')

def Circ(ax, cx, cy, r, c, ec='#555555', lw=0.7, z=3):
    ax.add_patch(plt.Circle((cx, cy), r, fc=c, ec=ec, lw=lw, zorder=z))

def darr(ax, x0, y0, x1, y1, label, fs=5.5, off=0.18):
    mx, my = (x0+x1)/2, (y0+y1)/2
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='<->', color='#777777', lw=0.8))
    if x0 == x1:
        ax.text(mx - off, my, label, fontsize=fs, color='#666666',
                ha='right', va='center', rotation=90)
    else:
        ax.text(mx, my - off, label, fontsize=fs, color='#666666',
                ha='center', va='top')

def setup(ax, title, xlim, ylim):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_facecolor('#F8F7F4')
    ax.set_title(title, fontsize=9, fontweight='bold', pad=6, color='#1A1A2E')


# ──────────────────────────────────────────────────────────────────────────────
# FIRST FLOOR — CHILD'S ROOM
# ──────────────────────────────────────────────────────────────────────────────
def draw_first_floor(ax):
    setup(ax, "FIRST FLOOR  ·  Child's Room  +  En-Suite Bathroom", (-1, 11.8), (-1.2, 7.5))
    W, H, ox, oy, e = 9.86, 5.02, 0.5, 0.8, 1.15

    # Eave triangles
    for pts in [[(ox,oy+e),(ox+e,oy),(ox+e,oy+e)],
                [(ox+W-e,oy),(ox+W,oy+e),(ox+W-e,oy+e)],
                [(ox,oy+H-e),(ox+e,oy+H),(ox+e,oy+H-e)],
                [(ox+W-e,oy+H-e),(ox+W-e,oy+H),(ox+W,oy+H-e)]]:
        ax.add_patch(mpatches.Polygon(pts, fc=C['eaves'], ec=C['wall'], lw=1.5, zorder=1))

    # Main room polygon
    ax.add_patch(mpatches.Polygon([
        (ox+e,oy),(ox+W-e,oy),(ox+W,oy+e),(ox+W,oy+H-e),
        (ox+W-e,oy+H),(ox+e,oy+H),(ox,oy+H-e),(ox,oy+e),
    ], fc=C['floor'], ec=C['wall'], lw=2.2, zorder=1))

    # En-suite (top-left, 2.6 × 2.8)
    bx, by = ox, oy+H-2.8
    R(ax, bx, by, 2.6, 2.8, C['bath_rm'], ec=C['wall'], lw=2, z=2)
    R(ax, bx+0.1, by+1.85, 1.55, 0.82, C['bath'], ec='#7799BB'); T(ax,bx+0.88,by+2.25,'Bath',4.5)
    R(ax, bx+0.1, by+0.8, 0.48, 0.72, '#F5F5F5', ec='#888888'); T(ax,bx+0.34,by+1.15,'WC',4.5)
    R(ax, bx+0.85, by+0.8, 0.75, 0.6, '#E4EDE8', ec='#888888'); T(ax,bx+1.22,by+1.1,'Sink',4.5)
    R(ax, bx+1.75, by+1.85, 0.72, 0.82, C['bath'], ec='#7799BB'); T(ax,bx+2.11,by+2.25,'Shower',4)
    ax.add_patch(mpatches.Arc((bx+2.6,by+0.6),1.0,1.0,angle=0,theta1=90,theta2=180,
                               color='#AA8855',lw=0.8,zorder=5))
    T(ax, bx+1.3, by+0.3, 'EN-SUITE', 5, '#336699', True)

    # Skylights
    for slx in [ox+2.2, ox+6.8]:
        R(ax, slx, oy+H/2-0.22, 1.1, 0.44, C['window'], ec='#7799CC', lw=1.5, z=4, alpha=0.55)
    T(ax, ox+2.75, oy+H/2-0.55, '↑ Skylight', 4.5, '#6688AA')
    T(ax, ox+7.35, oy+H/2-0.55, '↑ Skylight', 4.5, '#6688AA')

    # Child's double bed (1.35 × 1.9) against right wall, centred vertically
    bw, bh = 1.35, 1.9
    bx2, by2 = ox+W-bw-0.22, oy+(H-bh)/2
    R(ax, bx2, by2, bw, bh, C['bed'], ec='#5588AA', lw=1.2, z=3)
    R(ax, bx2, by2+bh-0.22, bw, 0.22, C['headboard'], ec='#5588AA', lw=0.6, z=4)
    R(ax, bx2+0.08, by2+bh-0.5, 0.52, 0.25, C['pillow'], ec='#AAC4D8', lw=0.5, z=5)
    R(ax, bx2+0.75, by2+bh-0.5, 0.52, 0.25, C['pillow'], ec='#AAC4D8', lw=0.5, z=5)
    T(ax, bx2+bw/2, by2+0.72, "Child's\nDouble Bed\n1.35 × 1.9m", 5.5, '#1A3A5A')
    R(ax, bx2-0.55, by2+0.45, 0.48, 0.48, C['storage']); T(ax,bx2-0.31,by2+0.69,'Side\nTbl',4.5)
    R(ax, bx2-0.55, by2+1.1,  0.48, 0.48, C['storage']); T(ax,bx2-0.31,by2+1.34,'Side\nTbl',4.5)

    # Wardrobe top wall
    R(ax, ox+2.8, oy+H-0.65, 3.0, 0.62, C['wardrobe'], ec='#AA8844', lw=1)
    T(ax, ox+4.3, oy+H-0.34, 'Wardrobe  3.0m', 5.5)
    R(ax, ox+5.9, oy+H-0.65, 1.0, 0.62, C['wardrobe'], ec='#AA8844')
    T(ax, ox+6.4, oy+H-0.34, 'Drawers', 5)

    # Play table + 4 small chairs
    ptx, pty = ox+3.2, oy+0.9
    R(ax, ptx, pty, 1.1, 0.7, C['table'], ec='#AA9933'); T(ax,ptx+0.55,pty+0.35,'Play Table',5)
    for cx_, cy_ in [(ptx+0.05,pty+0.76),(ptx+0.62,pty+0.76),
                     (ptx+0.05,pty-0.38),(ptx+0.62,pty-0.38)]:
        R(ax, cx_, cy_, 0.38, 0.33, C['chair'], ec='#AA8833', lw=0.5)

    # Bean bag
    Circ(ax, ox+5.5, oy+1.2, 0.42, C['sofa']); T(ax, ox+5.5, oy+1.2, 'Bean\nBag', 4.5)

    # Toy shelves bottom wall
    R(ax, ox+e+0.15, oy+0.1, 4.2, 0.55, C['storage'], ec='#AA8844')
    T(ax, ox+e+2.25, oy+0.37, 'Toy Shelf + Storage  4.2m', 5.5)

    # Play area rug
    ax.add_patch(FancyBboxPatch((ptx-0.3,pty-0.5),2.9,1.9,
                                boxstyle='round,pad=0.15',
                                fc=C['rug'],ec='#B0A090',lw=0.8,alpha=0.3,zorder=2))

    # Future desk in right eave alcove
    R(ax, ox+W-1.22, oy+0.22, 0.95, 0.55, C['desk'], ec='#8866AA')
    T(ax, ox+W-0.75, oy+0.49, 'Future\nDesk', 5, '#553377')

    # Eave labels
    for lx_, ly_, lt_ in [(ox+0.3,oy+0.48,'Eaves'),(ox+W-0.3,oy+0.48,'Eaves'),
                           (ox+0.3,oy+H-0.48,'Eaves'),(ox+W-0.3,oy+H-0.48,'Eaves')]:
        T(ax, lx_, ly_, lt_, 4.5, '#999999')

    T(ax, ox+W/2+0.6, oy+3.0,  "CHILD'S ROOM", 10, '#1A3A6A', True)
    T(ax, ox+W/2+0.6, oy+2.52, "9.86m × 5.02m  (32'4\" × 16'6\")", 6, '#4466AA')

    darr(ax, ox, oy-0.75, ox+W, oy-0.75, "9.86m (32'4\")")
    darr(ax, ox+W+0.45, oy, ox+W+0.45, oy+H, "5.02m (16'6\")")


# ──────────────────────────────────────────────────────────────────────────────
# GROUND FLOOR — MASTER BEDROOM + KITCHEN/DINING
# ──────────────────────────────────────────────────────────────────────────────
def draw_ground_floor(ax):
    setup(ax, "GROUND FLOOR  ·  Master Bedroom  +  Kitchen / Dining Room",
          (-1, 14.5), (-1.5, 10.5))

    # MASTER BEDROOM 4.96 × 3.14
    mx, my, mw, mh = 0.3, 5.5, 4.96, 3.14
    R(ax, mx, my, mw, mh, C['floor'], ec=C['wall'], lw=2.5, z=1)
    R(ax, mx+1.5, my+mh-0.06, 1.5, 0.06, C['window'], ec='#7799CC', lw=0, z=6)  # window

    # En-suite shower room  1.5 × 1.9
    ex, ey = mx, my+mh
    R(ax, ex, ey, 1.5, 1.9, C['bath_rm'], ec=C['wall'], lw=2, z=2)
    R(ax, ex+0.08, ey+0.72, 1.0, 1.05, C['bath'], ec='#7799BB'); T(ax,ex+0.58,ey+1.22,'Walk-in\nShower',4.5)
    R(ax, ex+0.08, ey+0.1, 0.45, 0.5, '#F5F5F5', ec='#888888'); T(ax,ex+0.3,ey+0.35,'WC',4.5)
    R(ax, ex+0.78, ey+0.1, 0.62, 0.5, '#E4EDE8', ec='#888888'); T(ax,ex+1.09,ey+0.35,'Sink',4.5)
    T(ax, ex+0.75, ey+1.82, 'En-Suite', 5, '#336699', True)

    # Super king bed 1.8 × 2.0 centred on top wall
    skw, skh = 1.8, 2.0
    skx = mx + (mw - skw) / 2
    sky = my + mh - skh - 0.1
    R(ax, skx, sky, skw, skh, C['bed'], ec='#4488BB', lw=1.3, z=3)
    R(ax, skx, sky+skh-0.22, skw, 0.22, C['headboard'], ec='#4488BB', lw=0.8, z=4)
    R(ax, skx+0.1,   sky+skh-0.54, 0.7, 0.28, C['pillow'], ec='#AACCE0', lw=0.5, z=5)
    R(ax, skx+1.0,   sky+skh-0.54, 0.7, 0.28, C['pillow'], ec='#AACCE0', lw=0.5, z=5)
    T(ax, skx+skw/2, sky+0.8, 'Super King\n1.8m × 2.0m', 5.5, '#1A3A5A')
    R(ax, skx-0.58, sky+0.72, 0.5, 0.5, C['storage']); T(ax,skx-0.33,sky+0.97,'Side\nTbl',4.5)
    R(ax, skx+skw+0.08, sky+0.72, 0.5, 0.5, C['storage']); T(ax,skx+skw+0.33,sky+0.97,'Side\nTbl',4.5)

    # Wardrobes fitted left wall
    R(ax, mx+0.05, my+0.1, 0.62, 2.5, C['wardrobe'], ec='#AA8844', lw=1)
    T(ax, mx+0.36, my+1.35, 'W\nR\nB', 4.5)
    R(ax, mx+0.05, my+2.7, 0.62, 0.34, C['wardrobe'], ec='#AA8844')
    T(ax, mx+0.36, my+2.87, 'WRB', 4.5)

    # Ottoman bench foot of bed
    R(ax, skx+0.15, my+0.12, 1.5, 0.45, C['chair'], ec='#AA8833')
    T(ax, skx+0.9, my+0.35, 'Ottoman Bench', 5)

    # Dressing table right corner
    R(ax, mx+mw-1.05, my+0.12, 1.0, 0.48, C['desk'], ec='#8866AA')
    T(ax, mx+mw-0.55, my+0.36, 'Dressing\nTable', 5, '#553377')

    T(ax, mx+mw/2, my+1.78, 'MASTER BEDROOM', 8, '#1A3A6A', True)
    T(ax, mx+mw/2, my+1.38, "4.96m × 3.14m  (16'3\" × 10'4\")", 5.5, '#4466AA')

    darr(ax, mx, my-0.6, mx+mw, my-0.6, "4.96m (16'3\")")

    # STAIRCASE schematic
    for i in range(8):
        R(ax, mx+mw+0.15, my+1.5+i*0.42, 0.8, 0.38, C['stair'], ec='#BBAA77', lw=0.4)
    T(ax, mx+mw+0.55, my+4.7, 'Stairs\n↑ 1st Fl\n↓ Lower\nGround', 4.5, '#888866')

    # KITCHEN / DINING 6.59 × 6.44
    kx, ky, kw, kh = 6.4, 0.5, 6.59, 6.44
    R(ax, kx, ky, kw, kh, C['kitchen'], ec=C['wall'], lw=2.5, z=1)

    # Back wall units + ovens (already fitted)
    R(ax, kx+0.1, ky+kh-0.68, 5.2, 0.65, '#DDDDD5', ec='#999988', lw=1)
    R(ax, kx+0.35, ky+kh-0.68, 0.62, 0.65, '#555555', ec='#333333', lw=0.8, z=4)
    T(ax, kx+0.66, ky+kh-0.36, 'Oven', 4.5, 'white')
    R(ax, kx+1.05, ky+kh-0.68, 0.62, 0.65, '#555555', ec='#333333', lw=0.8, z=4)
    T(ax, kx+1.36, ky+kh-0.36, 'MW', 4.5, 'white')
    T(ax, kx+3.5, ky+kh-0.36, 'Wall Units + Tall Storage', 5, '#555544')

    # Right wall units & sink
    R(ax, kx+kw-0.65, ky+0.4, 0.62, 3.5, '#DDDDD5', ec='#999988', lw=1)
    T(ax, kx+kw-0.34, ky+2.15, 'Kitchen\nUnits', 5, '#555544')
    R(ax, kx+kw-0.6, ky+1.7, 0.5, 0.35, C['bath'], ec='#888888', lw=0.5)
    T(ax, kx+kw-0.35, ky+1.87, 'Sink', 4)

    # Island 2.8 × 1.0 (already fitted)
    ix, iy, iw, ih = kx+1.3, ky+2.8, 2.8, 1.0
    R(ax, ix, iy, iw, ih, C['island'], ec='#888877', lw=1.5, z=3)
    for bx_, by_ in [(ix+0.28,iy+0.28),(ix+0.72,iy+0.28),
                     (ix+0.28,iy+0.65),(ix+0.72,iy+0.65)]:
        Circ(ax, bx_, by_, 0.11, '#888888', ec='#555555', lw=0.5)
    T(ax, ix+1.6, iy+0.5, 'Island · Hob + Storage', 5, '#444433')
    R(ax, ix+0.8, iy+ih, 0.6, 0.14, '#CCCCCC', ec='#999999', lw=0.5, z=4)
    T(ax, ix+1.1, iy+ih+0.07, 'Hood', 3.5, '#666666')

    # Bar stools ×3
    for sx_ in [ix+0.4, ix+1.1, ix+2.1]:
        R(ax, sx_-0.2, iy-0.5, 0.38, 0.42, C['chair'], ec='#AA8833', lw=0.5)
    T(ax, ix+1.3, iy-0.62, 'Bar Stools ×3', 5)

    # Pendant lights (copper)
    for px_ in [ix+0.55, ix+1.1, ix+1.65, ix+2.2]:
        Circ(ax, px_, iy+1.32, 0.09, '#CC7755', ec='#995533', lw=0.5, z=5)

    # Wine fridge
    R(ax, ix, iy-0.82, 0.55, 0.62, '#CCCCCC', ec='#888888', lw=0.6)
    T(ax, ix+0.27, iy-0.51, 'Wine\nFridge', 4.5)

    # Dining table 2.2 × 1.1, 6-8 persons
    dtx, dty = kx+0.28, ky+0.5
    R(ax, dtx, dty, 2.2, 1.1, C['table'], ec='#AA9933', lw=1, z=3)
    T(ax, dtx+1.1, dty+0.55, 'Dining Table  2.2m\n6–8 persons', 5.5, '#3A3A22')
    for cx_ in [dtx+0.2, dtx+0.75, dtx+1.3, dtx+1.85]:
        R(ax, cx_-0.18, dty-0.48, 0.36, 0.4, C['chair'], ec='#AA8833', lw=0.5)
        R(ax, cx_-0.18, dty+1.18, 0.36, 0.4, C['chair'], ec='#AA8833', lw=0.5)
    ax.add_patch(FancyBboxPatch((dtx-0.3,dty-0.62),3.0,2.35,
                                boxstyle='round,pad=0.15',
                                fc=C['rug'],ec='#B0A090',lw=0.8,alpha=0.3,zorder=2))

    # Sliding doors to balcony
    R(ax, kx+kw-0.06, ky+0.3, 0.06, 2.0, C['window'], ec='#7799CC', lw=0, z=6)
    T(ax, kx+kw+0.35, ky+1.3, '↔ Balcony\nDoors', 4.5, '#336699', ha='left')

    # Plant
    Circ(ax, kx+5.7, ky+2.0, 0.26, C['plant'], ec='#508050', lw=0.6, z=3)
    T(ax, kx+5.7, ky+2.0, '🌿', 5.5)

    T(ax, kx+kw/2, ky+kh-1.45, 'KITCHEN / DINING', 8, '#1A3A6A', True)
    T(ax, kx+kw/2, ky+kh-1.85, "6.59m × 6.44m  (21'7\" × 21'2\")", 5.5, '#4466AA')

    darr(ax, kx, ky-0.6, kx+kw, ky-0.6, "6.59m (21'7\")")


# ──────────────────────────────────────────────────────────────────────────────
# LOWER GROUND FLOOR — GUEST BEDROOM + LIVING / HOME OFFICE
# ──────────────────────────────────────────────────────────────────────────────
def draw_lower_ground(ax):
    setup(ax, "LOWER GROUND FLOOR  ·  Guest Bedroom  +  Living Room  /  Home Office",
          (-1.2, 15.5), (-1.5, 9.0))

    # GUEST BEDROOM 5.38 × 3.25
    gx, gy, gw, gh = 0.3, 3.7, 5.38, 3.25
    R(ax, gx, gy, gw, gh, C['floor'], ec=C['wall'], lw=2.5, z=1)
    R(ax, gx-0.06, gy+0.8, 0.06, 1.4, C['window'], ec='#7799CC', lw=0, z=6)
    T(ax, gx-0.55, gy+1.5, '↔ Terrace', 4.5, '#336699', ha='right')

    # Guest bathroom (compact bath/shower)
    bx_, by_ = gx, gy+gh
    R(ax, bx_, by_, 2.1, 1.9, C['bath_rm'], ec=C['wall'], lw=2, z=2)
    R(ax, bx_+0.1, by_+0.88, 1.6, 0.82, C['bath'], ec='#7799BB')
    T(ax, bx_+0.9, by_+1.28, 'Bath / Shower', 4.5)
    R(ax, bx_+0.1, by_+0.1, 0.45, 0.62, '#F5F5F5', ec='#888888'); T(ax,bx_+0.32,by_+0.41,'WC',4.5)
    R(ax, bx_+0.78, by_+0.1, 0.65, 0.62, '#E4EDE8', ec='#888888'); T(ax,bx_+1.1,by_+0.41,'Sink',4.5)
    R(ax, bx_-0.14, by_+0.25, 0.12, 1.25, '#CCCCCC', ec='#AAAAAA', lw=0.5)  # towel rail
    T(ax, bx_+1.05, by_+0.02, 'Guest Bathroom', 5, '#336699', True)

    # King bed 1.5 × 2.0 against top wall centred
    kbw, kbh = 1.5, 2.0
    kbx = gx + (gw - kbw) / 2
    kby = gy + gh - kbh - 0.1
    R(ax, kbx, kby, kbw, kbh, C['bed'], ec='#4488BB', lw=1.3, z=3)
    R(ax, kbx, kby+kbh-0.22, kbw, 0.22, C['headboard'], ec='#4488BB', lw=0.8, z=4)
    R(ax, kbx+0.1, kby+kbh-0.52, 0.55, 0.26, C['pillow'], ec='#AACCE0', lw=0.5, z=5)
    R(ax, kbx+0.85, kby+kbh-0.52, 0.55, 0.26, C['pillow'], ec='#AACCE0', lw=0.5, z=5)
    T(ax, kbx+kbw/2, kby+0.73, 'King Bed\n1.5m × 2.0m', 5.5, '#1A3A5A')
    R(ax, kbx-0.58, kby+0.65, 0.5, 0.5, C['storage']); T(ax,kbx-0.33,kby+0.9,'Side\nTbl',4.5)
    R(ax, kbx+kbw+0.08, kby+0.65, 0.5, 0.5, C['storage']); T(ax,kbx+kbw+0.33,kby+0.9,'Side\nTbl',4.5)

    # Wardrobe right wall
    R(ax, gx+gw-0.68, gy+0.1, 0.65, 1.9, C['wardrobe'], ec='#AA8844', lw=1)
    T(ax, gx+gw-0.35, gy+1.05, 'W\nR\nB', 5)

    # Armchair + reading lamp
    R(ax, gx+0.6, gy+0.15, 0.75, 0.72, C['sofa'], ec='#668866'); T(ax,gx+0.97,gy+0.51,'Chair',5)
    Circ(ax, gx+1.48, gy+0.42, 0.16, '#EECC44', ec='#CC9922', lw=0.5)

    # Small dresser
    R(ax, gx+1.82, gy+0.12, 0.9, 0.55, C['desk'], ec='#8866AA')
    T(ax, gx+2.27, gy+0.39, 'Dresser', 5, '#553377')

    T(ax, gx+gw/2, gy+2.0, 'GUEST BEDROOM', 8, '#1A3A6A', True)
    T(ax, gx+gw/2, gy+1.6, "5.38m × 3.25m  (17'8\" × 10'8\")", 5.5, '#4466AA')
    darr(ax, gx, gy-0.6, gx+gw, gy-0.6, "5.38m (17'8\")")

    # Staircase
    for i in range(6):
        R(ax, gx+gw+0.15, gy+1.6+i*0.43, 0.85, 0.38, C['stair'], ec='#BBAA77', lw=0.4)
    T(ax, gx+gw+0.57, gy+3.4, 'Stairs\n↑ GF', 4.5, '#888866')

    # RECEPTION / LIVING + HOME OFFICE 7.24 × 4.16
    rx, ry, rw, rh = 6.4, 0.6, 7.24, 4.16
    R(ax, rx, ry, rw, rh, C['floor'], ec=C['wall'], lw=2.5, z=1)
    R(ax, rx-0.06, ry+0.5, 0.06, 1.8, C['window'], ec='#7799CC', lw=0, z=6)
    T(ax, rx-0.55, ry+1.4, '↔ Terrace', 4.5, '#336699', ha='right')

    # LIVING ZONE – L-shaped sofa
    sx_, sy_ = rx+0.28, ry+1.35
    R(ax, sx_, sy_, 3.0, 0.85, C['sofa'], ec='#558855', lw=1.2, z=3)
    R(ax, sx_, sy_+0.85, 0.85, 1.55, C['sofa'], ec='#558855', lw=1.2, z=3)
    T(ax, sx_+1.7, sy_+0.42, 'Corner Sofa  3.0m', 5.5, '#224422')
    T(ax, sx_+0.42, sy_+1.6, 'Sofa', 5, '#224422')

    # Coffee table
    R(ax, sx_+1.0, sy_-1.0, 1.1, 0.6, C['table'], ec='#AA9933', z=3)
    T(ax, sx_+1.55, sy_-0.7, 'Coffee\nTable', 5)

    # Rug
    ax.add_patch(FancyBboxPatch((sx_-0.15,sy_-1.15),3.4,2.85,
                                boxstyle='round,pad=0.15',
                                fc=C['rug'],ec='#B0A090',lw=0.8,alpha=0.3,zorder=2))

    # TV on far wall
    R(ax, rx+0.45, ry+rh-0.65, 2.4, 0.14, C['tv'], ec='#333333', lw=0.5, z=5)
    R(ax, rx+0.45, ry+rh-0.55, 2.4, 0.42, '#AAAAAA', ec='#888888', lw=0.8, z=4)
    T(ax, rx+1.65, ry+rh-0.64, 'TV  65"', 5, 'white')
    R(ax, rx+0.45, ry+rh-1.12, 2.4, 0.42, C['storage'], ec='#AA8844', z=3)
    T(ax, rx+1.65, ry+rh-0.92, 'Media Unit', 5)

    # Side table + floor lamp
    Circ(ax, sx_+3.08, sy_+1.55, 0.2, '#EECC44', ec='#CC9922', lw=0.5)
    T(ax, sx_+3.08, sy_+1.55, '⚡', 5, '#884400')

    # Plants near garden doors
    Circ(ax, rx+0.4, ry+0.38, 0.28, C['plant'], ec='#508050', lw=0.6, z=3)
    T(ax, rx+0.4, ry+0.38, '🌿', 5.5)
    Circ(ax, rx+0.4, ry+2.55, 0.22, C['plant'], ec='#508050', lw=0.5, z=3)

    # HOME OFFICE ZONE – dashed boundary
    ax.add_patch(FancyBboxPatch((rx+rw-2.22,ry+0.28),2.1,3.0,
                                boxstyle='round,pad=0.15',
                                fc='#F0EAFA',ec='#9977CC',lw=1.3,linestyle='--',alpha=0.5,zorder=2))
    T(ax, rx+rw-1.17, ry+rh-0.32, 'HOME OFFICE', 6, '#7755BB', True)

    # Work desk 1.4 × 0.7
    dx_, dy_ = rx+rw-2.0, ry+1.42
    R(ax, dx_, dy_, 1.4, 0.7, C['desk'], ec='#8866AA', lw=1.2, z=3)
    T(ax, dx_+0.7, dy_+0.35, 'Desk  1.4m × 0.7m', 5.5, '#553377')

    # Ergonomic chair
    Circ(ax, dx_+0.7, dy_-0.48, 0.33, C['chair'], ec='#886644', lw=0.8, z=3)
    T(ax, dx_+0.7, dy_-0.48, 'Ergo\nChair', 4.5, '#553322')

    # Monitor hint
    R(ax, dx_+0.48, dy_+0.52, 0.52, 0.06, '#555555', ec='#333333', lw=0.4, z=5)
    T(ax, dx_+0.74, dy_+0.63, '🖥', 5.5)

    # Bookshelf right wall
    R(ax, rx+rw-0.72, ry+0.5, 0.65, 2.2, C['storage'], ec='#AA8844', z=3)
    T(ax, rx+rw-0.39, ry+1.6, 'Book-\nshelf', 5)

    # Filing cabinet
    R(ax, rx+rw-2.0, ry+0.32, 0.7, 0.72, C['storage'], ec='#AA8844', z=3)
    T(ax, rx+rw-1.65, ry+0.68, 'Filing\nCab.', 4.5)

    T(ax, rx+rw/2-0.8, ry+0.38, 'LIVING ROOM', 8, '#1A3A6A', True)
    T(ax, rx+rw/2-0.8, ry+0.04, "7.24m × 4.16m  (23'9\" × 13'8\")", 5.5, '#4466AA')
    darr(ax, rx, ry-0.6, rx+rw, ry-0.6, "7.24m (23'9\")")

    # Utility room
    ux_, uy_ = rx+rw-2.15, ry+rh
    R(ax, ux_, uy_, 2.15, 1.55, C['utility'], ec=C['wall'], lw=1.5, z=2)
    R(ax, ux_+0.15, uy_+0.22, 0.72, 0.65, '#CCCCDD', ec='#888888', lw=0.6, z=3)
    T(ax, ux_+0.51, uy_+0.55, 'W/M', 4.5)
    R(ax, ux_+0.97, uy_+0.22, 0.72, 0.65, '#DDCCCC', ec='#888888', lw=0.6, z=3)
    T(ax, ux_+1.33, uy_+0.55, 'Dryer', 4.5)
    T(ax, ux_+1.08, uy_+1.3, 'Utility Room', 5.5, '#555555')


# ──────────────────────────────────────────────────────────────────────────────
# ASSEMBLE
# ──────────────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(30, 27))
fig.patch.set_facecolor('#F5F4F0')
gs = GridSpec(2, 2, figure=fig, hspace=0.16, wspace=0.08,
              left=0.02, right=0.98, top=0.93, bottom=0.07)

ax1 = fig.add_subplot(gs[0, :])
ax2 = fig.add_subplot(gs[1, 0])
ax3 = fig.add_subplot(gs[1, 1])

draw_first_floor(ax1)
draw_ground_floor(ax2)
draw_lower_ground(ax3)

fig.suptitle('FURNITURE LAYOUT PLAN', fontsize=20, fontweight='bold',
             color='#111133', y=0.97)
fig.text(0.5, 0.944,
         "First Floor: Child's Room  ·  Ground: Master Bedroom + Kitchen/Dining  ·  "
         "Lower Ground: Guest Bedroom + Living Room / Home Office",
         ha='center', fontsize=9, color='#445566', style='italic')

legend_items = [
    mpatches.Patch(fc=C['bed'],     ec='#555', label='Bed / Bedding'),
    mpatches.Patch(fc=C['sofa'],    ec='#555', label='Sofa / Seating'),
    mpatches.Patch(fc=C['table'],   ec='#555', label='Tables / Dining'),
    mpatches.Patch(fc=C['wardrobe'],ec='#555', label='Wardrobe / Storage'),
    mpatches.Patch(fc=C['desk'],    ec='#555', label='Desk / Dressing Table'),
    mpatches.Patch(fc=C['bath'],    ec='#555', label='Bath / Shower'),
    mpatches.Patch(fc=C['bath_rm'], ec='#555', label='Bathroom'),
    mpatches.Patch(fc=C['window'],  ec='#555', label='Window / Door'),
    mpatches.Patch(fc=C['rug'],     ec='#B0A090', label='Area Rug'),
    mpatches.Patch(fc=C['plant'],   ec='#508050', label='Plants'),
]
fig.legend(handles=legend_items, loc='lower center', ncol=5, fontsize=7.5,
           frameon=True, fancybox=True, framealpha=0.92,
           bbox_to_anchor=(0.5, 0.0), title='LEGEND', title_fontsize=9)

out = '/home/user/concerts-announcements/house_layout.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#F5F4F0')
plt.close()
print(f"Saved: {out}")
