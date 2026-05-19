import flet as ft
import requests
import webbrowser
import os
import threading
import tempfile
from datetime import datetime

# ===================================================================
# CẤU HÌNH API
# ===================================================================
BASE = "https://phimapi.com"
CDN  = "https://phimimg.com/"

API_NEW_UPDATE    = f"{BASE}/danh-sach/phim-moi-cap-nhat"
API_SEARCH        = f"{BASE}/v1/api/tim-kiem"
API_DETAIL        = f"{BASE}/phim/"
API_LIST_GENRES   = f"{BASE}/the-loai"
API_LIST_COUNTRIES= f"{BASE}/quoc-gia"

# Danh sách theo loại
API_TYPE = f"{BASE}/v1/api/danh-sach/"   # + phim-le / phim-bo / hoat-hinh / tv-shows / phim-vietsub

# Lọc nâng cao
API_GET_GENRE   = f"{BASE}/v1/api/the-loai/"
API_GET_COUNTRY = f"{BASE}/v1/api/quoc-gia/"
API_GET_YEAR    = f"{BASE}/v1/api/nam/"

REQUEST_TIMEOUT = 12

LOAI_PHIM = [
    ("🆕 Phim Mới",       API_NEW_UPDATE,          "Phim Mới Cập Nhật"),
    ("🎬 Phim Lẻ",        f"{API_TYPE}phim-le",     "Phim Lẻ"),
    ("📺 Phim Bộ",        f"{API_TYPE}phim-bo",     "Phim Bộ"),
    ("🎌 Hoạt Hình",      f"{API_TYPE}hoat-hinh",   "Hoạt Hình"),
    ("📡 TV Shows",        f"{API_TYPE}tv-shows",    "TV Shows"),
    ("🔤 Vietsub",         f"{API_TYPE}phim-vietsub","Phim Vietsub"),
]

# Màu sắc giao diện
CLR_BG        = "#0f0f1a"
CLR_SURFACE   = "#1a1a2e"
CLR_CARD      = "#16213e"
CLR_BORDER    = "#0f3460"
CLR_ACCENT    = "#e94560"
CLR_ACCENT2   = "#533483"
CLR_TEXT      = "#eaeaea"
CLR_SUBTEXT   = "#8892a4"
CLR_GOLD      = "#f0a500"

def fix_image_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("http"):
        return url
    return CDN + url.lstrip("/")

