"""
ComfyUI Cleaner — Native Windows GUI with Canvas animations.
Pure Python stdlib + tkinter. No extra dependencies.
"""
import os
import sys
import json
import math
import time
import random
import ctypes
import threading
import subprocess
import tkinter as tk
from tkinter import font as tkfont

ROOT = os.path.dirname(os.path.abspath(__file__))


def resource_path(name):
    """Return a bundled resource path for source and PyInstaller builds."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", ROOT)
        candidate = os.path.join(base, name)
        if os.path.exists(candidate):
            return candidate
    candidates = [
        os.path.join(ROOT, name),
        os.path.join(os.path.dirname(ROOT), "assets", name),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]

# ═══════════════════════════════════════════════════
#  Theme
# ═══════════════════════════════════════════════════

BG_DARK   = "#0f0e17"
BG_CARD   = "#1a1930"
BG_CARD2  = "#222140"
ACCENT    = "#7c3aed"
ACCENT2   = "#4f46e5"
CYAN      = "#60a5fa"
GREEN     = "#34d399"
YELLOW    = "#fbbf24"
PINK      = "#f472b6"
WHITE     = "#e2e8f0"
MUTED     = "#64748b"
DIM       = "#334155"
FONT_SANS = ("Microsoft YaHei UI",)
FONT_MONO = ("Cascadia Code", "Consolas", "Courier New")

STATUS_LABELS = [
    ("ComfyUI.exe",       "Electron 主进程"),
    ("winpty-agent.exe",  "node-pty 终端助手"),
    ("nvidia-smi.exe",    "GPU 查询进程"),
    ("扫描残留进程",       "Python / 终端 / uv"),
]
STEP_DETAIL_EXTRA = [
    "Electron 主进程",
    "node-pty 终端助手",
    "GPU 查询进程",
    "Python / 终端 / uv",
]

# ═══════════════════════════════════════════════════
#  Cleanup logic (runs in background thread)
# ═══════════════════════════════════════════════════

def do_taskkill(exe_name):
    code = subprocess.call(
        ['taskkill', '/F', '/IM', exe_name],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return code == 0

def do_wmi_scan():
    ps_code = r'''
$all=@{}; Get-Process|ForEach-Object{$all[$_.Id]=$true};
$found=0; $details=@();
$procs=Get-WmiObject Win32_Process|Where-Object{
    ($_.Name -eq 'python.exe' -and $_.CommandLine -and $_.CommandLine -like '*comfyui*') -or
    ($_.Name -eq 'OpenConsole.exe' -and -not $all[$_.ParentProcessId]) -or
    ($_.Name -eq 'uv.exe' -and $_.ExecutablePath -like '*comfyui*')
};
foreach($p in $procs){
    $found++;
    $label=if($p.Name -eq 'python.exe'){'Python'}elseif($p.Name -eq 'OpenConsole.exe'){ur'终端'}else{'uv'};
    $details += "$label PID:$($p.ProcessId)";
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
};
$result = @{found=$found; details=$details} | ConvertTo-Json -Compress;
Write-Output $result
'''
    try:
        proc = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_code],
            capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        data = json.loads(proc.stdout.strip())
        return data['found'], data.get('details', [])
    except Exception:
        return 0, []

CLEANUP_STEPS = [
    lambda: ('ComfyUI.exe', do_taskkill('ComfyUI.exe')),
    lambda: ('winpty-agent.exe', do_taskkill('winpty-agent.exe')),
    lambda: ('nvidia-smi.exe', do_taskkill('nvidia-smi.exe')),
    lambda: ('扫描残留进程', do_wmi_scan()),
]

# ═══════════════════════════════════════════════════
#  Animation utilities
# ═══════════════════════════════════════════════════

def lerp(a, b, t):
    return a + (b - a) * t

def ease_out(t):
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    return 0.5 - math.cos(math.pi * t) / 2

# ═══════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════

class CleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ComfyUI 一键清理")
        self.root.geometry("420x580")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        # Set window + taskbar icon
        ico_path = resource_path('comfyui-cleaner.ico')
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        # State
        self.running = False
        self.step_objs = []
        self.step_results = [None, None, None, None]
        self.confetti_items = []
        self.anim_jobs = []
        self._spinner_frame = 0
        self._spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

        # Build UI
        self._build_ui()

    # ── UI Construction ──

    def _build_ui(self):
        # Main canvas for drawing
        self.canvas = tk.Canvas(
            self.root, bg=BG_DARK, highlightthickness=0,
            width=420, height=580
        )
        self.canvas.pack(fill="both", expand=True)

        # ── Background gradient ──
        self._draw_bg_gradient()

        # ── Ambient particles ──
        self._create_particles()

        # ── Header ──
        self._draw_header()

        # ── Step cards ──
        self._draw_step_cards()

        # ── Action button ──
        self._draw_button()

        # ── Footer ──
        self._draw_footer()

        # Confetti drawn directly on main canvas

    def _draw_bg_gradient(self):
        """Dark gradient background."""
        w, h = 420, 580
        for y in range(h):
            t = y / h
            r = int(15 + t * 5)
            g = int(14 + t * 5)
            b = int(23 + t * 10)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, y, w, y, fill=color, width=1)

    def _create_particles(self):
        """Small floating ambient dots."""
        self.particles = []
        for _ in range(25):
            x = random.randint(0, 420)
            y = random.randint(0, 580)
            r = random.randint(1, 3)
            color = random.choice([ACCENT, CYAN, GREEN, PINK, YELLOW])
            dot = self.canvas.create_oval(
                x-r, y-r, x+r, y+r,
                fill=color, outline="", stipple="gray25"
            )
            speed = random.uniform(0.3, 1.2)
            dx = random.uniform(-0.5, 0.5)
            self.particles.append((dot, y, speed, dx))
        self._animate_particles()

    def _animate_particles(self):
        for i, (dot, y0, speed, dx) in enumerate(self.particles):
            y = y0 - speed
            if y < -10:
                y = 590
            self.particles[i] = (dot, y, speed, dx)
            self.canvas.coords(dot, 200 + dx * 200 - 2, y - 2, 200 + dx * 200 + 2, y + 2)
        self.anim_jobs.append(self.root.after(40, self._animate_particles))

    def _draw_header(self):
        """Title + broom emoji."""
        # Broom label
        self.broom_label = tk.Label(
            self.root, text="🧹", font=(FONT_SANS[0], 40),
            fg=WHITE, bg=BG_DARK
        )
        self.broom_win = self.canvas.create_window(210, 50, window=self.broom_label)

        # Title
        self.title_label = tk.Label(
            self.root, text="ComfyUI 一键清理",
            font=(FONT_SANS[0], 20, "bold"),
            fg=WHITE, bg=BG_DARK
        )
        self.canvas.create_window(210, 105, window=self.title_label)

        # Subtitle
        self.sub_label = tk.Label(
            self.root, text="GPU 显存清理工具",
            font=(FONT_SANS[0], 10),
            fg=MUTED, bg=BG_DARK
        )
        self.canvas.create_window(210, 130, window=self.sub_label)

        # Separator line
        self.canvas.create_line(
            60, 155, 360, 155,
            fill=DIM, width=1
        )

        # Start broom bounce animation
        self._broom_bounce()

    def _broom_bounce(self):
        if not hasattr(self, '_bounce_frame'):
            self._bounce_frame = 0
        t = self._bounce_frame * 0.08
        offset = abs(math.sin(t)) * 10
        self.canvas.coords(self.broom_win, 210, 50 + int(offset))
        self._bounce_frame += 1
        self.anim_jobs.append(self.root.after(30, self._broom_bounce))

    def _draw_step_cards(self):
        """4 step cards with icon, name, detail, status."""
        self.step_frames = []
        self.step_icons = []
        self.step_names = []
        self.step_details = []
        self.step_status_labels = []

        colors = [ACCENT, ACCENT2, CYAN, GREEN]
        for i, ((name, detail), color) in enumerate(zip(STATUS_LABELS, colors)):
            y_base = 180 + i * 68
            # Card background (rounded rect via overlapping shapes)
            card = self.canvas.create_rectangle(
                25, y_base, 395, y_base + 56,
                fill=BG_CARD, outline=DIM, width=1
            )
            self.step_frames.append(card)

            # Left accent bar
            bar = self.canvas.create_rectangle(
                25, y_base, 29, y_base + 56,
                fill=color, outline=""
            )

            # Number circle
            cx, cy = 58, y_base + 28
            circle = self.canvas.create_oval(
                cx-16, cy-16, cx+16, cy+16,
                fill=BG_CARD2, outline=color, width=2
            )
            num_text = self.canvas.create_text(
                cx, cy, text=str(i+1),
                fill=color, font=(FONT_SANS[0], 13, "bold")
            )
            self.step_icons.append((circle, num_text, color, cx, cy))

            # Name
            name_text = self.canvas.create_text(
                88, y_base + 14, text=name,
                fill=WHITE, font=(FONT_SANS[0], 12, "bold"),
                anchor="w"
            )
            self.step_names.append(name_text)

            # Detail
            detail_text = self.canvas.create_text(
                88, y_base + 36, text=detail,
                fill=MUTED, font=(FONT_SANS[0], 9),
                anchor="w"
            )
            self.step_details.append(detail_text)

            # Status
            status_text = self.canvas.create_text(
                380, y_base + 28, text="",
                fill=MUTED, font=(FONT_SANS[0], 9),
                anchor="e"
            )
            self.step_status_labels.append(status_text)

    def _draw_button(self):
        """Action button with gradient background."""
        self.btn_rects = []
        w, h = 370, 44
        x, y = 25, 468

        # Gradient rectangles (vertical strips)
        strips = 20
        for i in range(strips):
            t = i / strips
            r = int(124 + t * 20)  # 124 -> 144
            g = int(58 + t * (-20))  # 58 -> 38
            b = int(237 + t * (-20))  # 237 -> 217
            color = f'#{r:02x}{g:02x}{b:02x}'
            sx = x + i * w / strips
            ex = x + (i + 1) * w / strips + 1
            rect = self.canvas.create_rectangle(
                sx, y, ex, y + h,
                fill=color, outline=""
            )
            self.btn_rects.append(rect)

        # Button border
        self.btn_border = self.canvas.create_rectangle(
            x, y, x + w, y + h,
            fill="", outline=ACCENT, width=1
        )

        # Button text
        self.btn_text = self.canvas.create_text(
            x + w/2, y + h/2,
            text="✨  开始清理",
            fill=WHITE, font=(FONT_SANS[0], 14, "bold")
        )

        # Click binding
        self.canvas.tag_bind(self.btn_text, "<Button-1>", lambda e: self.start_cleanup())
        for rect in self.btn_rects:
            self.canvas.tag_bind(rect, "<Button-1>", lambda e: self.start_cleanup())
        self.canvas.tag_bind(self.btn_border, "<Button-1>", lambda e: self.start_cleanup())

    def _draw_footer(self):
        self.canvas.create_text(
            210, 550,
            text="Powered by PUIKIN",
            fill=DIM, font=(FONT_SANS[0], 8)
        )

    # ── Step card animation ──

    def _animate_in(self):
        """Simple fade-in for cards (staggered)."""
        for i in range(4):
            delay = 300 + i * 100
            self.root.after(delay, self._light_up_card, i)

    def _light_up_card(self, idx):
        """Highlight a card briefly to draw attention."""
        circle, num, color, cx, cy = self.step_icons[idx]
        original_fill = BG_CARD2
        self.canvas.itemconfig(circle, fill=color)
        self.root.after(150, lambda: self.canvas.itemconfig(self.step_icons[idx][0], fill=original_fill))

    # ── Cleanup flow ──

    def start_cleanup(self):
        if self.running:
            return
        self.running = True

        # Reset all states
        for i in range(4):
            self.step_results[i] = None
            circle, num, color, cx, cy = self.step_icons[i]
            self.canvas.itemconfig(num, text=str(i+1))
            self.canvas.itemconfig(circle, outline=color, fill=BG_CARD2)
            if self.step_details[i]:
                self.canvas.itemconfig(self.step_details[i], text=STEP_DETAIL_EXTRA[i])
            if self.step_status_labels[i]:
                self.canvas.itemconfig(self.step_status_labels[i], text="")

        # Update button
        self.canvas.itemconfig(self.btn_text, text="清理中...", fill=MUTED)

        # Launch in background thread
        threading.Thread(target=self._run_cleanup, daemon=True).start()

        # Start animation polling
        self._poll_results()

    def _run_cleanup(self):
        """Execute all 4 steps in sequence."""
        for i, fn in enumerate(CLEANUP_STEPS):
            name, result = fn()
            if isinstance(result, bool):
                self.step_results[i] = {'name': name, 'killed': result}
            else:
                count, details = result
                self.step_results[i] = {
                    'name': name, 'killed': count > 0,
                    'count': count, 'details': details
                }
            time.sleep(0.15)  # small delay for visual rhythm

    def _poll_results(self):
        """Check step results and update UI with animated spinners."""
        # Advance spinner frame
        self._spinner_frame += 1
        spin_char = self._spinner_chars[self._spinner_frame % len(self._spinner_chars)]

        all_done = True
        for i in range(4):
            if self.step_results[i] is None:
                all_done = False
                self._update_step_running(i, spin_char)
            elif not hasattr(self, f'_step_{i}_done'):
                setattr(self, f'_step_{i}_done', True)
                self._update_step_done(i)

        if all_done:
            self._on_all_done()
        else:
            self.anim_jobs.append(self.root.after(80, self._poll_results))

    def _update_step_running(self, idx, spin_char="⏳"):
        """Show spinner on a running step."""
        circle, num, color, cx, cy = self.step_icons[idx]
        self.canvas.itemconfig(circle, fill=ACCENT2)
        self.canvas.itemconfig(num, text=spin_char, fill=CYAN, font=(FONT_SANS[0], 16))
        if self.step_status_labels[idx]:
            self.canvas.itemconfig(self.step_status_labels[idx], text="进行中...", fill=CYAN)

    def _update_step_done(self, idx):
        """Show result on completed step."""
        result = self.step_results[idx]
        if result is None:
            return

        circle, num, color, cx, cy = self.step_icons[idx]
        killed = result['killed']

        if killed:
            self.canvas.itemconfig(circle, fill="#064e3b")
            self.canvas.itemconfig(num, text="✓", fill=GREEN, font=(FONT_SANS[0], 16, "bold"))
            status = "已终止"
            status_color = GREEN
            count = result.get('count', 1)
            detail_text = f"已终止 {count} 个进程" if count > 1 else "已终止"
            if 'details' in result and result['details']:
                ds = result['details']
                detail_text = ", ".join(ds[:2]) + (" ..." if len(ds) > 2 else "")
        else:
            self.canvas.itemconfig(circle, fill=BG_CARD2)
            self.canvas.itemconfig(num, text="—", fill=YELLOW, font=(FONT_SANS[0], 14))
            status = "未发现"
            status_color = YELLOW
            detail_text = "未发现"

        if self.step_status_labels[idx]:
            self.canvas.itemconfig(self.step_status_labels[idx], text=status, fill=status_color)
        if self.step_details[idx]:
            self.canvas.itemconfig(self.step_details[idx], text=detail_text)

    def _on_all_done(self):
        """All steps complete."""
        self.running = False
        self.canvas.itemconfig(self.btn_text, text="✨  再次清理", fill=WHITE)

        # Celebration
        self._celebration_text()
        self._launch_confetti()

        # Reset after delay
        self.anim_jobs.append(self.root.after(3000, self._reset_ui))

    def _reset_ui(self):
        """Reset all cards to initial state."""
        for i in range(4):
            self.step_results[i] = None
            setattr(self, f'_step_{i}_done', False)
            circle, num, color, cx, cy = self.step_icons[i]
            self.canvas.itemconfig(circle, outline=color, fill=BG_CARD2)
            self.canvas.itemconfig(num, text=str(i+1), fill=color, font=(FONT_SANS[0], 13, "bold"))
            if self.step_details[i]:
                self.canvas.itemconfig(self.step_details[i], text=STEP_DETAIL_EXTRA[i])
            if self.step_status_labels[i]:
                self.canvas.itemconfig(self.step_status_labels[i], text="")
        # Clear confetti
        self.canvas.delete("confetti")
        self.confetti_items.clear()
        # Clear celebration text
        self.canvas.delete("celebration_text")
        self.canvas.itemconfig(self.btn_text, text="✨  开始清理", fill=WHITE)

    # ── Celebration effects ──

    def _celebration_text(self):
        """Show celebration text with pop animation."""
        self.canvas.delete("celebration_text")
        text = self.canvas.create_text(
            210, 540, text="🎉  清理完成！",
            fill=GREEN, font=(FONT_SANS[0], 12, "bold"),
            tags="celebration_text"
        )
        # Pop animation
        def pop(step=0):
            if step > 10: return
            s = 1 + math.sin(step * 0.6) * 0.3 * (1 - step/10)
            self.canvas.itemconfig(text, font=(FONT_SANS[0], int(12 * s), "bold"))
            self.root.after(50, pop, step + 1)
        pop()

    def _launch_confetti(self):
        """Canvas-based confetti burst."""
        colors = [ACCENT, CYAN, GREEN, YELLOW, PINK, ACCENT2, "#fb923c", "#e879f9"]
        cx, cy = 210, 300

        for _ in range(60):
            x = cx + random.randint(-80, 80)
            y = cy + random.randint(-30, 30)
            size = random.randint(3, 8)
            is_rect = random.random() > 0.5

            if is_rect:
                item = self.canvas.create_rectangle(
                    x, y, x + size, y + size * 0.6,
                    fill=random.choice(colors), outline="",
                    tags="confetti"
                )
            else:
                item = self.canvas.create_oval(
                    x - size//2, y - size//2, x + size//2, y + size//2,
                    fill=random.choice(colors), outline="",
                    tags="confetti"
                )

            vx = random.uniform(-4, 4)
            vy = random.uniform(-6, -1)
            gravity = random.uniform(0.15, 0.35)

            self.confetti_items.append({
                'id': item, 'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'gravity': gravity, 'life': 80 + random.randint(0, 40),
            })

        self._animate_confetti()

    def _animate_confetti(self):
        """Animate confetti particles."""
        alive = False
        for p in self.confetti_items:
            if p['life'] <= 0:
                continue
            alive = True
            p['life'] -= 1
            p['vy'] += p['gravity']
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vx'] *= 0.995

            dx = int(p['vx'])
            dy = int(p['vy'])
            self.canvas.move(p['id'], dx, dy)

            if p['life'] < 15:
                self.canvas.itemconfig(p['id'], fill=BG_DARK)

        if alive:
            self.anim_jobs.append(self.root.after(16, self._animate_confetti))
        else:
            self.canvas.delete("confetti")
            self.confetti_items.clear()


# ═══════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════

def main():
    # Give the window its own identity so the taskbar shows our icon, not Python's
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('PUIKIN.ComfyUI.Cleaner')
    except Exception:
        pass

    root = tk.Tk()
    app = CleanerApp(root)
    # Animate cards on startup
    app.root.after(200, app._animate_in)
    root.mainloop()


if __name__ == '__main__':
    main()
