class News:
    def __init__(self, title: str, published_date: str, summary: str):
        self.title = title
        self.published_date = published_date
        self.summary = summary
    
    def __str__(self):
        return f"Title: {self.title}\nDate: {self.published_date}\nSummary: {self.summary[:70]}..."