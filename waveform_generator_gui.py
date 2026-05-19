#!/usr/bin/env python3
"""
Arbitrary Waveform Generator 鈥?Real Signal Generator Front Panel
Screen (left) + Physical Keypad/Buttons (right).
Matches reference image colors exactly.
"""

import sys, os, numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QDoubleSpinBox,
    QGroupBox, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal, QLineF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPainterPath, QMouseEvent, QPaintEvent, QPolygonF
)

# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# EXACT COLORS from reference image analysis
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?BEZEL       = QColor(0,   0,   0)     # #000000 pure black bezel
SCR_BG      = QColor(3,   9,   13)    # #03090d screen background (very dark blue-black)
GRID        = QColor(192, 195, 194)   # #c0c3c2 main grid lines
GRID_SUB    = QColor(59,  67,  71)    # #3b4347 sub-grid lines
AXIS_C      = QColor(100, 105, 108)   # dashed center axis (between grid & sub-grid)
WAVE_CYAN   = QColor(2,   160, 232)   # #02a0e8 waveform trace
YELLOW_CH1  = QColor(240, 236, 54)    # #f0ec36 yellow channel marker
TEXT_WHITE  = QColor(219, 220, 219)   # #dbdcdb bright text
TEXT_DIM    = QColor(140, 143, 140)   # dim secondary text
TEXT_BLUE   = QColor(0,   190, 250)   # highlighted parameter value
L_PANEL     = QColor(136, 141, 145)   # #888d91 left softkey panel
R_PANEL     = QColor(123, 128, 125)   # #7b807d right softkey panel
PANEL_BG    = QColor(20,  22,  20)    # button panel background
BTN_FACE    = QColor(55,  58,  55)    # button face
BTN_HOVER   = QColor(72,  75,  72)    # button hover
BTN_ACTIVE  = QColor(0,   130, 210)   # active/selected button
BTN_OUTPUT  = QColor(30,  140, 30)    # output ON button
BORDER      = QColor(50,  53,  50)    # subtle borders


