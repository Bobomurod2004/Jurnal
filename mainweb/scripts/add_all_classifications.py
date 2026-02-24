import sys
import os
import time

# Add parent directory to path to import connector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.connector import PostgreSQLConnector

# Initialize database connection
dbc = PostgreSQLConnector(host='127.0.0.1', port=5432, user='postgres', password='1', database='journal')

# List of classifications with translations
# Format: [name_en, name_uz, name_ru]
classifications = [
    ["Literary Source Studies", "Adabiy manbashunoslik", "Литературное источниковедение"],
    ["Literary Theory", "Adabiyot nazariyasi", "Теория литературы"],
    ["Applied and Computational Linguistics", "Amaliy va kompyuter lingvistikasi", "Прикладная и компьютерная лингвистика"],
    ["Psychology of Religion", "Din psixologiyasi", "Психология религии"],
    ["Theory and Methodology of E-learning", "Elektron taʼlim nazariyasi va metodikasi", "Теория и методика электронного обучения"],
    ["Ethnopsychology", "Etnopsixologiya", "Этнопсихология"],
    ["Folklore Studies", "Folklorshunoslik", "Фольклористика"],
    ["Military Journalism", "Harbiy jurnalistika", "Военная журналистика"],
    ["Social Pedagogy", "Ijtimoiy pedagogika", "Социальная педагогика"],
    ["Social Psychology", "Ijtimoiy psixologiya", "Социальная психология"],
    ["Psychology of Human Professional Activity", "Inson kasbiy faoliyati psixologiyasi", "Психология профессиональной деятельности человека"],
    ["Internet Journalism", "Internet jurnalistikasi", "Интернет-журналистика"],
    ["Theory and Methodology of Vocational Education", "Kasb-hunar taʼlimi nazariyasi va metodikasi", "Теория и методика профессионального образования"],
    ["Cognitive Linguistics", "Kognitiv lingvistika", "Когнитивная лингвистика"],
    ["Comparative Studies", "Komparativistika", "Компаративистика"],
    ["Issues of Comparative Studies", "Komparativistika masalalari", "Вопросы компаративистики"],
    ["Theory and Methodology of Preschool Education", "Maktabgacha taʼlim va tarbiya nazariyasi va metodikasi", "Теория и методика дошкольного образования"],
    ["Textual Studies", "Matnshunoslik", "Текстология"],
    ["Special Pedagogy", "Maxsus pedagogika", "Специальная педагогика"],
    ["Neurolinguistics", "Neyrolingvistika", "Нейролингвистика"],
    ["Mass Media Journalism", "Ommaviy axborot vositalari jurnalistikasi", "Журналистика средств массовой информации"],
    ["Literature of Asian and African Peoples", "Osiyo va Afrika xalqlari adabiyoti", "Литература народов Азии и Африки"],
    ["Languages of Asian and African Peoples", "Osiyo va Afrika xalqlari tili", "Языки народов Азии и Африки"],
    ["History of Pedagogical Teachings", "Pedagogik taʼlimotlar tarixi", "История педагогических учений"],
    ["Pedagogical Theory", "Pedagogika nazariyasi", "Педагогическая теория"],
    ["Pragmalinguistics", "Pragmalingvistika", "Прагмалингвистика"],
    ["Psychophysiology", "Psixofiziologiya", "Психофизиология"],
    ["Psycholinguistics", "Psixolingvistika", "Психолингвистика"],
    ["History and Theory of Psychology", "Psixologiya tarixi va nazariyasi", "История и теория психологии"],
    ["Comparative Literature Studies", "Qiyosiy adabiyotshunoslik", "Сравнительное литературоведение"],
    ["Karakalpak Literature", "Qoraqalpoq adabiyoti", "Каракалпакская литература"],
    ["Karakalpak Language", "Qoraqalpoq tili", "Каракалпакский язык"],
    ["Radio Journalism", "Radio jurnalistika", "Радиожурналистика"],
    ["Developmental Psychology", "Rivojlanish psixologiyasi", "Психология развития"],
    ["Art Journalism", "San'at jurnalistikasi", "Арт-журналистика"],
    ["Travel Journalism", "Sayohat jurnalistikasi", "Туристическая журналистика"],
    ["Sociolinguistics", "Sotsiolinvistika", "Социолингвистика"],
    ["Sports Journalism", "Sport jurnalistikasi", "Спортивная журналистика"],
    ["Theory and Methodology of Education", "Taʼlim va tarbiya nazariyasi va metodikasi", "Теория и методика образования"],
    ["Management in Education", "Taʼlimda menejment", "Менеджмент в образовании"],
    ["TV Journalism", "Telejurnalistika", "Тележурналистика"],
    ["Medical and Special Psychology", "Tibbiy va maxsus psixologiya", "Медицинская и специальная психология"],
    ["Language Theory", "Til nazariyasi", "Теория языка"],
    ["General Psychology", "Umumiy psixologiya", "Общая психология"],
    ["Literature of European, American and Australian Peoples", "Yevropa, Amerika va Avstraliya xalqlari adabiyoti", "Литература народов Европы, Америки и Австралии"],
    ["Languages of European, American and Australian Peoples", "Yevropa, Amerika va Avstraliya xalqlari tili", "Языки народов Европы, Америки и Австралии"],
    ["Age and Pedagogical Psychology", "Yosh va pedagogik psixologiya", "Возрастная и педагогическая психология"],
    ["Uzbek Literature", "Oʻzbek adabiyoti", "Узбекская литература"],
    ["Uzbek Language", "Oʻzbek tili", "Узбекский язык"],
    ["Personality Psychology", "Shaxs psixologiyasi", "Психология личности"],
    ["Comparative Translation Studies", "Chogʻishtirma tarjimashunoslik", "Сравнительное переводоведение"],
    ["Comparative Linguistics", "Chogʻishtirma tilshunoslik", "Сравнительное языкознание"]
]

def main():
    try:
        # First, clear existing classifications using table.delete()
        print("Clearing existing classifications...")
        dbc.fix_classifications.delete().exec()
        
        # Add each classification with translations
        print("Adding classifications...")
        for classification in classifications:
            dbc.fix_classifications.add(
                name=classification[0],      # English name
                name_uz=classification[1],   # Uzbek name
                name_ru=classification[2],   # Russian name
            ).exec()
        
        # Verify the count
        count = dbc.fix_classifications.count().exec()
        print(f"Added {count} classifications successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 