# ===================================================================
# APP CHÍNH
# ===================================================================
def main(page: ft.Page):
    page.title = "🎬 Phim Ông Tiến"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = CLR_BG
    page.padding = 0
    page.window.width  = 1280
    page.window.height = 820
    page.window.min_width  = 900
    page.window.min_height = 600

    # Áp dụng theme tùy chỉnh
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(primary=CLR_ACCENT),
        font_family="Roboto",
    )

    # ----------------------------------------------------------------
    # TRẠNG THÁI
    # ----------------------------------------------------------------
    state = {
        "current_page":    1,
        "current_api_base": API_NEW_UPDATE,
        "title_prefix":    "Phim Mới Cập Nhật",
        "is_loading":      False,
        "active_type_idx": 0,     # index loại phim đang chọn
    }

    # ----------------------------------------------------------------
    # HTML PLAYER
    # ----------------------------------------------------------------
    def open_html_player(link, name):
        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{name}</title>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{background:#000;display:flex;flex-direction:column;height:100vh;font-family:sans-serif}}
    #topbar{{background:linear-gradient(90deg,#0f3460,#e94560);color:#fff;padding:8px 14px;font-size:14px;
             display:flex;align-items:center;gap:8px;flex-shrink:0}}
    #topbar span{{opacity:.8;font-size:12px}}
    video{{flex:1;width:100%;background:#000;outline:none}}
  </style>
</head>
<body>
  <div id="topbar">🎬 <span>{name}</span></div>
  <video id="v" controls autoplay></video>
  <script>
    var v=document.getElementById('v');
    var src="{link}";
    if(Hls.isSupported()){{
      var hls=new Hls({{maxBufferLength:60,maxBufferSize:120*1000*1000}});
      hls.loadSource(src);hls.attachMedia(v);
      hls.on(Hls.Events.MANIFEST_PARSED,()=>v.play());
    }}else if(v.canPlayType('application/vnd.apple.mpegurl')){{
      v.src=src;v.play();
    }}
  </script>
</body>
</html>"""
        f = os.path.join(tempfile.gettempdir(), "phim_player.html")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(html)
        webbrowser.open(f"file:///{f}")

    # ================================================================
    # WIDGET ĐỊNH NGHĨA
    # ================================================================

    # ---- Status bar ------------------------------------------------
    status_bar = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.INFO_OUTLINE, color=CLR_GOLD, size=16),
            ft.Text("Đang tải...", color=CLR_GOLD, size=13, weight=ft.FontWeight.W_500,
                    expand=True),
            ft.ProgressRing(width=18, height=18, stroke_width=2,
                            color=CLR_ACCENT, visible=False),
        ], spacing=8),
        bgcolor=CLR_SURFACE,
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        border=ft.border.only(bottom=ft.BorderSide(1, CLR_BORDER)),
    )
    status_icon  = status_bar.content.controls[0]
    status_label = status_bar.content.controls[1]
    loading_ring = status_bar.content.controls[2]

    def set_status(msg, loading=False, icon=ft.Icons.INFO_OUTLINE, color=CLR_GOLD):
        status_icon.name  = icon
        status_icon.color = color
        status_label.value = msg
        status_label.color = color
        loading_ring.visible = loading
        status_bar.update()

    # ---- Episodes panel -------------------------------------------
    ep_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=6)
    ep_panel = ft.Container(
        content=ep_col,
        visible=False,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=CLR_SURFACE,
        border=ft.border.all(1, CLR_BORDER),
        border_radius=10,
        height=200,
        margin=ft.margin.only(bottom=8),
    )

    # ---- Grid phim ------------------------------------------------
    movies_grid = ft.GridView(
        expand=True,
        runs_count=5,
        max_extent=210,
        child_aspect_ratio=0.58,
        spacing=12,
        run_spacing=12,
    )

    # ---- Phân trang -----------------------------------------------
    page_label = ft.Text("Trang 1", color=CLR_TEXT, size=13, weight=ft.FontWeight.W_600)
    btn_prev = ft.IconButton(
        icon=ft.Icons.ARROW_BACK_IOS_ROUNDED,
        icon_color=CLR_ACCENT, icon_size=20,
        on_click=lambda e: change_page(-1),
        tooltip="Trang trước",
        style=ft.ButtonStyle(shape=ft.CircleBorder(),
                             bgcolor=ft.Colors.with_opacity(0.1, CLR_ACCENT)),
    )
    btn_next = ft.IconButton(
        icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
        icon_color=CLR_ACCENT, icon_size=20,
        on_click=lambda e: change_page(1),
        tooltip="Trang sau",
        style=ft.ButtonStyle(shape=ft.CircleBorder(),
                             bgcolor=ft.Colors.with_opacity(0.1, CLR_ACCENT)),
    )
    pagination_row = ft.Row(
        [btn_prev, page_label, btn_next],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # ================================================================
    # RENDER PHIM
    # ================================================================
    def render_movies(items):
        movies_grid.controls.clear()
        ep_panel.visible = False

        for item in items:
            slug  = item['slug']
            name  = item['name']
            orig  = item.get('origin_name', '')
            thumb = fix_image_url(item.get('thumb_url','') or item.get('poster_url',''))
            year  = str(item.get('year', ''))
            ep    = item.get('episode_current','')
            qual  = item.get('quality','')
            lang  = item.get('lang','')

            # Badge chất lượng
            def badge(text, bg):
                return ft.Container(
                    content=ft.Text(text, size=9, color="#fff", weight=ft.FontWeight.BOLD),
                    bgcolor=bg, border_radius=4,
                    padding=ft.padding.symmetric(horizontal=5, vertical=2),
                )

            badges = ft.Row([], spacing=4, wrap=True)
            if qual:
                badges.controls.append(badge(qual, CLR_ACCENT))
            if ep:
                short_ep = ep if len(ep) <= 14 else ep[:13]+"…"
                badges.controls.append(badge(short_ep, CLR_ACCENT2))

            card = ft.Container(
                content=ft.Column([
                    # Thumbnail
                    ft.Stack([
                        ft.Image(
                            src=thumb,
                            fit=ft.ImageFit.COVER,
                            border_radius=ft.border_radius.only(top_left=8, top_right=8),
                            height=200,
                            error_content=ft.Container(
                                content=ft.Icon(ft.Icons.MOVIE_ROUNDED, size=48, color=CLR_BORDER),
                                bgcolor=CLR_CARD, height=200,
                                border_radius=ft.border_radius.only(top_left=8, top_right=8),
                                alignment=ft.alignment.center,
                            ),
                        ),
                        # Gradient overlay
                        ft.Container(
                            height=200,
                            border_radius=ft.border_radius.only(top_left=8, top_right=8),
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_center,
                                end=ft.alignment.bottom_center,
                                colors=["#00000000", "#CC000000"],
                            ),
                        ),
                        # Badges bottom-left
                        ft.Container(
                            content=badges,
                            alignment=ft.alignment.bottom_left,
                            padding=ft.padding.all(6),
                        ),
                    ], height=200),
                    # Info
                    ft.Container(
                        content=ft.Column([
                            ft.Text(name, size=12, weight=ft.FontWeight.BOLD,
                                    color=CLR_TEXT, no_wrap=True,
                                    overflow=ft.TextOverflow.ELLIPSIS, tooltip=name),
                            ft.Text(orig or year, size=10, color=CLR_SUBTEXT,
                                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ], spacing=2),
                        padding=ft.padding.symmetric(horizontal=8, vertical=6),
                    ),
                ], spacing=0),
                on_click=lambda e, s=slug: _detail_thread(s),
                border_radius=8,
                bgcolor=CLR_CARD,
                border=ft.border.all(1, CLR_BORDER),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                animate_scale=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT),
                on_hover=lambda e: setattr(e.control, 'scale',
                                           ft.Scale(1.03) if e.data == "true" else ft.Scale(1)) or e.control.update(),
            )
            movies_grid.controls.append(card)
        page.update()

    # ================================================================
    # CHI TIẾT PHIM
    # ================================================================
    def _show_detail(slug):
        set_status("Đang lấy thông tin phim...", loading=True,
                   icon=ft.Icons.HOURGLASS_TOP_ROUNDED, color=CLR_GOLD)
        ep_col.controls.clear()
        ep_panel.visible = False
        ep_panel.update()

        try:
            res  = requests.get(f"{API_DETAIL}{slug}", timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            data = res.json()
            mv   = data['movie']
            eps  = data['episodes']

            title = f"{mv['name']} ({mv.get('year','')})"

            has_link = False
            for srv in eps:
                srv_name = srv['server_name']
                row = ft.Row(wrap=True, spacing=6, run_spacing=6)
                for ep in srv['server_data']:
                    lnk = ep.get('link_m3u8','')
                    nm  = ep.get('name', 'Tập ?')
                    if not lnk:
                        continue
                    has_link = True
                    cap = f"{mv['name']} — {nm}"
                    btn = ft.ElevatedButton(
                        text=nm,
                        icon=ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6),
                            bgcolor={
                                ft.ControlState.DEFAULT:  CLR_ACCENT2,
                                ft.ControlState.HOVERED:  CLR_ACCENT,
                            },
                            color=ft.Colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        ),
                        on_click=lambda e, l=lnk, c=cap: open_html_player(l, c),
                    )
                    row.controls.append(btn)
                if row.controls:
                    ep_col.controls.append(
                        ft.Text(f"▸ {srv_name}", color="#4ade80",
                                size=12, weight=ft.FontWeight.BOLD)
                    )
                    ep_col.controls.append(row)

            if has_link:
                ep_panel.visible = True
                set_status(f"🎬  {title}", icon=ft.Icons.CHECK_CIRCLE_OUTLINE, color="#4ade80")
            else:
                is_cinema = mv.get('chieurap', False)
                ep_cur    = mv.get('episode_current','')
                if is_cinema:
                    set_status(f"⚫ {title} — Đang chiếu rạp, chưa có link stream.",
                               icon=ft.Icons.THEATER_COMEDY, color=CLR_SUBTEXT)
                elif 'trailer' in ep_cur.lower():
                    set_status(f"🎞️ {title} — Mới có Trailer, chưa phát hành online.",
                               icon=ft.Icons.THEATERS_ROUNDED, color=CLR_SUBTEXT)
                else:
                    set_status(f"⚠️ {title} — Chưa có link xem, đang cập nhật.",
                               icon=ft.Icons.WARNING_AMBER_ROUNDED, color=CLR_GOLD)
        except requests.Timeout:
            set_status("⏰ Kết nối quá chậm, thử lại sau.", icon=ft.Icons.TIMER_OFF, color=CLR_ACCENT)
        except Exception as err:
            set_status(f"Lỗi: {err}", icon=ft.Icons.ERROR_OUTLINE, color=CLR_ACCENT)
            print(f"detail error: {err}")

        page.update()

    def _detail_thread(slug):
        threading.Thread(target=_show_detail, args=(slug,), daemon=True).start()

    # ================================================================
    # TẢI DỮ LIỆU
    # ================================================================
    def _load_worker(reset_page=False):
        if state["is_loading"]:
            return
        state["is_loading"] = True
        if reset_page:
            state["current_page"] = 1

        p    = state["current_page"]
        base = state["current_api_base"]
        page_label.value = f"Trang {p}"
        set_status(f"Đang tải {state['title_prefix']} — trang {p}...",
                   loading=True, icon=ft.Icons.HOURGLASS_TOP_ROUNDED)
        page_label.update()

        try:
            sep = "&" if "?" in base else "?"
            url = f"{base}{sep}page={p}&limit=24"
            print(f"GET {url}")
            res = requests.get(url, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            d = res.json()

            items = []
            if 'items' in d:
                items = d['items']
            elif 'data' in d and 'items' in d['data']:
                items = d['data']['items']

            if items:
                render_movies(items)
                set_status(f"✅  {state['title_prefix']} — trang {p}",
                           icon=ft.Icons.CHECK_CIRCLE_OUTLINE, color="#4ade80")
            else:
                movies_grid.controls.clear()
                set_status(f"Không có dữ liệu trang {p}.",
                           icon=ft.Icons.INBOX, color=CLR_SUBTEXT)
        except requests.Timeout:
            set_status("⏰ Kết nối quá chậm.", icon=ft.Icons.TIMER_OFF, color=CLR_ACCENT)
        except Exception as err:
            print(f"load error: {err}")
            set_status(f"Lỗi API: {err}", icon=ft.Icons.ERROR_OUTLINE, color=CLR_ACCENT)

        state["is_loading"] = False
        page.update()

    def load_data(reset_page=False):
        threading.Thread(target=_load_worker, args=(reset_page,), daemon=True).start()

    def change_page(delta):
        nxt = state["current_page"] + delta
        if nxt < 1:
            return
        state["current_page"] = nxt
        load_data(reset_page=False)

    def set_category(api_url, title):
        state["current_api_base"] = api_url
        state["title_prefix"]     = title
        load_data(reset_page=True)

    # ================================================================
    # SEARCH BOX
    # ================================================================
    search_field = ft.TextField(
        hint_text="🔍  Tìm kiếm phim...",
        border_radius=24,
        border_color=CLR_BORDER,
        focused_border_color=CLR_ACCENT,
        bgcolor=CLR_SURFACE,
        color=CLR_TEXT,
        cursor_color=CLR_ACCENT,
        hint_style=ft.TextStyle(color=CLR_SUBTEXT),
        content_padding=ft.padding.symmetric(horizontal=18, vertical=10),
        expand=True,
        height=44,
        on_submit=lambda e: _do_search(),
    )
    def _do_search():
        kw = search_field.value.strip()
        if not kw:
            return
        set_category(f"{API_SEARCH}?keyword={kw}", f"Tìm: {kw}")

    search_btn = ft.IconButton(
        icon=ft.Icons.SEARCH_ROUNDED,
        icon_color=CLR_ACCENT,
        icon_size=22,
        on_click=lambda e: _do_search(),
        tooltip="Tìm kiếm",
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            bgcolor=ft.Colors.with_opacity(0.12, CLR_ACCENT),
        ),
    )
    search_row = ft.Container(
        content=ft.Row([search_field, search_btn], spacing=8),
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        bgcolor=CLR_BG,
        border=ft.border.only(bottom=ft.BorderSide(1, CLR_BORDER)),
    )

    # ================================================================
    # TYPE TABS (Phim Lẻ / Phim Bộ / ...)
    # ================================================================
    type_tab_row = ft.Row([], spacing=6, scroll=ft.ScrollMode.AUTO)

    def _make_type_tabs():
        type_tab_row.controls.clear()
        for idx, (label, api_url, title) in enumerate(LOAI_PHIM):
            is_active = (idx == state["active_type_idx"])
            tab = ft.Container(
                content=ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                                color=CLR_TEXT if is_active else CLR_SUBTEXT),
                bgcolor=CLR_ACCENT if is_active else ft.Colors.with_opacity(0.08, CLR_TEXT),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=14, vertical=7),
                on_click=lambda e, i=idx, u=api_url, t=title: _select_type(i, u, t),
                ink=True,
            )
            type_tab_row.controls.append(tab)

    def _select_type(idx, api_url, title):
        state["active_type_idx"] = idx
        _make_type_tabs()
        type_tab_row.update()
        set_category(api_url, title)

    _make_type_tabs()

    type_tab_container = ft.Container(
        content=type_tab_row,
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        bgcolor=CLR_SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, CLR_BORDER)),
    )

    # ================================================================
    # SIDEBAR
    # ================================================================
    sidebar_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)

    def _build_sidebar():
        sidebar_col.controls.clear()

        # Logo / Header
        sidebar_col.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("🎬", size=32),
                    ft.Text("Phim Ông Tiến", size=14, weight=ft.FontWeight.BOLD,
                            color=CLR_TEXT),
                    ft.Text("Movie Streaming", size=10, color=CLR_SUBTEXT),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=20),
                border=ft.border.only(bottom=ft.BorderSide(1, CLR_BORDER)),
            )
        )

        # ---- Thể loại ---
        def _section_title(t):
            return ft.Container(
                content=ft.Text(t.upper(), size=10, color=CLR_SUBTEXT,
                                weight=ft.FontWeight.BOLD,
                                style=ft.TextStyle(letter_spacing=1.2)),
                padding=ft.padding.only(left=14, top=14, bottom=6),
            )

        def _sidebar_item(label, on_click_fn, icon_name=None):
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon_name, size=15, color=CLR_SUBTEXT) if icon_name else ft.Container(width=4),
                    ft.Text(label, size=13, color=CLR_TEXT),
                ], spacing=8),
                on_click=on_click_fn,
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                border_radius=6,
                ink=True,
                on_hover=lambda e: (
                    setattr(e.control, 'bgcolor',
                            ft.Colors.with_opacity(0.08, CLR_ACCENT) if e.data=="true" else None)
                    or e.control.update()
                ),
            )

        # Thể loại
        sidebar_col.controls.append(_section_title("Thể Loại"))
        try:
            r = requests.get(API_LIST_GENRES, timeout=REQUEST_TIMEOUT)
            glist = r.json() if isinstance(r.json(), list) else r.json().get('items',[])
            for g in glist:
                sidebar_col.controls.append(
                    _sidebar_item(
                        g['name'],
                        lambda e, s=g['slug'], n=g['name']:
                            set_category(f"{API_GET_GENRE}{s}", f"Thể loại: {n}"),
                        ft.Icons.LABEL_OUTLINE,
                    )
                )
        except Exception as ex:
            print(f"Sidebar genre error: {ex}")
            sidebar_col.controls.append(ft.Text("Lỗi tải thể loại", color=CLR_ACCENT, size=12))

        # Quốc gia
        sidebar_col.controls.append(_section_title("Quốc Gia"))
        try:
            r = requests.get(API_LIST_COUNTRIES, timeout=REQUEST_TIMEOUT)
            clist = r.json() if isinstance(r.json(), list) else r.json().get('items',[])
            for c in clist:
                sidebar_col.controls.append(
                    _sidebar_item(
                        c['name'],
                        lambda e, s=c['slug'], n=c['name']:
                            set_category(f"{API_GET_COUNTRY}{s}", f"Quốc gia: {n}"),
                        ft.Icons.FLAG_OUTLINED,
                    )
                )
        except Exception as ex:
            print(f"Sidebar country error: {ex}")
            sidebar_col.controls.append(ft.Text("Lỗi tải quốc gia", color=CLR_ACCENT, size=12))

        # Năm
        sidebar_col.controls.append(_section_title("Năm Phát Hành"))
        cur_year = datetime.now().year
        for yr in range(cur_year, 2009, -1):
            sidebar_col.controls.append(
                _sidebar_item(
                    str(yr),
                    lambda e, y=yr: set_category(f"{API_GET_YEAR}{y}", f"Năm {y}"),
                    ft.Icons.CALENDAR_TODAY_OUTLINED,
                )
            )
        sidebar_col.update()

    # ================================================================
    # BỐ CỤC TỔNG THỂ
    # ================================================================
    sidebar = ft.Container(
        content=sidebar_col,
        width=200,
        bgcolor=CLR_SURFACE,
        border=ft.border.only(right=ft.BorderSide(1, CLR_BORDER)),
    )

    content_col = ft.Column([
        search_row,
        type_tab_container,
        status_bar,
        ft.Container(
            content=ft.Column([
                ep_panel,
                movies_grid,
                ft.Container(content=pagination_row, padding=ft.padding.symmetric(vertical=10)),
            ], spacing=0, expand=True),
            expand=True,
            padding=ft.padding.all(12),
        ),
    ], spacing=0, expand=True)

    page.add(
        ft.Row([sidebar, content_col], spacing=0, expand=True)
    )

    # Tải sidebar không đồng bộ
    threading.Thread(target=_build_sidebar, daemon=True).start()

    # Tải phim mới ngay khi khởi động
    set_category(API_NEW_UPDATE, "Phim Mới Cập Nhật")


if __name__ == "__main__":
    ft.app(target=main)