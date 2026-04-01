import sys
import os
import time
import argparse

# Add parent directory to path to import connector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.connector import PostgreSQLConnector

# List of countries with translations
# Format: [name_en, name_uz, name_ru]
countries = [
    ["Afghanistan", "Afg'oniston", "Афганистан"],
    ["Albania", "Albaniya", "Албания"],
    ["Algeria", "Jazoir", "Алжир"],
    ["Andorra", "Andorra", "Андорра"],
    ["Angola", "Angola", "Ангола"],
    ["Argentina", "Argentina", "Аргентина"],
    ["Armenia", "Armaniston", "Армения"],
    ["Australia", "Avstraliya", "Австралия"],
    ["Austria", "Avstriya", "Австрия"],
    ["Azerbaijan", "Ozarbayjon", "Азербайджан"],
    ["Bahamas", "Bagama orollari", "Багамские острова"],
    ["Bahrain", "Bahrayn", "Бахрейн"],
    ["Bangladesh", "Bangladesh", "Бангладеш"],
    ["Barbados", "Barbados", "Барбадос"],
    ["Belarus", "Belarus", "Беларусь"],
    ["Belgium", "Belgiya", "Бельгия"],
    ["Belize", "Beliz", "Белиз"],
    ["Benin", "Benin", "Бенин"],
    ["Bhutan", "Butan", "Бутан"],
    ["Bolivia", "Boliviya", "Боливия"],
    ["Bosnia and Herzegovina", "Bosniya va Gertsegovina", "Босния и Герцеговина"],
    ["Botswana", "Botsvana", "Ботсвана"],
    ["Brazil", "Braziliya", "Бразилия"],
    ["Brunei", "Bruney", "Бруней"],
    ["Bulgaria", "Bolgariya", "Болгария"],
    ["Burkina Faso", "Burkina-Faso", "Буркина-Фасо"],
    ["Burundi", "Burundi", "Бурунди"],
    ["Cambodia", "Kambodja", "Камбоджа"],
    ["Cameroon", "Kamerun", "Камерун"],
    ["Canada", "Kanada", "Канада"],
    ["Cape Verde", "Kabo-Verde", "Кабо-Верде"],
    ["Central African Republic", "Markaziy Afrika Respublikasi", "Центральноафриканская Республика"],
    ["Chad", "Chad", "Чад"],
    ["Chile", "Chili", "Чили"],
    ["China", "Xitoy", "Китай"],
    ["Colombia", "Kolumbiya", "Колумбия"],
    ["Comoros", "Komor orollari", "Коморские острова"],
    ["Congo", "Kongo", "Конго"],
    ["Costa Rica", "Kosta-Rika", "Коста-Рика"],
    ["Croatia", "Xorvatiya", "Хорватия"],
    ["Cuba", "Kuba", "Куба"],
    ["Cyprus", "Kipr", "Кипр"],
    ["Czech Republic", "Chexiya", "Чехия"],
    ["Denmark", "Daniya", "Дания"],
    ["Djibouti", "Jibuti", "Джибути"],
    ["Dominica", "Dominika", "Доминика"],
    ["Dominican Republic", "Dominikan Respublikasi", "Доминиканская Республика"],
    ["East Timor", "Sharqiy Timor", "Восточный Тимор"],
    ["Ecuador", "Ekvador", "Эквадор"],
    ["Egypt", "Misr", "Египет"],
    ["El Salvador", "El-Salvador", "Сальвадор"],
    ["Equatorial Guinea", "Ekvatorial Gvineya", "Экваториальная Гвинея"],
    ["Eritrea", "Eritreya", "Эритрея"],
    ["Estonia", "Estoniya", "Эстония"],
    ["Eswatini", "Esvatini", "Эсватини"],
    ["Ethiopia", "Efiopiya", "Эфиопия"],
    ["Fiji", "Fiji", "Фиджи"],
    ["Finland", "Finlandiya", "Финляндия"],
    ["France", "Fransiya", "Франция"],
    ["Gabon", "Gabon", "Габон"],
    ["Gambia", "Gambiya", "Гамбия"],
    ["Georgia", "Gruziya", "Грузия"],
    ["Germany", "Germaniya", "Германия"],
    ["Ghana", "Gana", "Гана"],
    ["Greece", "Gretsiya", "Греция"],
    ["Grenada", "Grenada", "Гренада"],
    ["Guatemala", "Gvatemala", "Гватемала"],
    ["Guinea", "Gvineya", "Гвинея"],
    ["Guinea-Bissau", "Gvineya-Bisau", "Гвинея-Бисау"],
    ["Guyana", "Gayana", "Гайана"],
    ["Haiti", "Gaiti", "Гаити"],
    ["Honduras", "Gonduras", "Гондурас"],
    ["Hungary", "Vengriya", "Венгрия"],
    ["Iceland", "Islandiya", "Исландия"],
    ["India", "Hindiston", "Индия"],
    ["Indonesia", "Indoneziya", "Индонезия"],
    ["Iran", "Eron", "Иран"],
    ["Iraq", "Iroq", "Ирак"],
    ["Ireland", "Irlandiya", "Ирландия"],
    ["Israel", "Isroil", "Израиль"],
    ["Italy", "Italiya", "Италия"],
    ["Jamaica", "Yamayka", "Ямайка"],
    ["Japan", "Yaponiya", "Япония"],
    ["Jordan", "Iordaniya", "Иордания"],
    ["Kazakhstan", "Qozog'iston", "Казахстан"],
    ["Kenya", "Keniya", "Кения"],
    ["Kiribati", "Kiribati", "Кирибати"],
    ["Kuwait", "Quvayt", "Кувейт"],
    ["Kyrgyzstan", "Qirg'iziston", "Киргизия"],
    ["Laos", "Laos", "Лаос"],
    ["Latvia", "Latviya", "Латвия"],
    ["Lebanon", "Livan", "Ливан"],
    ["Lesotho", "Lesoto", "Лесото"],
    ["Liberia", "Liberiya", "Либерия"],
    ["Libya", "Liviya", "Ливия"],
    ["Liechtenstein", "Lixtenshteyn", "Лихтенштейн"],
    ["Lithuania", "Litva", "Литва"],
    ["Luxembourg", "Lyuksemburg", "Люксембург"],
    ["Madagascar", "Madagaskar", "Мадагаскар"],
    ["Malawi", "Malavi", "Малави"],
    ["Malaysia", "Malayziya", "Малайзия"],
    ["Maldives", "Maldiv orollari", "Мальдивы"],
    ["Mali", "Mali", "Мали"],
    ["Malta", "Malta", "Мальта"],
    ["Marshall Islands", "Marshall orollari", "Маршалловы острова"],
    ["Mauritania", "Mavritaniya", "Мавритания"],
    ["Mauritius", "Mavrikiy", "Маврикий"],
    ["Mexico", "Meksika", "Мексика"],
    ["Micronesia", "Mikroneziya", "Микронезия"],
    ["Moldova", "Moldova", "Молдова"],
    ["Monaco", "Monako", "Монако"],
    ["Mongolia", "Mo'g'uliston", "Монголия"],
    ["Montenegro", "Chernogoriya", "Черногория"],
    ["Morocco", "Marokash", "Марокко"],
    ["Mozambique", "Mozambik", "Мозамбик"],
    ["Myanmar", "Myanma", "Мьянма"],
    ["Namibia", "Namibiya", "Намибия"],
    ["Nauru", "Nauru", "Науру"],
    ["Nepal", "Nepal", "Непал"],
    ["Netherlands", "Niderlandiya", "Нидерланды"],
    ["New Zealand", "Yangi Zelandiya", "Новая Зеландия"],
    ["Nicaragua", "Nikaragua", "Никарагуа"],
    ["Niger", "Niger", "Нигер"],
    ["Nigeria", "Nigeriya", "Нигерия"],
    ["North Korea", "Shimoliy Koreya", "Северная Корея"],
    ["North Macedonia", "Shimoliy Makedoniya", "Северная Македония"],
    ["Norway", "Norvegiya", "Норвегия"],
    ["Oman", "Ummon", "Оман"],
    ["Pakistan", "Pokiston", "Пакистан"],
    ["Palau", "Palau", "Палау"],
    ["Palestine", "Falastin", "Палестина"],
    ["Panama", "Panama", "Панама"],
    ["Papua New Guinea", "Papua-Yangi Gvineya", "Папуа-Новая Гвинея"],
    ["Paraguay", "Paragvay", "Парагвай"],
    ["Peru", "Peru", "Перу"],
    ["Philippines", "Filippin", "Филиппины"],
    ["Poland", "Polsha", "Польша"],
    ["Portugal", "Portugaliya", "Португалия"],
    ["Qatar", "Qatar", "Катар"],
    ["Romania", "Ruminiya", "Румыния"],
    ["Russia", "Rossiya", "Россия"],
    ["Rwanda", "Ruanda", "Руанда"],
    ["Saint Kitts and Nevis", "Sent-Kits va Nevis", "Сент-Китс и Невис"],
    ["Saint Lucia", "Sent-Lyusiya", "Сент-Люсия"],
    ["Saint Vincent and the Grenadines", "Sent-Vinsent va Grenadinlar", "Сент-Винсент и Гренадины"],
    ["Samoa", "Samoa", "Самоа"],
    ["San Marino", "San-Marino", "Сан-Марино"],
    ["Sao Tome and Principe", "San-Tome va Prinsipi", "Сан-Томе и Принсипи"],
    ["Saudi Arabia", "Saudiya Arabistoni", "Саудовская Аравия"],
    ["Senegal", "Senegal", "Сенегал"],
    ["Serbia", "Serbiya", "Сербия"],
    ["Seychelles", "Seyshel orollari", "Сейшельские острова"],
    ["Sierra Leone", "Syerra-Leone", "Сьерра-Леоне"],
    ["Singapore", "Singapur", "Сингапур"],
    ["Slovakia", "Slovakiya", "Словакия"],
    ["Slovenia", "Sloveniya", "Словения"],
    ["Solomon Islands", "Solomon orollari", "Соломоновы острова"],
    ["Somalia", "Somali", "Сомали"],
    ["South Africa", "Janubiy Afrika", "ЮАР"],
    ["South Korea", "Janubiy Koreya", "Южная Корея"],
    ["South Sudan", "Janubiy Sudan", "Южный Судан"],
    ["Spain", "Ispaniya", "Испания"],
    ["Sri Lanka", "Shri-Lanka", "Шри-Ланка"],
    ["Sudan", "Sudan", "Судан"],
    ["Suriname", "Surinam", "Суринам"],
    ["Sweden", "Shvetsiya", "Швеция"],
    ["Switzerland", "Shveytsariya", "Швейцария"],
    ["Syria", "Suriya", "Сирия"],
    ["Taiwan", "Tayvan", "Тайвань"],
    ["Tajikistan", "Tojikiston", "Таджикистан"],
    ["Tanzania", "Tanzaniya", "Танзания"],
    ["Thailand", "Tailand", "Таиланд"],
    ["Togo", "Togo", "Того"],
    ["Tonga", "Tonga", "Тонга"],
    ["Trinidad and Tobago", "Trinidad va Tobago", "Тринидад и Тобаго"],
    ["Tunisia", "Tunis", "Тунис"],
    ["Turkey", "Turkiya", "Турция"],
    ["Turkmenistan", "Turkmaniston", "Туркменистан"],
    ["Tuvalu", "Tuvalu", "Тувалу"],
    ["Uganda", "Uganda", "Уганда"],
    ["Ukraine", "Ukraina", "Украина"],
    ["United Arab Emirates", "BAA", "ОАЭ"],
    ["United Kingdom", "Buyuk Britaniya", "Великобритания"],
    ["United States", "AQSh", "США"],
    ["Uruguay", "Urugvay", "Уругвай"],
    ["Uzbekistan", "O'zbekiston", "Узбекистан"],
    ["Vanuatu", "Vanuatu", "Вануату"],
    ["Vatican City", "Vatikan", "Ватикан"],
    ["Venezuela", "Venesuela", "Венесуэла"],
    ["Vietnam", "Vetnam", "Вьетнам"],
    ["Yemen", "Yaman", "Йемен"],
    ["Zambia", "Zambiya", "Замбия"],
    ["Zimbabwe", "Zimbabve", "Зимбабве"]
]


def _build_connector():
    return PostgreSQLConnector(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', '5432')),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '1'),
        database=os.getenv('DB_NAME', 'journal2'),
    )


def seed_countries(dbc, replace=False):
    existing_count = dbc.fix_country.count().exec() or 0
    if existing_count > 0 and not replace:
        print(f"fix_country already has {existing_count} rows. Skipping country seed.")
        return existing_count

    if replace and existing_count > 0:
        print("Clearing existing countries...")
        dbc.fix_country.delete().exec()

    print("Adding countries...")
    now_ts = int(time.time())
    for country in countries:
        dbc.fix_country.add(
            name=country[0],      # English name
            name_uz=country[1],   # Uzbek name
            name_ru=country[2],   # Russian name
            created_at=now_ts
        ).exec()

    count = dbc.fix_country.count().exec()
    print(f"Countries seed complete. Total rows: {count}")
    return count


def _parse_args():
    parser = argparse.ArgumentParser(description='Seed fix_country table')
    parser.add_argument(
        '--replace',
        action='store_true',
        help='Delete existing rows and reseed from scratch',
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    dbc = _build_connector()
    try:
        seed_countries(dbc, replace=args.replace)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
