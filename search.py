import webbrowser
import urllib.parse

def google_search(query):
    if not query:
        print("No search query provided.")
        return
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    
    webbrowser.open(url)
    print(f"ARC: Searching Google for: {query}")