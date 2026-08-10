import webbrowser

sites = {
    "yt": "https://www.youtube.com",
    "ig": "https://www.instagram.com",
}

def open_site(name):
    name = name.lower().strip()

    if name in sites:
        url = sites[name]
    else:
        url = f"https://{name}.com"

    webbrowser.open(url)
    print(f"Opening {url}")

