import sys
import os
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector

PAGES_DATA = {
    'submission_guidelines': {
        'title': 'Submission Guidelines',
        'title_uz': 'Maqola yuborish bo\'yicha ko\'rsatmalar',
        'title_ru': 'Руководство по подаче статей',
        'content': '''
        <h4 class="text-lg font-medium mb-4">General Guidelines</h4>
        <p class="mb-4">Please read these guidelines carefully before submitting your manuscript...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Umumiy ko'rsatmalar</h4>
        <p class="mb-4">Iltimos, qo'lyozmangizni yuborishdan oldin ushbu ko'rsatmalarni diqqat bilan o'qib chiqing...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Общие указания</h4>
        <p class="mb-4">Пожалуйста, внимательно прочтите эти указания перед отправкой рукописи...</p>
        '''
    },
    'author_instructions': {
        'title': 'Instructions for Authors',
        'title_uz': 'Mualliflar uchun ko\'rsatmalar',
        'title_ru': 'Инструкции для авторов',
        'content': '''
        <h4 class="text-lg font-medium mb-4">Manuscript Preparation</h4>
        <p class="mb-4">Follow these instructions to prepare your manuscript...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Qo'lyozmani tayyorlash</h4>
        <p class="mb-4">Qo'lyozmangizni tayyorlash uchun ushbu ko'rsatmalarga amal qiling...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Подготовка рукописи</h4>
        <p class="mb-4">Следуйте этим инструкциям для подготовки вашей рукописи...</p>
        '''
    },
    'editorial_policy': {
        'title': 'Editorial Policy',
        'title_uz': 'Tahririyat siyosati',
        'title_ru': 'Редакционная политика',
        'content': '''
        <h4 class="text-lg font-medium mb-4">Publication Ethics</h4>
        <p class="mb-4">Our journal follows strict ethical guidelines...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Nashr etish etikasi</h4>
        <p class="mb-4">Bizning jurnal qat'iy etik ko'rsatmalarga amal qiladi...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Публикационная этика</h4>
        <p class="mb-4">Наш журнал следует строгим этическим принципам...</p>
        '''
    },
    'site_editing_services': {
        'title': 'Site Editing Services',
        'title_uz': 'Sayt tahrirlash xizmatlari',
        'title_ru': 'Услуги редактирования сайта',
        'content': '''
        <h4 class="text-lg font-medium mb-4">Our Editing Services</h4>
        <p class="mb-4">We offer professional editing services...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Bizning tahrirlash xizmatlarimiz</h4>
        <p class="mb-4">Biz professional tahrirlash xizmatlarini taqdim etamiz...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Наши услуги редактирования</h4>
        <p class="mb-4">Мы предлагаем профессиональные услуги редактирования...</p>
        '''
    },
    'journal_metrics': {
        'title': 'Journal Metrics',
        'title_uz': 'Jurnal ko\'rsatkichlari',
        'title_ru': 'Показатели журнала',
        'content': '''
        <h4 class="text-lg font-medium mb-4">Impact and Metrics</h4>
        <p class="mb-4">View our journal's performance metrics...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Ta'sir va ko'rsatkichlar</h4>
        <p class="mb-4">Jurnalimizning samaradorlik ko'rsatkichlarini ko'ring...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Влияние и показатели</h4>
        <p class="mb-4">Просмотрите показатели эффективности нашего журнала...</p>
        '''
    },
    'aims_scope': {
        'title': 'Aims and Scope',
        'title_uz': 'Maqsad va vazifalar',
        'title_ru': 'Цели и задачи',
        'content': '''
        <h4 class="text-lg font-medium mb-4">Journal Focus</h4>
        <p class="mb-4">Our journal focuses on advancing knowledge in...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Jurnal yo'nalishi</h4>
        <p class="mb-4">Bizning jurnal bilimlarni rivojlantirishga qaratilgan...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Направление журнала</h4>
        <p class="mb-4">Наш журнал направлен на развитие знаний в области...</p>
        '''
    },
    'journal_info': {
        'title': 'Journal Information',
        'title_uz': 'Jurnal haqida ma\'lumot',
        'title_ru': 'Информация о журнале',
        'content': '''
        <h4 class="text-lg font-medium mb-4">About Our Journal</h4>
        <p class="mb-4">Learn more about our journal's history and mission...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Bizning jurnal haqida</h4>
        <p class="mb-4">Jurnalimizning tarixi va vazifasi haqida ko'proq bilib oling...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">О нашем журнале</h4>
        <p class="mb-4">Узнайте больше об истории и миссии нашего журнала...</p>
        '''
    },
    'news_calls': {
        'title': 'News and Calls for Papers',
        'title_uz': 'Yangiliklar va maqolalar uchun chaqiruvlar',
        'title_ru': 'Новости и приглашения к публикации',
        'content': '''
        <h4 class="text-lg font-medium mb-4">Latest Updates</h4>
        <p class="mb-4">Stay informed about our latest news and opportunities...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">So'nggi yangilanishlar</h4>
        <p class="mb-4">Bizning so'nggi yangiliklar va imkoniyatlardan xabardor bo'ling...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Последние обновления</h4>
        <p class="mb-4">Будьте в курсе наших последних новостей и возможностей...</p>
        '''
    },
    'conferences': {
        'title': 'Conferences',
        'title_uz': 'Konferentsiyalar',
        'title_ru': 'Конференции',
        'content': '''
        <h4 class="text-lg font-medium mb-4">Upcoming Events</h4>
        <p class="mb-4">Find information about upcoming conferences and events...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Kelgusi tadbirlar</h4>
        <p class="mb-4">Kelgusi konferentsiyalar va tadbirlar haqida ma'lumot oling...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Предстоящие события</h4>
        <p class="mb-4">Найдите информацию о предстоящих конференциях и мероприятиях...</p>
        '''
    },
    'for_uzgumya_researchers': {
        'title': 'For UzGUMYA Researchers',
        'title_uz': 'UzDJTU tadqiqotchilari uchun',
        'title_ru': 'Для исследователей УзГУМЯ',
        'content': '''
        <h4 class="text-lg font-medium mb-4">Special Access</h4>
        <p class="mb-4">Information for UzGUMYA affiliated researchers...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Maxsus kirish</h4>
        <p class="mb-4">UzDJTU bilan bog'liq tadqiqotchilar uchun ma'lumot...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Специальный доступ</h4>
        <p class="mb-4">Информация для исследователей, связанных с УзГУМЯ...</p>
        '''
    },
    'for_all_researchers': {
        'title': 'For All Researchers',
        'title_uz': 'Barcha tadqiqotchilar uchun',
        'title_ru': 'Для всех исследователей',
        'content': '''
        <h4 class="text-lg font-medium mb-4">General Access</h4>
        <p class="mb-4">Information for all researchers...</p>
        ''',
        'content_uz': '''
        <h4 class="text-lg font-medium mb-4">Umumiy kirish</h4>
        <p class="mb-4">Barcha tadqiqotchilar uchun ma'lumot...</p>
        ''',
        'content_ru': '''
        <h4 class="text-lg font-medium mb-4">Общий доступ</h4>
        <p class="mb-4">Информация для всех исследователей...</p>
        '''
    }
}

