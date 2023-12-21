import asyncio
import aiohttp
from bs4 import BeautifulSoup as BS
from fake_useragent import UserAgent
import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from nltk.sentiment import SentimentIntensityAnalyzer

# Устанавливаем базовый URL для поиска ресторанов
BASE_URL = "https://www.restoclub.ru/msk/search/bar-moskvy"
# Устанавливаем заголовки для HTTP-запросов
HEADERS = {"User-Agent": UserAgent().random}

# Определяем основной класс приложения, унаследованный от tkinter.Tk
class BarSentimentAnalyzer(tk.Tk):
    # Конструктор для инициализации приложения
    def __init__(self):
        super().__init__()
        self.title("Bar Sentiment Analyzer")  # Устанавливаем заголовок окна
        self.geometry("800x600")  # Устанавливаем размер окна
        self.configure(bg='#F0F0F0')  # Устанавливаем цвет фона

        # Создаем горизонтальный разделитель
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=5)

        # Создаем фрейм для вывода результатов
        self.output_frame = tk.Frame(self, bg='#F0F0F0')
        self.output_frame.pack(padx=10, pady=10)

        # Создаем виджет прокручиваемого текста для вывода результатов
        self.output_text = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, width=80, height=20, bg='#FFFFFF')
        self.output_text.pack(padx=10, pady=10)

        # Создаем кнопку для запуска анализа
        self.start_button = tk.Button(self.output_frame, text="Начать анализ", command=self.run_analysis, bg='#3498db', fg='#FFFFFF', font=('Arial', 14), relief=tk.GROOVE, bd=0)
        self.start_button.pack(pady=10)

    # Асинхронный метод для получения HTML-контента по заданному URL с использованием aiohttp
    async def fetch(self, url, session):
        async with session.get(url, headers=HEADERS) as response:
            return await response.text()

    # Асинхронный метод для парсинга отзывов по заданному URL
    async def parse_reviews(self, url, session, sentiments, bar_sentiments):
        html = await self.fetch(url, session)
        soup = BS(html, "html.parser")

        reviews = soup.find_all("div", {"class": "review__text"})
        sid = SentimentIntensityAnalyzer()

        for comment_elem in reviews:
            comment = comment_elem.text.strip()

            # Используем VADER из NLTK для анализа настроений
            sentiment = sid.polarity_scores(comment)['compound']

            output = f"Отзыв: {comment} | Настроение: {sentiment}\n"
            self.output_text.insert(tk.END, output)

            sentiments.append(sentiment)
            bar_sentiments.append({"url": url, "sentiment": sentiment})

    # Асинхронный метод для парсинга страницы с барами
    async def parse_page(self, url, session, sentiments, bar_sentiments):
        html = await self.fetch(url, session)
        soup = BS(html, "html.parser")

        items = soup.find_all("li", {"class": "page-search__item _premium"})
        for item in items:
            title = item.find("div", {"class": "search-place-card__title"})
            place_about = item.find("div", {"class": "search-place-card__about"}).text.strip()
            location = item.find("li", {"class": "search-place-card__info-item"}).text.strip()
            url_more = item.select_one('a').get('href')
            full_url = f"https://www.restoclub.ru{url_more}"

            output = f"Название: {title.text.strip()} | {place_about} | {location} | {full_url}\n"
            self.output_text.insert(tk.END, output)

            await self.parse_reviews(full_url, session, sentiments, bar_sentiments)

    # Асинхронный метод для выполнения основной логики приложения
    async def main(self):
        sentiments = []  # Список для хранения настроений отзывов
        bar_sentiments = []  # Список для хранения настроений по барам

        async with aiohttp.ClientSession() as session:
            await self.parse_page(BASE_URL, session, sentiments, bar_sentiments)

        sorted_bars = sorted(bar_sentiments, key=lambda x: x["sentiment"], reverse=True)

        results_frame = tk.Frame(self.output_frame, bg='#F0F0F0')
        results_frame.pack(pady=10)

        output_top_bars = "\nТоп 3 бара с положительными эмоциями:\n\n"
        for i, bar in enumerate(sorted_bars[:3]):
            output_top_bars += f"{i + 1}. URL: {bar['url']} | Настроение: {bar['sentiment']}\n"

        top_bars_label = tk.Label(results_frame, text=output_top_bars, bg='#F0F0F0', font=('Arial', 12))
        top_bars_label.pack()

        # Создание круговой диаграммы
        labels = [
            f'Положительное\n{sum(1 for sentiment in sentiments if sentiment > 0) / len(sentiments) * 100:.1f}%',
            f'Нейтральное\n{sum(1 for sentiment in sentiments if sentiment == 0) / len(sentiments) * 100:.1f}%',
            f'Негативное\n{sum(1 for sentiment in sentiments if sentiment < 0) / len(sentiments) * 100:.1f}%'
        ]

        counts = [sum(1 for sentiment in sentiments if sentiment > 0),
                  sum(1 for sentiment in sentiments if sentiment == 0),
                  sum(1 for sentiment in sentiments if sentiment < 0)]

        plt.pie(counts, labels=labels, autopct='', startangle=90, colors=['green', 'orange', 'red'])
        plt.axis('equal')  # Сохраняем соотношение сторон для отображения круга.
        plt.title('Распределение настроений', pad=20)
        plt.show()

    # Метод для запуска анализа приложения
    def run_analysis(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main())

# Запуск приложения, если файл запускается напрямую
if __name__ == '__main__':
    app = BarSentimentAnalyzer()
    app.mainloop()
