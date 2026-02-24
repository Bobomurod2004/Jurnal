import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector
from config import *

dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

# Test news items
news_data = [
    {
        'type': 'news',
        'title': 'New Research on Linguistic Markers in Story Recall',
        'title_ru': 'Новое исследование лингвистических маркеров в воспроизведении историй',
        'title_uz': 'Hikoya eslashda lingvistik belgilar bo\'yicha yangi tadqiqot',
        'content': 'Recent studies have shown significant correlations between linguistic markers and memory recall patterns in narrative comprehension.',
        'content_ru': 'Недавние исследования показали значительные корреляции между лингвистическими маркерами и паттернами воспроизведения памяти при понимании нарратива.',
        'content_uz': 'So\'nggi tadqiqotlar narrativni tushunishda lingvistik belgilar va xotira qayta tiklash naqshlari o\'rtasida muhim korrelyatsiyalarni ko\'rsatdi.',
        'status': 'published',
        'created_at': int(time.time()),
        'published_at': int(time.time()) - 86400,  # 1 day ago
        'author_id': 1
    },
    {
        'type': 'news',
        'title': 'Digital Humanities Conference 2024 Highlights',
        'title_ru': 'Основные моменты конференции по цифровой гуманитаристике 2024',
        'title_uz': 'Raqamli gumanitar fanlar konferentsiyasi 2024 asosiy lahzalari',
        'content': 'The annual Digital Humanities Conference showcased groundbreaking research in computational linguistics and text analysis.',
        'content_ru': 'Ежегодная конференция по цифровой гуманитаристике продемонстрировала прорывные исследования в области компьютерной лингвистики и анализа текста.',
        'content_uz': 'Yillik raqamli gumanitar fanlar konferentsiyasi kompyuter lingvistikasi va matn tahlili sohasidagi ilg\'or tadqiqotlarni namoyish etdi.',
        'status': 'published',
        'created_at': int(time.time()),
        'published_at': int(time.time()) - 172800,  # 2 days ago
        'author_id': 1
    },
    {
        'type': 'news',
        'title': 'Journal Impact Factor Update',
        'title_ru': 'Обновление импакт-фактора журнала',
        'title_uz': 'Jurnal ta\'sir omili yangilanishi',
        'content': 'We are pleased to announce that our journal\'s impact factor has increased significantly this year.',
        'content_ru': 'Мы рады сообщить, что импакт-фактор нашего журнала значительно вырос в этом году.',
        'content_uz': 'Bizning jurnalimizning ta\'sir omili bu yil sezilarli darajada oshganini e\'lon qilishdan mamnunmiz.',
        'status': 'published',
        'created_at': int(time.time()),
        'published_at': int(time.time()) - 259200,  # 3 days ago
        'author_id': 1
    }
]

# Test announcements
announcements_data = [
    {
        'type': 'announcement',
        'title': 'Call for Papers: Special Issue on Computational Linguistics',
        'title_ru': 'Приглашение к публикации: Специальный выпуск по компьютерной лингвистике',
        'title_uz': 'Maqolalar uchun chaqiruv: Kompyuter lingvistikasi bo\'yicha maxsus son',
        'content': 'We invite submissions for our upcoming special issue focusing on recent advances in computational linguistics and natural language processing.',
        'content_ru': 'Мы приглашаем к подаче статей для нашего предстоящего специального выпуска, посвященного последним достижениям в области компьютерной лингвистики и обработки естественного языка.',
        'content_uz': 'Kompyuter lingvistikasi va tabiiy tilni qayta ishlashdagi so\'nggi yutuqlarga bag\'ishlangan maxsus sonimiz uchun maqolalar taqdim etishga taklif qilamiz.',
        'status': 'published',
        'created_at': int(time.time()),
        'published_at': int(time.time()) - 86400,  # 1 day ago
        'author_id': 1
    },
    {
        'type': 'announcement',
        'title': 'Extended Deadline: Manuscript Submissions',
        'title_ru': 'Продленный срок: Подача рукописей',
        'title_uz': 'Uzaytirilgan muddat: Qo\'lyozma taqdim etish',
        'content': 'Due to high interest, we have extended the submission deadline for our current issue to the end of this month.',
        'content_ru': 'В связи с большим интересом мы продлили срок подачи статей для текущего выпуска до конца этого месяца.',
        'content_uz': 'Katta qiziqish tufayli joriy son uchun maqola taqdim etish muddatini shu oy oxirigacha uzaytirdik.',
        'status': 'published',
        'created_at': int(time.time()),
        'published_at': int(time.time()) - 172800,  # 2 days ago
        'author_id': 1
    },
    {
        'type': 'announcement',
        'title': 'New Editorial Board Members',
        'title_ru': 'Новые члены редакционной коллегии',
        'title_uz': 'Tahririyat hay\'atining yangi a\'zolari',
        'content': 'We are excited to welcome three distinguished scholars to our editorial board, bringing expertise in sociolinguistics and discourse analysis.',
        'content_ru': 'Мы рады приветствовать трех выдающихся ученых в нашей редакционной коллегии, которые привносят экспертизу в области социолингвистики и дискурс-анализа.',
        'content_uz': 'Sotsiolingvistika va diskurs tahlili sohasida tajribaga ega bo\'lgan uchta taniqli olimni tahririyat hay\'atimizga qabul qilishdan xursandmiz.',
        'status': 'published',
        'created_at': int(time.time()),
        'published_at': int(time.time()) - 259200,  # 3 days ago
        'author_id': 1
    }
]

# Add news items
print("Adding test news items...")
for news in news_data:
    try:
        dbc.news.add(**news).exec()
        print(f"Added news: {news['title']}")
    except Exception as e:
        print(f"Error adding news '{news['title']}': {e}")

# Add announcements
print("\nAdding test announcements...")
for announcement in announcements_data:
    try:
        dbc.news.add(**announcement).exec()
        print(f"Added announcement: {announcement['title']}")
    except Exception as e:
        print(f"Error adding announcement '{announcement['title']}': {e}")

print("\nTest news and announcements added successfully!") 