class ScreenWidget(QWidget):
    """Left: the display screen 鈥?matching reference image."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 500)
        self.waveforms: list[dict] = []
        self.show_grid = True
        self.freq_s = "1.000 000 kHz"
        self.amp_s = "1.000 Vpp"
        self.offset_s = "0.000 Vdc"
        self.phase_s = "0.0掳"
        self.active_ch = "CH1"
        self.ch1_on = True
        self.ch2_on = False
        self.edit_param: str | None = None  # 'freq','amp','offset','phase'
        self.edit_buf = ""

    def set_wf(self, wfs): self.waveforms = wfs; self.update()
    def set_ro(self, f, a, o, p="0.0掳"): self.freq_s=f; self.amp_s=a; self.offset_s=o; self.phase_s=p; self.update()

    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # Bezel (pure black)
        p.fillRect(0, 0, W, H, BEZEL)

        # Screen area inset
        mx, my = 15, 40
        mw, mh = W - 30, H - 60

        # Screen background
        p.fillRect(mx, my, mw, mh, SCR_BG)

        # Screen border
        p.setPen(QPen(QColor(151,154,154), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(mx, my, mw, mh)

        # Top brand line
        p.fillRect(mx, my, mw, 2, QColor(2, 160, 232))
        p.setPen(TEXT_WHITE)
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(mx + 10, my + 14, "AWG-2202  Arbitrary Waveform Generator")

        # 鈹€鈹€ Grid + Waveform (takes most of the screen) 鈹€鈹€
        gx = mx + 12
        gy = my + 22
        gw = int(mw * 0.60) - 16
        gh = int(mh * 0.80)

        if self.show_grid: self._grid(p, gx, gy, gw, gh)

        p.setClipRect(gx, gy, gw, gh)
        for idx, wf in enumerate(self.waveforms):
            if wf.get("visible", True):
                self._wave(p, gx, gy, gw, gh, wf, idx)
        p.setClipping(False)

        p.setPen(QPen(GRID, 1.5)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(gx, gy, gw, gh)

        # Small channel arrows (subtle)
        if self.ch1_on:
            ay = gy + 12
            p.setPen(QPen(YELLOW_CH1, 1.5)); p.setBrush(YELLOW_CH1)
            p.drawPolygon(QPolygonF([QPointF(gx-5,ay), QPointF(gx,ay-3), QPointF(gx,ay+3)]))
            p.setFont(QFont("Segoe UI", 6, QFont.Weight.Bold)); p.setPen(YELLOW_CH1)
            p.drawText(gx-42, ay+3, "CH1")
        if self.ch2_on:
            ay = gy + 28
            p.setPen(QPen(WAVE_CYAN, 1.5)); p.setBrush(WAVE_CYAN)
            p.drawPolygon(QPolygonF([QPointF(gx-5,ay), QPointF(gx,ay-3), QPointF(gx,ay+3)]))
            p.setFont(QFont("Segoe UI", 6, QFont.Weight.Bold)); p.setPen(WAVE_CYAN)
            p.drawText(gx-42, ay+3, "CH2")

        # 鈹€鈹€ Parameter readouts (right side of screen) 鈹€鈹€
        rx = gx + gw + 14
        ry = gy
        spacing = (gh - 10) // 4  # spread 4 params evenly across grid height

        def draw_param(label, value, y, editing, buf, pname):
            p.setPen(TEXT_DIM)
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(rx, y, label)
            p.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            if editing:
                display = buf if buf else "_"
                p.fillRect(rx, y+5, 145, 24, QColor(25,30,35))
                p.setPen(QColor(180,200,220))
                p.drawText(rx+4, y+23, display)
                p.setPen(QColor(100,140,160))
                p.setFont(QFont("Segoe UI", 7))
                p.drawText(rx, y-2, f"Editing {pname.upper()}...")
            else:
                p.setPen(TEXT_BLUE if label == "Frequency" else TEXT_WHITE)
                p.drawText(rx, y+23, value)

        draw_param("Frequency", self.freq_s, ry, self.edit_param=='freq', self.edit_buf, "freq")
        draw_param("Amplitude", self.amp_s, ry+spacing, self.edit_param=='amp', self.edit_buf, "amp")
        draw_param("Offset", self.offset_s, ry+spacing*2, self.edit_param=='offset', self.edit_buf, "offset")
        draw_param("Phase", self.phase_s, ry+spacing*3, self.edit_param=='phase', self.edit_buf, "phase")

        # Channel indicator bottom-right
        p.setPen(TEXT_DIM); p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.drawText(rx, gy+gh-4, f"Active: {self.active_ch}")

    def _grid(self, p, px, py, pw, ph):
        dx, dy = pw/10, ph/8
        p.setPen(QPen(GRID_SUB, 0.6, Qt.PenStyle.SolidLine))
        for i in range(51): p.drawLine(QLineF(px+i*dx/5, py, px+i*dx/5, py+ph))
        for i in range(41): p.drawLine(QLineF(px, py+i*dy/5, px+pw, py+i*dy/5))
        p.setPen(QPen(GRID, 1, Qt.PenStyle.SolidLine))
        for i in range(11): p.drawLine(QLineF(px+i*dx, py, px+i*dx, py+ph))
        for i in range(9): p.drawLine(QLineF(px, py+i*dy, px+pw, py+i*dy))
        p.setPen(QPen(AXIS_C, 0.8, Qt.PenStyle.DashLine))
        p.drawLine(QLineF(px+pw/2, py, px+pw/2, py+ph))
        p.drawLine(QLineF(px, py+ph/2, px+pw, py+ph/2))

    def _wave(self, p, px, py, pw, ph, wf, idx):
        d = wf.get("data", np.array([]))
        if len(d) < 2: return
        vs = wf.get("v_scale", 1.0); vo = wf.get("v_offset", 0.0)
        p.setPen(QPen(wf.get("color", WAVE_CYAN), wf.get("line_width", 1.5)))
        mid = py + ph/2
        sy = (ph*0.85/2)/vs if vs else 1
        sx = pw/(len(d)-1) if len(d) > 1 else 1
        path = QPainterPath()
        path.moveTo(px, max(py, min(py+ph, mid-(d[0]+vo)*sy)))
        for i in range(1, len(d)):
            path.lineTo(px+i*sx, max(py, min(py+ph, mid-(d[i]+vo)*sy)))
        p.drawPath(path)
        if wf.get("label"):
            p.setFont(QFont("Segoe UI", 7)); p.setPen(wf.get("color", WAVE_CYAN))
            p.drawText(int(px+4), int(py+13*(idx+1)), wf["label"])

    def mousePressEvent(self, e: QMouseEvent):
        """Detect click on parameter readouts."""
        W, H = self.width(), self.height()
        mx, my = 15, 40
        mh = H - 60
        gw = int((W-30)*0.60)-16
        gh = int(mh * 0.80)
        spacing = (gh - 10) // 4
        rx = mx+gw+26
        ry = my+22
        x, y = e.pos().x(), e.pos().y()
        if rx <= x <= rx+155:
            if ry <= y <= ry+spacing: self.edit_param = 'freq'
            elif ry+spacing <= y <= ry+spacing*2: self.edit_param = 'amp'
            elif ry+spacing*2 <= y <= ry+spacing*3: self.edit_param = 'offset'
            elif ry+spacing*3 <= y <= ry+spacing*4: self.edit_param = 'phase'
            else: return
            self.edit_buf = ""
            self.update()


class DrawDialog(QWidget):
    """Hand-draw arbitrary waveform dialog."""
    done = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hand-Draw Waveform")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(620, 370)
        self.setStyleSheet(f"background:#03090d;")
        self.pts: list[QPointF] = []
        self.drawing = False

    def paintEvent(self, e):
        p = QPainter(self); p.fillRect(self.rect(), QColor(3,9,13))
        W, H = self.width(), self.height()
        L, R, T, B = 50, 20, 20, 35  # margins (left, right, top, bottom)
        pw, ph = W-L-R, H-T-B
        gx, gy = L, T

        # Grid lines with 10脳8 divisions
        dx, dy = pw/10, ph/8
        p.setPen(QPen(QColor(38,43,47), 0.8))
        for i in range(51): x = gx+i*dx/5; p.drawLine(QLineF(x, gy, x, gy+ph))
        for i in range(41): y = gy+i*dy/5; p.drawLine(QLineF(gx, y, gx+pw, y))
        p.setPen(QPen(QColor(59,67,71), 1))
        for i in range(11): x = gx+i*dx; p.drawLine(QLineF(x, gy, x, gy+ph))
        for i in range(9): y = gy+i*dy; p.drawLine(QLineF(gx, y, gx+pw, y))
        p.setPen(QPen(QColor(90,95,98), 1, Qt.PenStyle.DashLine))
        p.drawLine(QLineF(gx+pw/2, gy, gx+pw/2, gy+ph))
        p.drawLine(QLineF(gx, gy+ph/2, gx+pw, gy+ph/2))
        p.setPen(QPen(QColor(192,195,194), 2)); p.drawRect(gx, gy, pw, ph)

        # 鈹€鈹€ Axis labels 鈹€鈹€
        p.setFont(QFont("Segoe UI", 8)); p.setPen(QColor(140,143,140))
        # X-axis: time labels
        for i in range(11):
            x = gx+i*dx
            label = f"{i-5:.0f}ms"
            tw = QFontMetrics(p.font()).horizontalAdvance(label)
            p.drawText(int(x-tw/2), gy+ph+16, label)
        # X-axis unit
        p.setFont(QFont("Segoe UI", 7)); p.setPen(QColor(100,105,108))
        p.drawText(int(gx+pw/2-10), gy+ph+28, "Time (ms)")

        # Y-axis: voltage labels
        p.setFont(QFont("Segoe UI", 8))
        for i in range(9):
            y = gy+i*dy
            label = f"{(4-i)*0.25:.2f}V"
            tw = QFontMetrics(p.font()).horizontalAdvance(label)
            p.drawText(int(gx-tw-6), int(y+4), label)
        # Y-axis unit
        p.setFont(QFont("Segoe UI", 7)); p.setPen(QColor(100,105,108))
        p.save(); p.translate(12, int(gy+ph/2+20)); p.rotate(-90)
        p.drawText(0, 0, "Amplitude (V)"); p.restore()

        # Draw user's waveform
        if len(self.pts) > 1:
            p.setPen(QPen(QColor(2,160,232), 3))
            pp = QPainterPath()
            pp.moveTo(self.pts[0].x(), self.pts[0].y())
            for pt in self.pts[1:]: pp.lineTo(pt.x(), pt.y())
            p.drawPath(pp)

        # Help text
        p.setPen(QColor(140,143,140)); p.setFont(QFont("Segoe UI", 10))
        p.drawText(12, H-10, "Hold mouse to draw | C: clear | Enter: confirm | Esc: cancel")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.pts = [QPointF(e.pos())]
            self.update()
    def mouseMoveEvent(self, e):
        if self.drawing:
            self.pts.append(QPointF(e.pos()))
            if len(self.pts) % 3 == 0: self.update()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.drawing = False; self.update()
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_C: self.pts = []; self.update()
        elif e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter): self._fin()
        elif e.key() == Qt.Key.Key_Escape: self.close()
    def _fin(self):
        if len(self.pts) < 2: return
        W, H = self.width(), self.height(); m = 30; pw, ph = W-2*m, H-2*m
        xs = np.array([p.x() for p in self.pts]); ys = np.array([p.y() for p in self.pts])
        xn = (xs-m)/pw; yn = 1.0-(ys-m)/ph; yn = (yn-0.5)*2
        xt = np.linspace(xn.min(), xn.max(), 1000)
        self.done.emit(np.interp(xt, xn, yn))
        self.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AWG-2202 Arbitrary Waveform Generator")
        self.setMinimumSize(1060, 720)
        self.resize(1080, 740)

        # Channel state
        self.ch = {
            1: {"type":"Sine","freq":1.0,"amp":1.0,"offset":0.0,"duty":0.5,"phase":0.0,"on":True,"cached":None},
            2: {"type":"Sine","freq":1.0,"amp":1.0,"offset":0.0,"duty":0.5,"phase":0.0,"on":False,"cached":None},
        }
        self.active_ch = 1
        self.rate, self.N, self.running = 100_000, 1000, True
        self.mod_params: dict = {}
        self.mod_on = self.sweep_on = False
        self.sw_start, self.sw_stop, self.sw_time = 0.1, 10.0, 1.0
        self.wf_data: list[dict] = []
        self._wf_btns: dict[str, QPushButton] = {}
        self._last_wf: QPushButton | None = None

        self._setup(); self._style()
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick); self._timer.start(50)
        self._upd_sk(); self._tick()

    # 鈹€鈹€ Build UI 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    def _setup(self):
        c = QWidget(); self.setCentralWidget(c)
        root = QHBoxLayout(c); root.setContentsMargins(4,4,4,4); root.setSpacing(0)

        # ===== LEFT: Screen =====
        screen_box = QWidget()
        screen_box.setMinimumWidth(520)
        sv = QVBoxLayout(screen_box); sv.setContentsMargins(0,0,0,0)
        self.scr = ScreenWidget()
        sv.addWidget(self.scr)

        # Status bar under screen
        st = QWidget(); st.setFixedHeight(22)
        st.setStyleSheet(f"background:#000; border-top:1px solid #1a1a1a;")
        sl = QHBoxLayout(st); sl.setContentsMargins(8,0,8,0)
        self.st_l = QLabel("CH1: Sine 1.000kHz 1.000Vpp")
        self.st_l.setStyleSheet(f"color:#8c8f8c; font-size:8px;")
        sl.addWidget(self.st_l); sl.addStretch()
        self.st_r = QLabel("100kSa/s | 1k pts")
        self.st_r.setStyleSheet(f"color:#8c8f8c; font-size:8px;")
        sl.addWidget(self.st_r)
        sv.addWidget(st)

        root.addWidget(screen_box, stretch=5)

        # Vertical separator
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setFixedWidth(2)
        sep.setStyleSheet("background:#222;"); root.addWidget(sep)

        # ===== RIGHT: Button Panel =====
        rp = QWidget(); rp.setFixedWidth(340)
        rp.setStyleSheet(f"background:#101210;")
        rl = QVBoxLayout(rp); rl.setContentsMargins(6,4,6,6); rl.setSpacing(3)
        rl.addWidget(self._wf_section())
        rl.addWidget(self._mode_section())
        rl.addWidget(self._kp_section())
        rl.addWidget(self._unit_knob_section())
        rl.addWidget(self._ch_section())
        rl.addStretch()
        root.addWidget(rp)

    def _wf_section(self):
        g = QGroupBox("Waveform"); g.setStyleSheet(self._gs(QColor(2,160,232)))
        gl = QGridLayout(g); gl.setSpacing(3); gl.setContentsMargins(5,10,5,4)
        for t, l, r, c in [("Sine","Sine",0,0),("Square","Sq",0,1),("Ramp","Ramp",0,2),
                            ("Pulse","Puls",1,0),("Noise","Noise",1,1),("Arb","Arb",1,2)]:
            b = QPushButton(l); b.setCheckable(True); b.setMinimumHeight(26)
            b.clicked.connect(lambda _, x=t: self._wf(x))
            self._wf_btns[t] = b; gl.addWidget(b, r, c)
        self._wf_btns["Sine"].setChecked(True); self._last_wf = self._wf_btns["Sine"]
        return g

    def _mode_section(self):
        g = QGroupBox("Mode"); g.setStyleSheet(self._gs(TEXT_WHITE))
        gl = QGridLayout(g); gl.setSpacing(3); gl.setContentsMargins(5,10,5,4)
        self.mod_btn = QPushButton("Mod"); self.mod_btn.setCheckable(True); self.mod_btn.setMinimumHeight(24)
        self.mod_btn.clicked.connect(self._mod)
        self.swp_btn = QPushButton("Sweep"); self.swp_btn.setCheckable(True); self.swp_btn.setMinimumHeight(24)
        self.swp_btn.clicked.connect(self._swp)
        self.bst_btn = QPushButton("Burst"); self.bst_btn.setCheckable(True); self.bst_btn.setMinimumHeight(24)
        gl.addWidget(self.mod_btn,0,0); gl.addWidget(self.swp_btn,0,1); gl.addWidget(self.bst_btn,0,2)
        return g

    def _kp_section(self):
        g = QGroupBox("Numeric Keypad"); g.setStyleSheet(self._gs(TEXT_WHITE))
        gl = QGridLayout(g); gl.setSpacing(3); gl.setContentsMargins(5,10,5,4)
        for t, r, c in [('7',0,0),('8',0,1),('9',0,2),('4',1,0),('5',1,1),('6',1,2),
                         ('1',2,0),('2',2,1),('3',2,2),('0',3,0),('.',3,1),('卤',3,2)]:
            b = QPushButton(t); b.setMinimumHeight(30)
            b.setStyleSheet(f"font-size:15px; font-weight:bold;")
            b.clicked.connect(lambda _, x=t: self._kp(x))
            gl.addWidget(b, r, c)
        db = QPushButton("DEL"); db.setMinimumHeight(30)
        db.clicked.connect(lambda: self._kp('del'))
        gl.addWidget(db, 3, 3)
        ob = QPushButton("OK"); ob.setMinimumHeight(96)  # spans ~3 rows
        ob.setStyleSheet(f"font-size:13px; font-weight:bold; background:#1a551a; color:white;")
        ob.clicked.connect(lambda: self._kp('ok'))
        gl.addWidget(ob, 0, 3, 3, 1)
        return g

    def _unit_knob_section(self):
        """Combined Units + Knob section."""
        g = QGroupBox("Units & Knob"); g.setStyleSheet(self._gs(TEXT_WHITE))
        gl = QGridLayout(g); gl.setSpacing(3); gl.setContentsMargins(5,10,5,4)

        # Unit buttons (left side)
        for t, r, c in [("kHz",0,0),("MHz",0,1),("Hz",0,2),("Vpp",1,0),("Vrms",1,1),("dBm",1,2)]:
            b = QPushButton(t); b.setMinimumHeight(24)
            b.clicked.connect(lambda _, x=t: self._unit(x))
            gl.addWidget(b, r, c)

        # Knob / arrow cluster (right side)
        arr_w = QWidget()
        arr_l = QGridLayout(arr_w); arr_l.setSpacing(1); arr_l.setContentsMargins(0,0,0,0)
        for t, r, c in [("鈫?,0,1),("鈫?,1,0),("鈼?,1,1),("鈫?,1,2),("鈫?,2,1)]:
            b = QPushButton(t); b.setFixedSize(32,22); b.setStyleSheet("font-size:11px;")
            if t == '鈫?: b.clicked.connect(lambda: self._nudge(10))
            elif t == '鈫?: b.clicked.connect(lambda: self._nudge(-10))
            elif t == '鈫?: b.clicked.connect(lambda: self._nudge(-1))
            elif t == '鈫?: b.clicked.connect(lambda: self._nudge(1))
            arr_l.addWidget(b, r, c)
        gl.addWidget(arr_w, 0, 3, 2, 1, Qt.AlignmentFlag.AlignCenter)
        return g

    def _ch_section(self):
        g = QGroupBox("Channel & System"); g.setStyleSheet(self._gs(TEXT_WHITE))
        gl = QGridLayout(g); gl.setSpacing(3); gl.setContentsMargins(5,10,5,4)
        self.c1b = QPushButton("CH1"); self.c1b.setCheckable(True); self.c1b.setChecked(True); self.c1b.setMinimumHeight(26)
        self.c1b.clicked.connect(lambda: self._ch_select(1))
        self.c2b = QPushButton("CH2"); self.c2b.setCheckable(True); self.c2b.setMinimumHeight(26)
        self.c2b.clicked.connect(lambda: self._ch_select(2))
        self.outb = QPushButton("Output"); self.outb.setCheckable(True); self.outb.setChecked(True); self.outb.setMinimumHeight(26)
        self.outb.toggled.connect(lambda v: self._output(v))
        gl.addWidget(self.c1b,0,0); gl.addWidget(self.c2b,0,1); gl.addWidget(self.outb,0,2)
        pb = QPushButton("Preset"); pb.clicked.connect(self._preset); pb.setMinimumHeight(22)
        ub = QPushButton("鈻?Load"); ub.clicked.connect(self._load_file); ub.setMinimumHeight(22)
        db = QPushButton("鉁?Draw"); db.clicked.connect(self._draw); db.setMinimumHeight(22)
        gl.addWidget(pb,1,0); gl.addWidget(ub,1,1); gl.addWidget(db,1,2)
        sb = QPushButton("Save"); sb.clicked.connect(self._export_csv); sb.setMinimumHeight(22)
        sb2 = QPushButton("WAV"); sb2.clicked.connect(self._export_wav); sb2.setMinimumHeight(22)
        gl.addWidget(sb,2,0); gl.addWidget(sb2,2,1)
        return g

    def _gs(self, c: QColor) -> str:
        return f"""
            QGroupBox {{ color:{c.name()}; border:1px solid #323532; border-radius:3px;
                margin-top:0.6em; padding-top:0.2em; background:#101210; font-weight:bold; font-size:9px; }}
            QGroupBox::title {{ subcontrol-origin:margin; left:6px; padding:0 3px; }}
        """

    def _style(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background:#000; }}
            QLabel {{ color:{TEXT_WHITE.name()}; font-size:10px; }}
            QPushButton {{
                background:#373a37; color:{TEXT_WHITE.name()};
                border:1px solid #323532; border-radius:3px; padding:4px 6px; font-size:10px;
            }}
            QPushButton:hover {{ background:#484b48; }}
            QPushButton:checked {{ background:#0082d2; border-color:#00befa; }}
            QPushButton#ch1_on {{ background:#c8aa0a; }}
            QPushButton#ch2_on {{ background:#008cd2; }}
            QPushButton#out_on {{ background:#1e8c1e; border-color:#2ebc2e; }}
            QComboBox {{ background:#373a37; color:{TEXT_WHITE.name()}; border:1px solid #323532; border-radius:3px; padding:2px 6px; }}
            QComboBox QAbstractItemView {{ background:#1a1c1a; color:{TEXT_WHITE.name()}; selection-background-color:#0082d2; }}
            QDoubleSpinBox {{ background:#373a37; color:{TEXT_WHITE.name()}; border:1px solid #323532; border-radius:3px; padding:2px 4px; }}
        """)

    # 鈹€鈹€ Actions 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    def _kp(self, key: str):
        """Numeric keypad pressed."""
        # Auto-activate frequency if nothing selected
        if self.scr.edit_param is None:
            self.scr.edit_param = 'freq'
            self.scr.edit_buf = ""

        if key == 'ok':
            try:
                val = float(self.scr.edit_buf) if self.scr.edit_buf else None
            except ValueError:
                val = None
            if val is not None and self.scr.edit_param:
                self._apply(self.scr.edit_param, val)
            self.scr.edit_param = None; self.scr.edit_buf = ""
        elif key == 'del':
            self.scr.edit_buf = self.scr.edit_buf[:-1]
        elif key == '卤':
            self.scr.edit_buf = self.scr.edit_buf[1:] if self.scr.edit_buf.startswith('-') else '-' + self.scr.edit_buf
        else:
            if key in '0123456789.':
                self.scr.edit_buf += key
        self._upd_sk(); self.scr.update()

    def _unit(self, unit: str):
        """Unit key pressed 鈥?confirms with unit conversion."""
        try:
            val = float(self.scr.edit_buf) if self.scr.edit_buf else None
        except ValueError:
            val = None

        if val is None:
            ch = self.ch[self.active_ch]
            p = self.scr.edit_param
            if p == 'freq': val = ch["freq"]
            elif p == 'amp': val = ch["amp"]
            elif p == 'offset': val = ch["offset"]
            elif p == 'phase': val = ch["phase"]
            else: return

        # Unit conversion
        p = self.scr.edit_param
        if p == 'freq':
            if unit == 'MHz': val *= 1000
            elif unit == 'Hz': val /= 1000
        elif p in ('amp', 'offset'):
            if unit == 'Vrms': val *= 2.828
            elif unit == 'dBm': val = 10**((val-13.01)/20)

        if p:
            self._apply(p, val)
        self.scr.edit_param = None; self.scr.edit_buf = ""
        self._upd_sk(); self.scr.update()

    def _apply(self, param: str, val: float):
        ch = self.ch[self.active_ch]
        if param == 'freq': ch["freq"] = max(0.000001, min(100000, val))
        elif param == 'amp': ch["amp"] = max(0.001, min(20, val))
        elif param == 'offset': ch["offset"] = max(-10, min(10, val))
        elif param == 'phase': ch["phase"] = max(-360, min(360, val))
        self._tick()

    def _nudge(self, d: int):
        """Knob/arrow nudge."""
        if self.scr.edit_param is None:
            self.scr.edit_param = 'freq'
        ch = self.ch[self.active_ch]; p = self.scr.edit_param
        if p == 'freq': ch["freq"] = max(0.000001, min(100000, ch["freq"]+d*0.001))
        elif p == 'amp': ch["amp"] = max(0.001, min(20, ch["amp"]+d*0.001))
        elif p == 'offset': ch["offset"] = max(-10, min(10, ch["offset"]+d*0.001))
        elif p == 'phase': ch["phase"] = (ch["phase"]+d*0.1)%360
        self._upd_sk(); self._tick()

    def _wf(self, t: str):
        if self._last_wf: self._last_wf.setChecked(False)
        b = self._wf_btns.get(t)
        if b: b.setChecked(True); self._last_wf = b
        self.ch[self.active_ch]["type"] = t
        self.ch[self.active_ch]["cached"] = None
        self.mod_on = self.sweep_on = False
        self.mod_btn.setChecked(False); self.swp_btn.setChecked(False)
        if t == "Arb": self._load_file()
        self._upd_sk(); self._tick()

    def _mod(self, v: bool):
        self.mod_on = v
        if v: self.sweep_on = False; self.swp_btn.setChecked(False)
        if v: self._open_mod_dlg()
        self._upd_sk(); self._tick()

    def _swp(self, v: bool):
        self.sweep_on = v
        if v: self.mod_on = False; self.mod_btn.setChecked(False)
        self._upd_sk(); self._tick()

    def _ch_select(self, c: int):
        self.active_ch = c
        self.c1b.setChecked(c==1); self.c2b.setChecked(c==2)
        self.scr.active_ch = f"CH{c}"; self.scr.edit_param = None; self.scr.edit_buf = ""
        # Update waveform button highlight for this channel's type
        wt = self.ch[c]["type"]
        if self._last_wf: self._last_wf.setChecked(False)
        b = self._wf_btns.get(wt)
        if b: b.setChecked(True); self._last_wf = b
        self._upd_sk(); self._tick()

    def _output(self, v: bool):
        self.ch[self.active_ch]["on"] = v
        self._tick()

    def _preset(self):
        self.ch[1] = {"type":"Sine","freq":1.0,"amp":1.0,"offset":0.0,"duty":0.5,"phase":0.0,"on":True,"cached":None}
        self.ch[2] = {"type":"Sine","freq":1.0,"amp":1.0,"offset":0.0,"duty":0.5,"phase":0.0,"on":False,"cached":None}
        self.mod_on = self.sweep_on = False
        self.mod_btn.setChecked(False); self.swp_btn.setChecked(False)
        if self._last_wf: self._last_wf.setChecked(False)
        self._wf_btns["Sine"].setChecked(True); self._last_wf = self._wf_btns["Sine"]
        self.scr.edit_param = None; self.scr.edit_buf = ""
        self._upd_sk(); self._tick()

    def _upd_sk(self):
        """Update screen state (edit buffer display handled in paint)."""
        self.scr.update()

    # 鈹€鈹€ Waveform Generation 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    def _gen(self, ch: dict) -> np.ndarray:
        wf, f, a, o, d, ph = ch["type"], ch["freq"]*1000, ch["amp"], ch["offset"], ch["duty"], ch["phase"]
        t = np.linspace(0, self.N/self.rate, self.N)
        pr = np.deg2rad(ph)

        if self.sweep_on:
            f0, f1 = self.sw_start*1000, self.sw_stop*1000
            k = (f1-f0)/self.sw_time
            return (a*np.sin(2*np.pi*np.cumsum(f0+k*t)/self.rate+pr)+o).astype(np.float64)

        if self.mod_on:
            return self._gen_mod(ch, t)

        if wf == "Sine": y = a*np.sin(2*np.pi*f*t+pr)+o
        elif wf == "Square": pn = (f*t+ph/360)%1.0; y = np.where(pn<d, a, -a)+o
        elif wf == "Ramp": pn = (f*t+ph/360)%1.0; y = a*(2*pn-1)+o
        elif wf == "Pulse":
            pd = 1/f if f>0 else 1; pn = (t/pd+ph/360)%1.0; y = np.where(pn<d*0.2, a, 0)+o
        elif wf == "Noise": y = a*(np.random.randn(self.N)*0.3)+o
        elif wf == "DC": y = np.full(self.N, a+o)
        elif wf == "Arb":
            c = ch.get("cached")
            y = a*c+o if c is not None else a*np.sin(2*np.pi*f*t+pr)+o
        else: y = a*np.sin(2*np.pi*f*t+pr)+o
        return y.astype(np.float64)

    def _gen_mod(self, ch: dict, t: np.ndarray) -> np.ndarray:
        m = self.mod_params or {"mod_type":"AM","carrier_freq":ch["freq"],"mod_freq":1.0,"depth":0.5}
        mt, fc = m.get("mod_type","AM"), m.get("carrier_freq",10)*1000
        fm, dp = m.get("mod_freq",1)*1000, m.get("depth",0.5)
        a, o = ch["amp"], ch["offset"]
        car, ms = np.sin(2*np.pi*fc*t), np.sin(2*np.pi*fm*t)
        if mt=="AM": y = a*(1+dp*ms)*car+o
        elif mt=="FM": y = a*np.sin(2*np.pi*fc*t+dp*ms)+o
        elif mt=="PM": y = a*np.sin(2*np.pi*fc*t+dp*np.pi*ms)+o
        elif mt=="FSK": y = a*np.where(ms>0, np.sin(2*np.pi*(fc+dp*1000)*t), np.sin(2*np.pi*(fc-dp*1000)*t))+o
        elif mt=="ASK": y = a*(0.5+0.5*ms)*car+o
        else: y = a*car+o
        return y.astype(np.float64)

    def _tick(self):
        if not self.running: return
        self.wf_data = []
        for cn in [1,2]:
            ch = self.ch[cn]
            if ch["on"]:
                d = self._gen(ch)
                self.wf_data.append({
                    "data":d, "color":YELLOW_CH1 if cn==1 else WAVE_CYAN,
                    "label":f"CH{cn} {ch['type']} {ch['freq']:.2f}kHz {ch['amp']:.2f}V",
                    "v_scale":max(ch["amp"]*1.5,0.01), "v_offset":ch["offset"],
                    "line_width":1.8 if cn==1 else 1.5, "visible":True,
                })
        self.scr.set_wf(self.wf_data)
        self.scr.ch1_on = self.ch[1]["on"]; self.scr.ch2_on = self.ch[2]["on"]
        self.scr.active_ch = f"CH{self.active_ch}"

        ach = self.ch[self.active_ch]
        self.scr.set_ro(
            f=f"{ach['freq']:.6f} kHz", a=f"{ach['amp']:.3f} Vpp",
            o=f"{ach['offset']:.3f} Vdc", p=f"{ach['phase']:.1f}掳")

        st = f"CH1:{self.ch[1]['type']} {self.ch[1]['freq']:.3f}kHz {self.ch[1]['amp']:.3f}Vpp"
        if self.ch[2]["on"]:
            st += f"  CH2:{self.ch[2]['type']} {self.ch[2]['freq']:.3f}kHz {self.ch[2]['amp']:.3f}Vpp"
        if self.mod_on: st += "  [MOD]"
        if self.sweep_on: st += "  [SWEEP]"
        self.st_l.setText(st)
        self.outb.setChecked(self.ch[self.active_ch]["on"])
        self.st_r.setText(f"{self.rate/1000:.0f}kSa/s | {self.N}pts")
        self.scr.update()

    # 鈹€鈹€ Dialogs 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    def _open_mod_dlg(self):
        d = QWidget(self, Qt.WindowType.Dialog)
        d.setWindowTitle("Modulation Config"); d.setMinimumSize(360,260)
        d.setStyleSheet(f"background:#101210; color:{TEXT_WHITE.name()};")
        l = QVBoxLayout(d); l.setSpacing(8); l.setContentsMargins(14,14,14,14)
        t = QLabel("Modulation Settings"); t.setStyleSheet(f"font-weight:bold; font-size:13px; color:#00befa;")
        l.addWidget(t)
        mt = QComboBox(); mt.addItems(["AM","FM","PM","FSK","ASK"])
        l.addLayout(self._row("Type:",mt))
        cf = QDoubleSpinBox(); cf.setRange(0.001,100000); cf.setValue(10); cf.setSuffix(" kHz")
        l.addLayout(self._row("Carrier:",cf))
        mf = QDoubleSpinBox(); mf.setRange(0.001,100000); mf.setValue(1); mf.setSuffix(" kHz")
        l.addLayout(self._row("Mod Freq:",mf))
        dp = QDoubleSpinBox(); dp.setRange(0.01,10); dp.setValue(0.5); dp.setSingleStep(0.05)
        l.addLayout(self._row("Depth:",dp))
        br = QHBoxLayout()
        ok = QPushButton("OK"); cx = QPushButton("Cancel"); cx.clicked.connect(d.close)
        ok.clicked.connect(lambda: self._mod_done({"mod_type":mt.currentText(),"carrier_freq":cf.value(),
                          "mod_freq":mf.value(),"depth":dp.value()}, d))
        br.addWidget(ok); br.addWidget(cx); br.addStretch(); l.addLayout(br); l.addStretch()
        d.show()

    def _row(self, label, w):
        r = QHBoxLayout(); lb = QLabel(label); lb.setFixedWidth(60); r.addWidget(lb); r.addWidget(w); r.addStretch(); return r

    def _mod_done(self, p, d):
        self.mod_params = p; d.close(); self._upd_sk(); self._tick()

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Waveform", "", "Waveform (*.csv *.txt *.dat);;All (*)")
        if not path:
            self.ch[self.active_ch]["type"] = "Sine"
            if self._last_wf: self._last_wf.setChecked(False)
            self._wf_btns["Sine"].setChecked(True); self._last_wf = self._wf_btns["Sine"]
            return
        try:
            data = np.loadtxt(path, delimiter=',')
            if data.ndim > 1: data = data[:,0]
            dmax = np.max(np.abs(data))
            if dmax > 0: data = data/dmax
            if len(data) != self.N:
                data = np.interp(np.linspace(0,1,self.N), np.linspace(0,1,len(data)), data)
            self.ch[self.active_ch]["cached"] = data
            self.ch[self.active_ch]["type"] = "Arb"
            self._upd_sk(); self._tick()
            QMessageBox.information(self,"Loaded",f"Loaded {len(data)} pts")
        except Exception as e: QMessageBox.warning(self,"Error",str(e))

    def _draw(self):
        d = DrawDialog(self)
        d.done.connect(self._draw_done)
        d.show()

    def _draw_done(self, data: np.ndarray):
        self.ch[self.active_ch]["cached"] = data
        self.ch[self.active_ch]["type"] = "Arb"
        if self._last_wf: self._last_wf.setChecked(False)
        b = self._wf_btns.get("Arb")
        if b: b.setChecked(True); self._last_wf = b
        self._upd_sk(); self._tick()

    def _export_csv(self):
        if not self.wf_data: return
        path, _ = QFileDialog.getSaveFileName(self,"Save CSV","waveform.csv","CSV (*.csv)")
        if not path: return
        d = self.wf_data[0]["data"]
        np.savetxt(path, np.column_stack([np.arange(len(d)),d]), delimiter=',',
                   header='Sample,Amplitude(V)', comments='')
        QMessageBox.information(self,"Saved",f"Exported to {path}")

    def _export_wav(self):
        if not self.wf_data: return
        path, _ = QFileDialog.getSaveFileName(self,"Export WAV","waveform.wav","WAV (*.wav)")
        if not path: return
        import wave
        d = self.wf_data[0]["data"]
        n = (d / max(np.abs(d)) * 32767).astype(np.int16)
        with wave.open(path,'w') as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(self.rate); wf.writeframes(n.tobytes())
        QMessageBox.information(self,"Saved",f"Exported to {path}")

    def closeEvent(self, e): self.running=False; self._timer.stop(); e.accept()


def main():
    app = QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__": main()
