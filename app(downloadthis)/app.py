import sys
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Auto-install required packages if missing
for pkg in ["requests", "pillow", "feedparser"]:
    try:
        __import__(pkg)
    except ImportError:
        install(pkg)

import requests
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading
from PIL import Image, ImageTk
import io
import feedparser
import urllib.parse

THANKYOU_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Thank You!</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f7f7f7;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }
        .thankyou-container {
            background: #fff;
            padding: 2rem 3rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
        }
        h1 {
            color: #2d8cff;
            margin-bottom: 1rem;
        }
        p {
            color: #333;
            font-size: 1.2rem;
        }
    </style>
</head>
<body>
    <div class="thankyou-container">
        <h1>Thank You!</h1>
        <p>Thank you for using our app.<br>
        All use is appreciated!</p>
    </div>
</body>
</html>
"""

GAMERPOWER_API = "https://www.gamerpower.com/api/giveaways"
CHEAPSHARK_API = "https://www.cheapshark.com/api/1.0/deals"
CHEAPSHARK_STORES_API = "https://www.cheapshark.com/api/1.0/stores"

def get_store_map():
    try:
        resp = requests.get(CHEAPSHARK_STORES_API, timeout=10)
        resp.raise_for_status()
        stores = resp.json()
        return {store['storeID']: store['storeName'] for store in stores}
    except Exception:
        # fallback: just show storeID
        return {}

class GameDealsApp:
    def __init__(self, root):
        self.root = root
        root.title("Ultimate Game Deals & Free Giveaways Finder")
        root.geometry("1200x750")
        root.resizable(False, False)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=32, font=('Segoe UI', 11))
        self.style.configure("TButton", font=('Segoe UI', 11))
        self.style.configure("TLabel", font=('Segoe UI', 11))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Tabs
        self.free_tab = ttk.Frame(self.notebook)
        self.deals_tab = ttk.Frame(self.notebook)
        self.news_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.free_tab, text='🎁 Free Giveaways')
        self.notebook.add(self.deals_tab, text='💰 Game Deals')
        self.notebook.add(self.news_tab, text='📰 Gaming News')

        self.store_map = get_store_map()

        self.setup_free_tab()
        self.setup_deals_tab()
        self.setup_news_tab()

        # Load data
        self.load_free_giveaways()
        self.load_game_deals()
        self.load_news()

        # Auto-refresh every 5 mins
        self.root.after(5 * 60 * 1000, self.auto_refresh)

    # ---------- FREE GIVEAWAYS TAB ----------
    def setup_free_tab(self):
        frame = self.free_tab

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', pady=5)

        ttk.Label(control_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.free_search_var = tk.StringVar()
        free_search_entry = ttk.Entry(control_frame, textvariable=self.free_search_var, width=30)
        free_search_entry.pack(side='left')
        free_search_entry.bind('<Return>', lambda e: self.filter_free())

        ttk.Button(control_frame, text="Filter", command=self.filter_free).pack(side='left', padx=5)

        ttk.Label(control_frame, text="Platform:").pack(side='left', padx=(15,5))
        self.platform_var = tk.StringVar(value="all")
        platforms = ['all', 'pc', 'steam', 'epic-games-store', 'gog', 'origin', 'ubisoft']
        platform_menu = ttk.OptionMenu(control_frame, self.platform_var, 'all', *platforms, command=lambda e: self.load_free_giveaways())
        platform_menu.pack(side='left')

        # Treeview setup
        columns = ('Title', 'Platforms', 'Value (USD)', 'Expires', 'Link')
        self.free_tree = ttk.Treeview(frame, columns=columns, show='headings', height=20)
        for col in columns[:-1]:
            self.free_tree.heading(col, text=col)
            self.free_tree.column(col, width=170, anchor='w')
        self.free_tree.heading('Link', text='Link')
        self.free_tree.column('Link', width=60, anchor='center')

        self.free_tree.pack(fill='both', expand=True, padx=5, pady=5)

        self.free_tree.bind('<Double-1>', self.open_selected_free)
        ttk.Button(frame, text="Copy Selected Link", command=self.copy_free_link).pack(pady=5)

    def load_free_giveaways(self):
        def fetch():
            try:
                platform = self.platform_var.get()
                url = GAMERPOWER_API
                if platform != 'all':
                    url += f"?platform={platform}"
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                self.free_giveaways = resp.json()
                self.filtered_free_giveaways = self.free_giveaways
                self.show_free(self.free_giveaways)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load giveaways: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    def show_free(self, giveaways):
        self.free_tree.delete(*self.free_tree.get_children())
        for g in giveaways:
            title = g.get('title', 'N/A')
            platforms = ", ".join(g.get('platforms', []))
            value = g.get('worth', 'N/A')
            expires = g.get('end_date', 'N/A')
            link = g.get('open_giveaway_url', '')
            self.free_tree.insert('', 'end', values=(title, platforms, value, expires, "Open"))

    def filter_free(self):
        keyword = self.free_search_var.get().lower()
        filtered = [g for g in self.free_giveaways if keyword in g.get('title','').lower()]
        self.filtered_free_giveaways = filtered
        self.show_free(filtered)

    def open_selected_free(self, event):
        item = self.free_tree.selection()
        if item:
            index = self.free_tree.index(item[0])
            giveaway = self.filtered_free_giveaways[index]
            link = giveaway.get('open_giveaway_url')
            if link:
                webbrowser.open(link)

    def copy_free_link(self):
        item = self.free_tree.selection()
        if item:
            index = self.free_tree.index(item[0])
            giveaway = self.filtered_free_giveaways[index]
            link = giveaway.get('open_giveaway_url')
            if link:
                self.root.clipboard_clear()
                self.root.clipboard_append(link)
                messagebox.showinfo("Copied", "Giveaway link copied to clipboard!")

    # ---------- GAME DEALS TAB ----------
    def setup_deals_tab(self):
        frame = self.deals_tab

        # Split left (tree) and right (image/details)
        main_pane = tk.PanedWindow(frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill='both', expand=True)

        # Left: controls + tree
        left_frame = ttk.Frame(main_pane)
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill='x', pady=5)

        ttk.Label(control_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.deal_search_var = tk.StringVar()
        deal_search_entry = ttk.Entry(control_frame, textvariable=self.deal_search_var, width=30)
        deal_search_entry.pack(side='left')
        deal_search_entry.bind('<Return>', lambda e: self.load_game_deals())

        ttk.Label(control_frame, text="Sort by:").pack(side='left', padx=(15,5))
        self.sort_var = tk.StringVar(value="Deal Rating")
        sort_options = ['Deal Rating', 'Price', 'Savings']
        sort_menu = ttk.OptionMenu(control_frame, self.sort_var, 'Deal Rating', *sort_options, command=lambda e: self.load_game_deals())
        sort_menu.pack(side='left')

        columns = ('Title', 'Store', 'Sale Price', 'Normal Price', 'Savings (%)', 'Link')
        self.deals_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=18)
        widths = [250, 120, 100, 100, 100, 50]
        for col, width in zip(columns, widths):
            self.deals_tree.heading(col, text=col)
            self.deals_tree.column(col, width=width, anchor='w' if col == 'Title' else 'center')

        self.deals_tree.pack(fill='both', expand=True, padx=5, pady=5)
        self.deals_tree.bind('<Double-1>', self.open_selected_deal)
        ttk.Button(left_frame, text="Copy Selected Link", command=self.copy_deal_link).pack(pady=5)
        ttk.Button(left_frame, text="Copy All Deals", command=self.copy_all_deals).pack(pady=5)

        main_pane.add(left_frame, stretch="always")

        # Right: image and details
        right_frame = ttk.Frame(main_pane, width=320)
        right_frame.pack_propagate(False)
        self.deal_img_label = ttk.Label(right_frame)
        self.deal_img_label.pack(pady=10)
        self.deal_info_label = ttk.Label(right_frame, justify='left', wraplength=300)
        self.deal_info_label.pack(pady=10)
        main_pane.add(right_frame)

        self.deals_tree.bind('<<TreeviewSelect>>', self.show_selected_deal_image)
        self.deal_img = None  # Keep reference

    def load_game_deals(self):
        def fetch():
            try:
                query = self.deal_search_var.get().strip()
                sort_map = {
                    'Deal Rating': 'dealRating',
                    'Price': 'price',
                    'Savings': 'savings'
                }
                sort_by = sort_map.get(self.sort_var.get(), 'dealRating')
                params = {
                    'storeID': None,  # All stores
                    'sortBy': sort_by,
                    'desc': '1',
                    'pageSize': '50',
                    'title': query if query else None,
                }
                params = {k: v for k, v in params.items() if v is not None}
                resp = requests.get(CHEAPSHARK_API, params=params, timeout=15)
                resp.raise_for_status()
                self.game_deals = resp.json()
                self.show_deals(self.game_deals)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load game deals: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    def show_deals(self, deals):
        self.deals_tree.delete(*self.deals_tree.get_children())
        self.current_deals = deals
        for d in deals:
            title = d.get('title', 'N/A')
            store_id = d.get('storeID', 'N/A')
            store = self.store_map.get(store_id, store_id)
            sale_price = f"${d.get('salePrice', 'N/A')}"
            normal_price = f"${d.get('normalPrice', 'N/A')}"
            savings = f"{d.get('savings', '0')[:4]}%" if 'savings' in d else '0%'
            self.deals_tree.insert('', 'end', values=(title, store, sale_price, normal_price, savings, "Open"))

    def show_selected_deal_image(self, event):
        item = self.deals_tree.selection()
        if item:
            index = self.deals_tree.index(item[0])
            deal = self.current_deals[index]
            thumb_url = deal.get('thumb')
            info = f"Title: {deal.get('title', 'N/A')}\nStore: {self.store_map.get(deal.get('storeID',''),deal.get('storeID',''))}\nSale Price: ${deal.get('salePrice', 'N/A')}\nNormal Price: ${deal.get('normalPrice', 'N/A')}\nSavings: {deal.get('savings', '0')[:4]}%\n"
            self.deal_info_label.config(text=info)
            if thumb_url:
                try:
                    resp = requests.get(thumb_url, timeout=10)
                    img_data = resp.content
                    img = Image.open(io.BytesIO(img_data)).resize((220, 110))
                    self.deal_img = ImageTk.PhotoImage(img)
                    self.deal_img_label.config(image=self.deal_img)
                except Exception:
                    self.deal_img_label.config(image='')
            else:
                self.deal_img_label.config(image='')

    def open_selected_deal(self, event):
        item = self.deals_tree.selection()
        if item:
            index = self.deals_tree.index(item[0])
            deal = self.current_deals[index]
            deal_link = f"https://www.cheapshark.com/redirect?dealID={deal.get('dealID')}"
            webbrowser.open(deal_link)

    def copy_deal_link(self):
        item = self.deals_tree.selection()
        if item:
            index = self.deals_tree.index(item[0])
            deal = self.current_deals[index]
            deal_link = f"https://www.cheapshark.com/redirect?dealID={deal.get('dealID')}"
            self.root.clipboard_clear()
            self.root.clipboard_append(deal_link)
            messagebox.showinfo("Copied", "Deal link copied to clipboard!")

    def copy_all_deals(self):
        if not hasattr(self, "current_deals") or not self.current_deals:
            messagebox.showinfo("Info", "No deals to copy.")
            return
        lines = []
        for d in self.current_deals:
            store = self.store_map.get(d.get('storeID',''), d.get('storeID',''))
            line = f"{d.get('title','N/A')} | Store: {store} | Sale: ${d.get('salePrice','N/A')} | Normal: ${d.get('normalPrice','N/A')} | Savings: {d.get('savings','0')[:4]}% | https://www.cheapshark.com/redirect?dealID={d.get('dealID')}"
            lines.append(line)
        all_text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(all_text)
        messagebox.showinfo("Copied", "All deals copied to clipboard!")

    # ---------- GAMING NEWS TAB ----------
    def setup_news_tab(self):
        frame = self.news_tab

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', pady=5)

        ttk.Label(control_frame, text="News Type:").pack(side='left', padx=(0, 5))
        self.news_type_var = tk.StringVar(value="PC News")
        news_types = ["PC News", "Fortnite", "Roblox"]
        news_menu = ttk.OptionMenu(control_frame, self.news_type_var, "PC News", *news_types, command=lambda e: self.load_news())
        news_menu.pack(side='left')

        ttk.Button(control_frame, text="Refresh", command=self.load_news).pack(side='left', padx=10)

        self.news_tree = ttk.Treeview(frame, columns=("Title", "Source", "Summary"), show='headings', height=18)
        self.news_tree.heading("Title", text="Title")
        self.news_tree.heading("Source", text="Source")
        self.news_tree.heading("Summary", text="Summary")
        self.news_tree.column("Title", width=420, anchor='w')
        self.news_tree.column("Source", width=120, anchor='w')
        self.news_tree.column("Summary", width=500, anchor='w')
        self.news_tree.pack(fill='both', expand=True, padx=5, pady=5)

        self.news_tree.bind('<Double-1>', self.open_selected_news)
        self.news_tree.bind('<<TreeviewSelect>>', self.show_news_summary)

        self.news_articles = []
        self.news_summary_label = ttk.Label(frame, text="", wraplength=1100, justify='left', font=('Segoe UI', 11, 'italic'))
        self.news_summary_label.pack(fill='x', padx=10, pady=5)

    def load_news(self):
        news_type = self.news_type_var.get()
        self.news_tree.delete(*self.news_tree.get_children())
        self.news_articles = []
        self.news_summary_label.config(text="")

        def fetch_news():
            try:
                if news_type == "PC News":
                    query = "pc gaming"
                else:
                    query = news_type.lower()
                query_encoded = urllib.parse.quote_plus(query + " game")
                rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=en-US&gl=US&ceid=US:en"
                feed = feedparser.parse(rss_url)
                articles = []
                for entry in feed.entries[:30]:
                    title = entry.title
                    source = getattr(entry, "source", None)
                    if source and hasattr(source, "title"):
                        source_title = source.title
                    else:
                        source_title = "Google News"
                    link = entry.link
                    summary = getattr(entry, "summary", "")
                    articles.append({"title": title, "source": source_title, "link": link, "summary": summary})
                self.root.after(0, lambda: self.display_news(articles))
            except Exception as e:
                self.root.after(0, lambda e=e: messagebox.showerror("Error", f"Failed to load news: {e}"))

        threading.Thread(target=fetch_news, daemon=True).start()

    def display_news(self, articles):
        self.news_articles = articles
        self.news_tree.delete(*self.news_tree.get_children())
        for art in articles:
            self.news_tree.insert('', 'end', values=(art["title"], art["source"], art["summary"][:180] + ("..." if len(art["summary"]) > 180 else "")))

    def show_news_summary(self, event):
        item = self.news_tree.selection()
        if item:
            index = self.news_tree.index(item[0])
            article = self.news_articles[index]
            summary = article.get("summary", "")
            self.news_summary_label.config(text=summary)
        else:
            self.news_summary_label.config(text="")

    def open_selected_news(self, event):
        item = self.news_tree.selection()
        if item:
            index = self.news_tree.index(item[0])
            article = self.news_articles[index]
            link = article.get("link")
            if link:
                webbrowser.open(link)

    def auto_refresh(self):
        self.load_free_giveaways()
        self.load_game_deals()
        self.load_news()
        self.root.after(5 * 60 * 1000, self.auto_refresh)  # Refresh every 5 minutes

def write_thankyou_html():
    with open("thankyou.html", "w", encoding="utf-8") as f:
        f.write(THANKYOU_HTML)

if __name__ == "__main__":
    write_thankyou_html()
    root = tk.Tk()
    app = GameDealsApp(root)
    root.mainloop()
    webbrowser.open("thankyou.html")