def update_pages():
    # Initialize database connection
    dbc = PostgreSQLConnector(host='127.0.0.1', port=5432, user='postgres', password='1', database='journal')
    
    current_time = int(time.time())
    
    # Get all existing pages
    existing_pages = dbc.pages.get().exec()
    existing_aliases = {page['alias']: page for page in existing_pages} if existing_pages else {}
    
    # Update or create each page
    for alias, page_data in PAGES_DATA.items():
        if alias in existing_aliases:
            print(f"Updating page: {page_data['title']}")
            dbc.pages.get(alias=alias).update(
                title=page_data['title'],
                title_uz=page_data['title_uz'],
                title_ru=page_data['title_ru'],
                content=page_data['content'],
                content_uz=page_data['content_uz'],
                content_ru=page_data['content_ru'],
                last_update=current_time
            ).exec()
        else:
            print(f"Creating new page: {page_data['title']}")
            dbc.pages.add(
                alias=alias,
                title=page_data['title'],
                title_uz=page_data['title_uz'],
                title_ru=page_data['title_ru'],
                content=page_data['content'],
                content_uz=page_data['content_uz'],
                content_ru=page_data['content_ru'],
                last_update=current_time,
                created_at=current_time
            ).exec()

    print("All pages updated successfully!")

if __name__ == '__main__':
    update_pages() 