import flet as ft
import requests
import webbrowser
import os
from datetime import datetime

# --- CẤU HÌNH API ---
API_NEW_UPDATE = "https://phimapi.com/danh-sach/phim-moi-cap-nhat"
API_SEARCH = "https://phimapi.com/v1/api/tim-kiem"
API_DETAIL = "https://phimapi.com/phim/"
API_LIST_GENRES = "https://phimapi.com/the-loai"
API_LIST_COUNTRIES = "https://phimapi.com/quoc-gia"

# API Lọc
API_GET_GENRE = "https://phimapi.com/v1/api/the-loai/"
API_GET_COUNTRY = "https://phimapi.com/v1/api/quoc-gia/"
API_GET_YEAR = "https://phimapi.com/v1/api/nam/"

def main(page: ft.Page):
    page.title = "Phim Ông Tiến"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.window_width = 1200
    page.window_height = 800

    # --- BIẾN TOÀN CỤC QUẢN LÝ TRANG ---
    # Dùng list để chứa giá trị thay đổi được trong hàm con
    state = {
        "current_page": 1,
        "current_api_base": API_NEW_UPDATE, # Mặc định là phim mới
        "current_params": "", # Các tham số phụ như keyword search
        "title_prefix": "Phim Mới Cập Nhật"
    }

    # --- HÀM PLAYER (HTML5) ---
    def open_html_player(link, name):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Đang xem: {name}</title>
            <style>
                body {{ margin: 0; background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; }}
                video {{ width: 100%; height: 100%; }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
        </head>
        <body>
            <video id="video" controls autoplay></video>
            <script>
                var video = document.getElementById('video');
                var videoSrc = "{link}";
                if (Hls.isSupported()) {{
                    var hls = new Hls();
                    hls.loadSource(videoSrc);
                    hls.attachMedia(video);
                }}
                else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                    video.src = videoSrc;
                }}
            </script>
        </body>
        </html>
        """
        file_path = os.path.abspath("watch.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        webbrowser.open(f"file://{file_path}")

    # --- GIAO DIỆN CHÍNH ---
    movies_grid = ft.GridView(
        expand=True,
        runs_count=5,
        max_extent=200,
        child_aspect_ratio=0.65,
        spacing=10,
        run_spacing=10,
    )
    
    status_text = ft.Text("Đang tải dữ liệu...", color=ft.colors.AMBER, size=16, weight="bold")
    
    # Hiển thị số trang hiện tại
    page_info_text = ft.Text("Trang 1", color=ft.colors.WHITE, weight="bold")

    episodes_view = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    episode_container = ft.Container(
        content=episodes_view,
        visible=False,
        padding=10,
        bgcolor=ft.colors.BLACK45,
        border_radius=10,
        height=200,
        border=ft.border.all(1, ft.colors.WHITE24)
    )

    # --- HÀM VẼ GIAO DIỆN ---
    def render_movies(items):
        movies_grid.controls.clear()
        episode_container.visible = False
        img_domain = "https://img.phimapi.com/" 

        for item in items:
            slug = item['slug']
            name = item['name']
            thumb = item.get('thumb_url', '') or item.get('poster_url', '')
            if "http" not in thumb:
                thumb = f"{img_domain}/{thumb}"

            card = ft.Container(
                content=ft.Column([
                    ft.Image(src=thumb, fit=ft.ImageFit.COVER, border_radius=5, height=220),
                    ft.Text(name, size=14, weight="bold", no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"{item.get('year', '')}", size=12, color="grey")
                ], spacing=2),
                on_click=lambda e, s=slug: show_detail(e, s),
                padding=5,
                border_radius=8,
                bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE),
                ink=True
            )
            movies_grid.controls.append(card)
        page.update()

    # --- HÀM CHI TIẾT PHIM ---
    def show_detail(e, slug):
        status_text.value = "⏳ Đang lấy thông tin phim..."
        status_text.update()
        episodes_view.controls.clear()
        episode_container.visible = False

        try:
            res = requests.get(f"{API_DETAIL}{slug}")
            data = res.json()
            movie = data['movie']
            episodes = data['episodes']

            status_text.value = f"🎬 {movie['name']} ({movie['year']})"

            if episodes:
                for server in episodes:
                    server_name = server['server_name']
                    wrap_episodes = ft.Row(wrap=True, spacing=5)
                    episodes_view.controls.append(ft.Text(f"Server: {server_name}", color="green", weight="bold"))
                    episodes_view.controls.append(wrap_episodes)

                    for ep in server['server_data']:
                        link = ep['link_m3u8']
                        name = ep['name']
                        btn = ft.ElevatedButton(
                            text=name,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), bgcolor=ft.colors.BLUE_GREY_800),
                            on_click=lambda e, l=link, n=f"{movie['name']} - {name}": open_html_player(l, n)
                        )
                        wrap_episodes.controls.append(btn)
                episode_container.visible = True
            else:
                status_text.value = "❌ Phim đang cập nhật tập."
        except Exception as err:
            status_text.value = f"Lỗi: {err}"
        page.update()

    # --- HÀM TẢI DỮ LIỆU CHÍNH (QUAN TRỌNG) ---
    def load_data(reset_page=False):
        if reset_page:
            state["current_page"] = 1
        
        current_p = state["current_page"]
        base_url = state["current_api_base"]
        
        # Cập nhật text trạng thái
        status_text.value = f"⏳ {state['title_prefix']} - Đang tải trang {current_p}..."
        page_info_text.value = f"Trang {current_p}"
        status_text.update()
        page_info_text.update()

        try:
            # Xử lý URL: Nếu URL đã có dấu '?' thì dùng '&page=', ngược lại dùng '?page='
            separator = "&" if "?" in base_url else "?"
            full_url = f"{base_url}{separator}page={current_p}&limit=24"
            
            # Debug URL để kiểm tra
            print(f"Calling API: {full_url}")

            res = requests.get(full_url)
            data = res.json()
            
            # Xử lý cấu trúc JSON khác nhau của các API
            items = []
            if 'items' in data: 
                items = data['items'] # Cấu trúc phim mới
            elif 'data' in data and 'items' in data['data']: 
                items = data['data']['items'] # Cấu trúc tìm kiếm/thể loại
            
            if items:
                render_movies(items)
                status_text.value = f"✅ {state['title_prefix']} (Trang {current_p})"
            else:
                status_text.value = f"⚠️ Không có dữ liệu ở trang {current_p}."
                movies_grid.controls.clear()
        except Exception as err:
            print(f"Lỗi tải: {err}")
            status_text.value = "Lỗi kết nối API."
        
        page.update()

    # --- HÀM ĐIỀU HƯỚNG TRANG ---
    def change_page(delta):
        new_page = state["current_page"] + delta
        if new_page < 1: return # Không cho lùi quá trang 1
        
        state["current_page"] = new_page
        load_data(reset_page=False)

    # --- HÀM THIẾT LẬP LOẠI PHIM ---
    def set_category(api_url, title):
        state["current_api_base"] = api_url
        state["title_prefix"] = title
        load_data(reset_page=True) # Reset về trang 1 khi chuyển thể loại

    def search_movies(e):
        keyword = search_box.value
        if not keyword: return
        # API tìm kiếm cần ?keyword=abc trước
        url = f"{API_SEARCH}?keyword={keyword}"
        set_category(url, f"Tìm kiếm: {keyword}")

    # --- SIDEBAR ---
    def create_sidebar():
        sidebar_content = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=5)
        
        # Nút Trang Chủ
        sidebar_content.controls.append(
            ft.Container(
                content=ft.Row([ft.Icon(ft.icons.HOME, color="yellow"), ft.Text("Phim Mới", weight="bold")]),
                on_click=lambda e: set_category(API_NEW_UPDATE, "Phim Mới Cập Nhật"),
                padding=10, border_radius=5, ink=True
            )
        )

        # Thể Loại
        genre_tiles = []
        try:
            res = requests.get(API_LIST_GENRES)
            data = res.json()
            items = data if isinstance(data, list) else data.get('items', [])
            for item in items:
                genre_tiles.append(
                    ft.ListTile(
                        title=ft.Text(item['name'], size=13),
                        on_click=lambda e, s=item['slug'], n=item['name']: set_category(f"{API_GET_GENRE}{s}", f"Thể loại: {n}")
                    )
                )
        except: pass
        
        sidebar_content.controls.append(
            ft.ExpansionTile(title=ft.Text("Thể Loại"), leading=ft.Icon(ft.icons.CATEGORY), controls=genre_tiles, collapsed_text_color=ft.colors.AMBER, text_color=ft.colors.AMBER)
        )

        # Quốc Gia
        country_tiles = []
        try:
            res = requests.get(API_LIST_COUNTRIES)
            data = res.json()
            items = data if isinstance(data, list) else data.get('items', [])
            for item in items:
                country_tiles.append(
                    ft.ListTile(
                        title=ft.Text(item['name'], size=13),
                        on_click=lambda e, s=item['slug'], n=item['name']: set_category(f"{API_GET_COUNTRY}{s}", f"Quốc gia: {n}")
                    )
                )
        except: pass

        sidebar_content.controls.append(
            ft.ExpansionTile(title=ft.Text("Quốc Gia"), leading=ft.Icon(ft.icons.PUBLIC), controls=country_tiles, collapsed_text_color=ft.colors.AMBER, text_color=ft.colors.AMBER)
        )

        # Năm
        year_tiles = []
        current_year = datetime.now().year
        for year in range(current_year, 2009, -1):
            year_tiles.append(
                ft.ListTile(
                    title=ft.Text(str(year), size=13),
                    on_click=lambda e, y=year: set_category(f"{API_GET_YEAR}{y}", f"Năm phát hành: {y}")
                )
            )

        sidebar_content.controls.append(
            ft.ExpansionTile(title=ft.Text("Năm"), leading=ft.Icon(ft.icons.CALENDAR_MONTH), controls=year_tiles, collapsed_text_color=ft.colors.AMBER, text_color=ft.colors.AMBER)
        )

        return ft.Container(content=sidebar_content, width=220, padding=10, border=ft.border.only(right=ft.border.BorderSide(1, ft.colors.WHITE10)))

    # --- BỐ CỤC CHÍNH ---
    search_box = ft.TextField(hint_text="Nhập tên phim...", on_submit=search_movies, expand=True, height=40, content_padding=10, border_radius=20)
    search_btn = ft.IconButton(icon=ft.icons.SEARCH, on_click=search_movies, icon_color=ft.colors.AMBER)
    
    # THANH PHÂN TRANG (MỚI)
    pagination_controls = ft.Row(
        [
            ft.IconButton(icon=ft.icons.ARROW_BACK_IOS, on_click=lambda e: change_page(-1), tooltip="Trang trước"),
            page_info_text,
            ft.IconButton(icon=ft.icons.ARROW_FORWARD_IOS, on_click=lambda e: change_page(1), tooltip="Trang sau"),
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    sidebar = create_sidebar()

    content_area = ft.Column([
        ft.Row([search_box, search_btn]),
        status_text,
        episode_container,
        movies_grid,
        ft.Container(content=pagination_controls, padding=10) # Đặt phân trang ở dưới cùng
    ], expand=True)

    page.add(
        ft.Row([sidebar, content_area], expand=True)
    )

    # Tải lần đầu
    set_category(API_NEW_UPDATE, "Phim Mới Cập Nhật")

if __name__ == "__main__":
    ft.app(target=main)