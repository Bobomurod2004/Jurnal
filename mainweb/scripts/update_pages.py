import argparse
import sys
import os
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector
from config import *

PAGES_DATA = {
    'submission_guidelines': {
        'title': 'Submission Guidelines',
        'title_uz': 'Maqola yuborish bo\'yicha ko\'rsatmalar',
        'title_ru': 'Руководство по подаче статей',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yuborishdan oldin</h4>
          <p class="mb-4">Maqola jurnalning mavzu yo'nalishiga mos, original bo'lishi va boshqa nashrlarda ko'rib chiqilmayotgan bo'lishi kerak.</p>
          <p class="mb-0">Mualliflar ro'yxati, hissalar va manfaatlar to'qnashuvi haqida ma'lumot aniq ko'rsatiladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kerakli fayllar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Asosiy qo'lyozma (muallif ma'lumotlari bilan).</li>
            <li>Anonimlashtirilgan versiya (ko'rib chiqish uchun).</li>
            <li>Rasm/jadval va qo'shimcha materiallar.</li>
            <li>Yo'llanma xati (ixtiyoriy, qisqa).</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tuzilishi va format</h4>
          <p class="mb-4">Maqola odatda sarlavha, annotatsiya, kalit so'zlar, kirish, metodologiya, natijalar, muhokama, xulosa va adabiyotlar bo'limlaridan iborat bo'ladi.</p>
          <p class="mb-0">Matn <strong>doc/docx</strong> formatida taqdim etiladi. Jadval va rasmlar raqamlanadi, sarlavha va manba bilan beriladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Etika va mualliflik</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Plagiat va soxta ma'lumotlarga yo'l qo'yilmaydi.</li>
            <li>Mualliflik hissalari adolatli ko'rsatiladi.</li>
            <li>Manbalar to'liq va aniq keltiriladi.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Ko'rib chiqish jarayoni</h4>
          <p class="mb-0">Har bir maqola avval texnik tekshiruvdan o'tadi, so'ngra mutaxassislar tomonidan ilmiy ekspertiza qilinadi. Zaruratga ko'ra tahririy tuzatishlar so'raladi.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yuborishdan oldin</h4>
          <p class="mb-4">Maqola jurnalning mavzu yo'nalishiga mos, original bo'lishi va boshqa nashrlarda ko'rib chiqilmayotgan bo'lishi kerak.</p>
          <p class="mb-0">Mualliflar ro'yxati, hissalar va manfaatlar to'qnashuvi haqida ma'lumot aniq ko'rsatiladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kerakli fayllar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Asosiy qo'lyozma (muallif ma'lumotlari bilan).</li>
            <li>Anonimlashtirilgan versiya (ko'rib chiqish uchun).</li>
            <li>Rasm/jadval va qo'shimcha materiallar.</li>
            <li>Yo'llanma xati (ixtiyoriy, qisqa).</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tuzilishi va format</h4>
          <p class="mb-4">Maqola odatda sarlavha, annotatsiya, kalit so'zlar, kirish, metodologiya, natijalar, muhokama, xulosa va adabiyotlar bo'limlaridan iborat bo'ladi.</p>
          <p class="mb-0">Matn <strong>doc/docx</strong> formatida taqdim etiladi. Jadval va rasmlar raqamlanadi, sarlavha va manba bilan beriladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Etika va mualliflik</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Plagiat va soxta ma'lumotlarga yo'l qo'yilmaydi.</li>
            <li>Mualliflik hissalari adolatli ko'rsatiladi.</li>
            <li>Manbalar to'liq va aniq keltiriladi.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Ko'rib chiqish jarayoni</h4>
          <p class="mb-0">Har bir maqola avval texnik tekshiruvdan o'tadi, so'ngra mutaxassislar tomonidan ilmiy ekspertiza qilinadi. Zaruratga ko'ra tahririy tuzatishlar so'raladi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yuborishdan oldin</h4>
          <p class="mb-4">Maqola jurnalning mavzu yo'nalishiga mos, original bo'lishi va boshqa nashrlarda ko'rib chiqilmayotgan bo'lishi kerak.</p>
          <p class="mb-0">Mualliflar ro'yxati, hissalar va manfaatlar to'qnashuvi haqida ma'lumot aniq ko'rsatiladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kerakli fayllar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Asosiy qo'lyozma (muallif ma'lumotlari bilan).</li>
            <li>Anonimlashtirilgan versiya (ko'rib chiqish uchun).</li>
            <li>Rasm/jadval va qo'shimcha materiallar.</li>
            <li>Yo'llanma xati (ixtiyoriy, qisqa).</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tuzilishi va format</h4>
          <p class="mb-4">Maqola odatda sarlavha, annotatsiya, kalit so'zlar, kirish, metodologiya, natijalar, muhokama, xulosa va adabiyotlar bo'limlaridan iborat bo'ladi.</p>
          <p class="mb-0">Matn <strong>doc/docx</strong> formatida taqdim etiladi. Jadval va rasmlar raqamlanadi, sarlavha va manba bilan beriladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Etika va mualliflik</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Plagiat va soxta ma'lumotlarga yo'l qo'yilmaydi.</li>
            <li>Mualliflik hissalari adolatli ko'rsatiladi.</li>
            <li>Manbalar to'liq va aniq keltiriladi.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Ko'rib chiqish jarayoni</h4>
          <p class="mb-0">Har bir maqola avval texnik tekshiruvdan o'tadi, so'ngra mutaxassislar tomonidan ilmiy ekspertiza qilinadi. Zaruratga ko'ra tahririy tuzatishlar so'raladi.</p>
        </section>
        '''
    },
    'author_instructions': {
        'title': 'Instructions for Authors',
        'title_uz': 'Mualliflar uchun ko\'rsatmalar',
        'title_ru': 'Инструкции для авторов',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Maqola tuzilmasi</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Sarlavha va muallif ma'lumotlari</li>
            <li>Annotatsiya va kalit so'zlar</li>
            <li>Asosiy matn (kirish, metod, natijalar, muhokama, xulosa)</li>
            <li>Adabiyotlar ro'yxati</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Annotatsiya va kalit so'zlar</h4>
          <p class="mb-0">Annotatsiya tadqiqot maqsadi, metodlari va asosiy natijalarni qisqa va lo'nda yoritishi kerak. Kalit so'zlar mavzuni to'g'ri aks ettiradigan, qidiruv uchun qulay bo'lgan so'z birikmalaridan tanlanadi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jadval va rasmlar</h4>
          <p class="mb-0">Har bir jadval va rasm raqamlanadi, sarlavha beriladi va matnda izohlanadi. Tasvirlar sifatli bo'lishi, manba ko'rsatilishi zarur.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Adabiyotlar</h4>
          <p class="mb-0">Adabiyotlar bir xil bibliografik uslubda rasmiylashtiriladi. Mavjud bo'lsa DOI va boshqa identifikatorlar ko'rsatiladi.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Maqola tuzilmasi</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Sarlavha va muallif ma'lumotlari</li>
            <li>Annotatsiya va kalit so'zlar</li>
            <li>Asosiy matn (kirish, metod, natijalar, muhokama, xulosa)</li>
            <li>Adabiyotlar ro'yxati</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Annotatsiya va kalit so'zlar</h4>
          <p class="mb-0">Annotatsiya tadqiqot maqsadi, metodlari va asosiy natijalarni qisqa va lo'nda yoritishi kerak. Kalit so'zlar mavzuni to'g'ri aks ettiradigan, qidiruv uchun qulay bo'lgan so'z birikmalaridan tanlanadi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jadval va rasmlar</h4>
          <p class="mb-0">Har bir jadval va rasm raqamlanadi, sarlavha beriladi va matnda izohlanadi. Tasvirlar sifatli bo'lishi, manba ko'rsatilishi zarur.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Adabiyotlar</h4>
          <p class="mb-0">Adabiyotlar bir xil bibliografik uslubda rasmiylashtiriladi. Mavjud bo'lsa DOI va boshqa identifikatorlar ko'rsatiladi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Maqola tuzilmasi</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Sarlavha va muallif ma'lumotlari</li>
            <li>Annotatsiya va kalit so'zlar</li>
            <li>Asosiy matn (kirish, metod, natijalar, muhokama, xulosa)</li>
            <li>Adabiyotlar ro'yxati</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Annotatsiya va kalit so'zlar</h4>
          <p class="mb-0">Annotatsiya tadqiqot maqsadi, metodlari va asosiy natijalarni qisqa va lo'nda yoritishi kerak. Kalit so'zlar mavzuni to'g'ri aks ettiradigan, qidiruv uchun qulay bo'lgan so'z birikmalaridan tanlanadi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jadval va rasmlar</h4>
          <p class="mb-0">Har bir jadval va rasm raqamlanadi, sarlavha beriladi va matnda izohlanadi. Tasvirlar sifatli bo'lishi, manba ko'rsatilishi zarur.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Adabiyotlar</h4>
          <p class="mb-0">Adabiyotlar bir xil bibliografik uslubda rasmiylashtiriladi. Mavjud bo'lsa DOI va boshqa identifikatorlar ko'rsatiladi.</p>
        </section>
        '''
    },
    'editorial_policy': {
        'title': 'Editorial Policy',
        'title_uz': 'Tahririyat siyosati',
        'title_ru': 'Редакционная политика',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahririyat mustaqilligi</h4>
          <p class="mb-0">Tahririyat qarorlari ilmiy sifat va dolzarblik mezonlariga asoslanadi. Mualliflar va homiylarning institutsional mansubligi yoki shaxsiy fikrlar nashr qaroriga ta'sir qilmaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ilmiy ekspertiza</h4>
          <p class="mb-0">Maqolalar xolis va malakali mutaxassislar tomonidan ko'rib chiqiladi. Zarur hollarda anonim ekspertiza amaliyoti qo'llaniladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Etika va shaffoflik</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Plagiat va ma'lumotlarni soxtalashtirish qat'iyan taqiqlanadi.</li>
            <li>Manfaatlar to'qnashuvi bo'lsa, mualliflar buni ochiq bildiradi.</li>
            <li>Inson ishtirokidagi tadqiqotlarda etik ruxsatlar ko'rsatiladi.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tuzatishlar va qaytarib olish</h4>
          <p class="mb-0">Aniqlangan xatolar bo'yicha tuzatishlar beriladi. Jiddiy qonunbuzarlik holatlarida maqola qaytarib olinishi mumkin.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahririyat mustaqilligi</h4>
          <p class="mb-0">Tahririyat qarorlari ilmiy sifat va dolzarblik mezonlariga asoslanadi. Mualliflar va homiylarning institutsional mansubligi yoki shaxsiy fikrlar nashr qaroriga ta'sir qilmaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ilmiy ekspertiza</h4>
          <p class="mb-0">Maqolalar xolis va malakali mutaxassislar tomonidan ko'rib chiqiladi. Zarur hollarda anonim ekspertiza amaliyoti qo'llaniladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Etika va shaffoflik</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Plagiat va ma'lumotlarni soxtalashtirish qat'iyan taqiqlanadi.</li>
            <li>Manfaatlar to'qnashuvi bo'lsa, mualliflar buni ochiq bildiradi.</li>
            <li>Inson ishtirokidagi tadqiqotlarda etik ruxsatlar ko'rsatiladi.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tuzatishlar va qaytarib olish</h4>
          <p class="mb-0">Aniqlangan xatolar bo'yicha tuzatishlar beriladi. Jiddiy qonunbuzarlik holatlarida maqola qaytarib olinishi mumkin.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahririyat mustaqilligi</h4>
          <p class="mb-0">Tahririyat qarorlari ilmiy sifat va dolzarblik mezonlariga asoslanadi. Mualliflar va homiylarning institutsional mansubligi yoki shaxsiy fikrlar nashr qaroriga ta'sir qilmaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ilmiy ekspertiza</h4>
          <p class="mb-0">Maqolalar xolis va malakali mutaxassislar tomonidan ko'rib chiqiladi. Zarur hollarda anonim ekspertiza amaliyoti qo'llaniladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Etika va shaffoflik</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Plagiat va ma'lumotlarni soxtalashtirish qat'iyan taqiqlanadi.</li>
            <li>Manfaatlar to'qnashuvi bo'lsa, mualliflar buni ochiq bildiradi.</li>
            <li>Inson ishtirokidagi tadqiqotlarda etik ruxsatlar ko'rsatiladi.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tuzatishlar va qaytarib olish</h4>
          <p class="mb-0">Aniqlangan xatolar bo'yicha tuzatishlar beriladi. Jiddiy qonunbuzarlik holatlarida maqola qaytarib olinishi mumkin.</p>
        </section>
        '''
    },
    'site_editing_services': {
        'title': 'Site Editing Services',
        'title_uz': 'Sayt tahrirlash xizmatlari',
        'title_ru': 'Услуги редактирования сайта',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahrirlash xizmatlari</h4>
          <p class="mb-0">Mualliflar uchun til va uslubiy tahrir, formatlash va bibliografik tekshiruv xizmatlari taklif etiladi. Xizmatlar ixtiyoriy bo'lib, maqolaning nashrga qabul qilinishini kafolatlamaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Xizmat turlari</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Imlo va uslubiy tahrir (til sifati)</li>
            <li>Formatlash va dizayn talablariga moslashtirish</li>
            <li>Jadval va rasm yozuvlarini standartlashtirish</li>
            <li>Adabiyotlar ro'yxatini tekshirish</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Qanday foydalaniladi</h4>
          <p class="mb-0">Tahrirlash xizmati talab qilinganda, tahririyat ish hajmi va muddatini baholab, alohida tartibda ma'lumot beradi.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahrirlash xizmatlari</h4>
          <p class="mb-0">Mualliflar uchun til va uslubiy tahrir, formatlash va bibliografik tekshiruv xizmatlari taklif etiladi. Xizmatlar ixtiyoriy bo'lib, maqolaning nashrga qabul qilinishini kafolatlamaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Xizmat turlari</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Imlo va uslubiy tahrir (til sifati)</li>
            <li>Formatlash va dizayn talablariga moslashtirish</li>
            <li>Jadval va rasm yozuvlarini standartlashtirish</li>
            <li>Adabiyotlar ro'yxatini tekshirish</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Qanday foydalaniladi</h4>
          <p class="mb-0">Tahrirlash xizmati talab qilinganda, tahririyat ish hajmi va muddatini baholab, alohida tartibda ma'lumot beradi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahrirlash xizmatlari</h4>
          <p class="mb-0">Mualliflar uchun til va uslubiy tahrir, formatlash va bibliografik tekshiruv xizmatlari taklif etiladi. Xizmatlar ixtiyoriy bo'lib, maqolaning nashrga qabul qilinishini kafolatlamaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Xizmat turlari</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Imlo va uslubiy tahrir (til sifati)</li>
            <li>Formatlash va dizayn talablariga moslashtirish</li>
            <li>Jadval va rasm yozuvlarini standartlashtirish</li>
            <li>Adabiyotlar ro'yxatini tekshirish</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Qanday foydalaniladi</h4>
          <p class="mb-0">Tahrirlash xizmati talab qilinganda, tahririyat ish hajmi va muddatini baholab, alohida tartibda ma'lumot beradi.</p>
        </section>
        '''
    },
    'journal_metrics': {
        'title': 'Journal Metrics',
        'title_uz': 'Jurnal ko\'rsatkichlari',
        'title_ru': 'Показатели журнала',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlari</h4>
          <div class="space-y-4 text-gray-700">
            <div>
              <div class="font-medium text-gray-900">Foydalanish</div>
              <p class="mt-1">Yillik o'rtacha .... ming marta ko'riladi yoki yuklab olinadi.</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Iqtibos ko'rsatkichlari</div>
              <p class="mt-1">......</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Tezlik/qabul qilish</div>
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li>5 kun — Submission to first decision → Maqola topshirilgandan dastlabki tahririy qarorgacha bo'lgan muddat;</li>
                <li>9 kun — Submission to decision after review → Taqrizdan keyingi qaror qabul qilinishigacha bo'lgan muddat;</li>
                <li>18 kun — Submission to acceptance → Maqola topshirilgandan qabul qilinishigacha bo'lgan muddat;</li>
                <li>5 kun — Acceptance to online publication → Qabul qilingandan onlayn nashr etilgungacha bo'lgan muddat.</li>
              </ul>
            </div>
          </div>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlarini tushunish va ulardan foydalanish</h4>
          <p class="mb-4">Jurnal ko'rsatkichlari o'quvchilar va o'zlarining keyingi qo'lyozmalarini nashr qilish uchun qayerga topshirishni hal qilayotgan mualliflar uchun foydali vosita bo'lishi mumkin. Biroq, har qanday o'lchov jurnalning sifati va ta'siri haqidagi ma'lumotlarning faqat bir qismini aks ettiradi.</p>
          <p class="mb-4">Har bir ko'rsatkichning o'z cheklovlari bor — uni hech qachon alohida ko'rib chiqmaslik kerak. Ko'rsatkichlar sifat tahlilini almashtirish uchun emas, balki qo'llab-quvvatlash uchun ishlatilishi kerak. Jurnalning maqsadlari va qamrovi, o'quvchilar soni va oldingi kontentni ko'rib chiqish kabi sifat omillari bilan bir qatorda ko'rsatkichlardan foydalanishni tavsiya qilamiz.</p>
          <p class="mb-0">Bundan tashqari, individual maqola har doim nashr etilgan jurnalning samaradorligiga emas, balki uning mohiyatiga qarab baholanishi kerak. Qo'shimcha ma'lumot olish uchun jurnal ko'rsatkichlarini tushunish bo'yicha mualliflik xizmatlari qo'llanmasini o'qing.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlari haqida qisqacha</h4>
          <p class="mb-0">Yuqoridagi foydalanish va qabul qilish ma'lumotlari eng so'nggi to'liq kalendar yili uchun bo'lib, har yili fevral oyida yangilanadi. Tezlik ma'lumotlari har olti oyda oldingi olti oylik ma'lumotlar asosida yangilanadi. Iqtibos stavkalari yilning o'rtalarida yangilanadi. E'tibor bering, ba'zi jurnallar quyidagi ko'rsatkichlarning barchasini ko'rsatmasligi mumkin (sababini bilib oling).</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlari</h4>
          <div class="space-y-4 text-gray-700">
            <div>
              <div class="font-medium text-gray-900">Foydalanish</div>
              <p class="mt-1">Yillik o'rtacha .... ming marta ko'riladi yoki yuklab olinadi.</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Iqtibos ko'rsatkichlari</div>
              <p class="mt-1">......</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Tezlik/qabul qilish</div>
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li>5 kun — Submission to first decision → Maqola topshirilgandan dastlabki tahririy qarorgacha bo'lgan muddat;</li>
                <li>9 kun — Submission to decision after review → Taqrizdan keyingi qaror qabul qilinishigacha bo'lgan muddat;</li>
                <li>18 kun — Submission to acceptance → Maqola topshirilgandan qabul qilinishigacha bo'lgan muddat;</li>
                <li>5 kun — Acceptance to online publication → Qabul qilingandan onlayn nashr etilgungacha bo'lgan muddat.</li>
              </ul>
            </div>
          </div>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlarini tushunish va ulardan foydalanish</h4>
          <p class="mb-4">Jurnal ko'rsatkichlari o'quvchilar va o'zlarining keyingi qo'lyozmalarini nashr qilish uchun qayerga topshirishni hal qilayotgan mualliflar uchun foydali vosita bo'lishi mumkin. Biroq, har qanday o'lchov jurnalning sifati va ta'siri haqidagi ma'lumotlarning faqat bir qismini aks ettiradi.</p>
          <p class="mb-4">Har bir ko'rsatkichning o'z cheklovlari bor — uni hech qachon alohida ko'rib chiqmaslik kerak. Ko'rsatkichlar sifat tahlilini almashtirish uchun emas, balki qo'llab-quvvatlash uchun ishlatilishi kerak. Jurnalning maqsadlari va qamrovi, o'quvchilar soni va oldingi kontentni ko'rib chiqish kabi sifat omillari bilan bir qatorda ko'rsatkichlardan foydalanishni tavsiya qilamiz.</p>
          <p class="mb-0">Bundan tashqari, individual maqola har doim nashr etilgan jurnalning samaradorligiga emas, balki uning mohiyatiga qarab baholanishi kerak. Qo'shimcha ma'lumot olish uchun jurnal ko'rsatkichlarini tushunish bo'yicha mualliflik xizmatlari qo'llanmasini o'qing.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlari haqida qisqacha</h4>
          <p class="mb-0">Yuqoridagi foydalanish va qabul qilish ma'lumotlari eng so'nggi to'liq kalendar yili uchun bo'lib, har yili fevral oyida yangilanadi. Tezlik ma'lumotlari har olti oyda oldingi olti oylik ma'lumotlar asosida yangilanadi. Iqtibos stavkalari yilning o'rtalarida yangilanadi. E'tibor bering, ba'zi jurnallar quyidagi ko'rsatkichlarning barchasini ko'rsatmasligi mumkin (sababini bilib oling).</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlari</h4>
          <div class="space-y-4 text-gray-700">
            <div>
              <div class="font-medium text-gray-900">Foydalanish</div>
              <p class="mt-1">Yillik o'rtacha .... ming marta ko'riladi yoki yuklab olinadi.</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Iqtibos ko'rsatkichlari</div>
              <p class="mt-1">......</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Tezlik/qabul qilish</div>
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li>5 kun — Submission to first decision → Maqola topshirilgandan dastlabki tahririy qarorgacha bo'lgan muddat;</li>
                <li>9 kun — Submission to decision after review → Taqrizdan keyingi qaror qabul qilinishigacha bo'lgan muddat;</li>
                <li>18 kun — Submission to acceptance → Maqola topshirilgandan qabul qilinishigacha bo'lgan muddat;</li>
                <li>5 kun — Acceptance to online publication → Qabul qilingandan onlayn nashr etilgungacha bo'lgan muddat.</li>
              </ul>
            </div>
          </div>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlarini tushunish va ulardan foydalanish</h4>
          <p class="mb-4">Jurnal ko'rsatkichlari o'quvchilar va o'zlarining keyingi qo'lyozmalarini nashr qilish uchun qayerga topshirishni hal qilayotgan mualliflar uchun foydali vosita bo'lishi mumkin. Biroq, har qanday o'lchov jurnalning sifati va ta'siri haqidagi ma'lumotlarning faqat bir qismini aks ettiradi.</p>
          <p class="mb-4">Har bir ko'rsatkichning o'z cheklovlari bor — uni hech qachon alohida ko'rib chiqmaslik kerak. Ko'rsatkichlar sifat tahlilini almashtirish uchun emas, balki qo'llab-quvvatlash uchun ishlatilishi kerak. Jurnalning maqsadlari va qamrovi, o'quvchilar soni va oldingi kontentni ko'rib chiqish kabi sifat omillari bilan bir qatorda ko'rsatkichlardan foydalanishni tavsiya qilamiz.</p>
          <p class="mb-0">Bundan tashqari, individual maqola har doim nashr etilgan jurnalning samaradorligiga emas, balki uning mohiyatiga qarab baholanishi kerak. Qo'shimcha ma'lumot olish uchun jurnal ko'rsatkichlarini tushunish bo'yicha mualliflik xizmatlari qo'llanmasini o'qing.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlari haqida qisqacha</h4>
          <p class="mb-0">Yuqoridagi foydalanish va qabul qilish ma'lumotlari eng so'nggi to'liq kalendar yili uchun bo'lib, har yili fevral oyida yangilanadi. Tezlik ma'lumotlari har olti oyda oldingi olti oylik ma'lumotlar asosida yangilanadi. Iqtibos stavkalari yilning o'rtalarida yangilanadi. E'tibor bering, ba'zi jurnallar quyidagi ko'rsatkichlarning barchasini ko'rsatmasligi mumkin (sababini bilib oling).</p>
        </section>
        '''
    },
    'aims_scope': {
        'title': 'Aims and Scope',
        'title_uz': 'Maqsad va vazifalar',
        'title_ru': 'Цели и задачи',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Maqsad va qamrov</h4>
          <p class="mb-0">Jurnal filologiya va tilshunoslik sohasidagi nazariy va amaliy tadqiqotlarni yoritishga, zamonaviy ilmiy yondashuvlarni targ'ib etishga qaratilgan.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Asosiy yo'nalishlar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Umumiy va qiyosiy tilshunoslik</li>
            <li>Amaliy tilshunoslik, tarjimashunoslik</li>
            <li>Adabiyotshunoslik va matn tahlili</li>
            <li>Diskurs va pragmatika tadqiqotlari</li>
            <li>Til o'qitish metodikasi</li>
            <li>Korpus va raqamli lingvistika</li>
          </ul>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Maqsad va qamrov</h4>
          <p class="mb-0">Jurnal filologiya va tilshunoslik sohasidagi nazariy va amaliy tadqiqotlarni yoritishga, zamonaviy ilmiy yondashuvlarni targ'ib etishga qaratilgan.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Asosiy yo'nalishlar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Umumiy va qiyosiy tilshunoslik</li>
            <li>Amaliy tilshunoslik, tarjimashunoslik</li>
            <li>Adabiyotshunoslik va matn tahlili</li>
            <li>Diskurs va pragmatika tadqiqotlari</li>
            <li>Til o'qitish metodikasi</li>
            <li>Korpus va raqamli lingvistika</li>
          </ul>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Maqsad va qamrov</h4>
          <p class="mb-0">Jurnal filologiya va tilshunoslik sohasidagi nazariy va amaliy tadqiqotlarni yoritishga, zamonaviy ilmiy yondashuvlarni targ'ib etishga qaratilgan.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Asosiy yo'nalishlar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Umumiy va qiyosiy tilshunoslik</li>
            <li>Amaliy tilshunoslik, tarjimashunoslik</li>
            <li>Adabiyotshunoslik va matn tahlili</li>
            <li>Diskurs va pragmatika tadqiqotlari</li>
            <li>Til o'qitish metodikasi</li>
            <li>Korpus va raqamli lingvistika</li>
          </ul>
        </section>
        '''
    },
    'journal_info': {
        'title': 'Journal Information',
        'title_uz': 'Jurnal haqida ma\'lumot',
        'title_ru': 'Информация о журнале',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal haqida</h4>
          <p class="mb-0">Jurnal filologiya, tilshunoslik va adabiyotshunoslik yo'nalishlarida ilmiy maqolalar nashr etishga ixtisoslashgan. Maqsad — zamonaviy ilmiy yondashuvlarni targ'ib qilish va ilmiy hamkorlikni kengaytirish.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kimlar uchun</h4>
          <p class="mb-0">Jurnal o'qituvchilar, tadqiqotchilar, doktorantlar va sohaga qiziquvchi mutaxassislar uchun mo'ljallangan.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Nashr siyosati</h4>
          <p class="mb-0">Maqolalar ilmiy ekspertiza asosida saralanadi. Mualliflar tomonidan taqdim etilgan ma'lumotlarning ishonchliligi va manbalarining to'g'riligi muhim mezon hisoblanadi.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal haqida</h4>
          <p class="mb-0">Jurnal filologiya, tilshunoslik va adabiyotshunoslik yo'nalishlarida ilmiy maqolalar nashr etishga ixtisoslashgan. Maqsad — zamonaviy ilmiy yondashuvlarni targ'ib qilish va ilmiy hamkorlikni kengaytirish.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kimlar uchun</h4>
          <p class="mb-0">Jurnal o'qituvchilar, tadqiqotchilar, doktorantlar va sohaga qiziquvchi mutaxassislar uchun mo'ljallangan.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Nashr siyosati</h4>
          <p class="mb-0">Maqolalar ilmiy ekspertiza asosida saralanadi. Mualliflar tomonidan taqdim etilgan ma'lumotlarning ishonchliligi va manbalarining to'g'riligi muhim mezon hisoblanadi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal haqida</h4>
          <p class="mb-0">Jurnal filologiya, tilshunoslik va adabiyotshunoslik yo'nalishlarida ilmiy maqolalar nashr etishga ixtisoslashgan. Maqsad — zamonaviy ilmiy yondashuvlarni targ'ib qilish va ilmiy hamkorlikni kengaytirish.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kimlar uchun</h4>
          <p class="mb-0">Jurnal o'qituvchilar, tadqiqotchilar, doktorantlar va sohaga qiziquvchi mutaxassislar uchun mo'ljallangan.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Nashr siyosati</h4>
          <p class="mb-0">Maqolalar ilmiy ekspertiza asosida saralanadi. Mualliflar tomonidan taqdim etilgan ma'lumotlarning ishonchliligi va manbalarining to'g'riligi muhim mezon hisoblanadi.</p>
        </section>
        '''
    },
    'news_calls': {
        'title': 'News and Calls for Papers',
        'title_uz': 'Yangiliklar va maqolalar uchun chaqiruvlar',
        'title_ru': 'Новости и приглашения к публикации',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yangiliklar va chaqiruvlar</h4>
          <p class="mb-0">Ushbu bo'limda jurnal faoliyatiga oid yangiliklar, maxsus sonlar bo'yicha chaqiruvlar va muhim e'lonlar muntazam joylashtiriladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Qanday kuzatish mumkin</h4>
          <p class="mb-0">Yangiliklar bo'limini tekshirib boring yoki e'lon qilingan chaqiruvlarga muvofiq maqolalaringizni taqdim eting.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yangiliklar va chaqiruvlar</h4>
          <p class="mb-0">Ushbu bo'limda jurnal faoliyatiga oid yangiliklar, maxsus sonlar bo'yicha chaqiruvlar va muhim e'lonlar muntazam joylashtiriladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Qanday kuzatish mumkin</h4>
          <p class="mb-0">Yangiliklar bo'limini tekshirib boring yoki e'lon qilingan chaqiruvlarga muvofiq maqolalaringizni taqdim eting.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yangiliklar va chaqiruvlar</h4>
          <p class="mb-0">Ushbu bo'limda jurnal faoliyatiga oid yangiliklar, maxsus sonlar bo'yicha chaqiruvlar va muhim e'lonlar muntazam joylashtiriladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Qanday kuzatish mumkin</h4>
          <p class="mb-0">Yangiliklar bo'limini tekshirib boring yoki e'lon qilingan chaqiruvlarga muvofiq maqolalaringizni taqdim eting.</p>
        </section>
        '''
    },
    'conferences': {
        'title': 'Conferences',
        'title_uz': 'Konferentsiyalar',
        'title_ru': 'Конференции',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Konferensiyalar</h4>
          <p class="mb-0">Jurnal hamkorligida o'tkaziladigan ilmiy konferensiyalar, davra suhbatlari va seminarlar haqida ma'lumotlar shu yerda beriladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Ishtirok va nashr</h4>
          <p class="mb-0">Konferensiya materiallari asosida tayyorlangan maqolalar jurnal talablariga mos bo'lsa, alohida ko'rib chiqiladi.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Konferensiyalar</h4>
          <p class="mb-0">Jurnal hamkorligida o'tkaziladigan ilmiy konferensiyalar, davra suhbatlari va seminarlar haqida ma'lumotlar shu yerda beriladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Ishtirok va nashr</h4>
          <p class="mb-0">Konferensiya materiallari asosida tayyorlangan maqolalar jurnal talablariga mos bo'lsa, alohida ko'rib chiqiladi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Konferensiyalar</h4>
          <p class="mb-0">Jurnal hamkorligida o'tkaziladigan ilmiy konferensiyalar, davra suhbatlari va seminarlar haqida ma'lumotlar shu yerda beriladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Ishtirok va nashr</h4>
          <p class="mb-0">Konferensiya materiallari asosida tayyorlangan maqolalar jurnal talablariga mos bo'lsa, alohida ko'rib chiqiladi.</p>
        </section>
        '''
    },
    'for_uzgumya_researchers': {
        'title': 'For UzGUMYA Researchers',
        'title_uz': 'UzDJTU tadqiqotchilari uchun',
        'title_ru': 'Для исследователей УзГУМЯ',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">UzDJTU tadqiqotchilari uchun</h4>
          <p class="mb-0">Universitet tadqiqotchilari uchun mualliflik jarayoni bo'yicha maslahat va metodik ko'mak ko'rsatiladi. Ichki ilmiy yo'nalishlarga mos mavzular alohida tavsiya qilinishi mumkin.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tavsiyalar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Muassasa emaili orqali ro'yxatdan o'tish tavsiya etiladi.</li>
            <li>Maqola yo'nalishini kafedra yoki ilmiy rahbar bilan muvofiqlashtiring.</li>
            <li>Ichki grantlar va loyihalar bo'yicha natijalarni alohida ko'rsating.</li>
          </ul>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">UzDJTU tadqiqotchilari uchun</h4>
          <p class="mb-0">Universitet tadqiqotchilari uchun mualliflik jarayoni bo'yicha maslahat va metodik ko'mak ko'rsatiladi. Ichki ilmiy yo'nalishlarga mos mavzular alohida tavsiya qilinishi mumkin.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tavsiyalar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Muassasa emaili orqali ro'yxatdan o'tish tavsiya etiladi.</li>
            <li>Maqola yo'nalishini kafedra yoki ilmiy rahbar bilan muvofiqlashtiring.</li>
            <li>Ichki grantlar va loyihalar bo'yicha natijalarni alohida ko'rsating.</li>
          </ul>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">UzDJTU tadqiqotchilari uchun</h4>
          <p class="mb-0">Universitet tadqiqotchilari uchun mualliflik jarayoni bo'yicha maslahat va metodik ko'mak ko'rsatiladi. Ichki ilmiy yo'nalishlarga mos mavzular alohida tavsiya qilinishi mumkin.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tavsiyalar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Muassasa emaili orqali ro'yxatdan o'tish tavsiya etiladi.</li>
            <li>Maqola yo'nalishini kafedra yoki ilmiy rahbar bilan muvofiqlashtiring.</li>
            <li>Ichki grantlar va loyihalar bo'yicha natijalarni alohida ko'rsating.</li>
          </ul>
        </section>
        '''
    },
    'for_all_researchers': {
        'title': 'For All Researchers',
        'title_uz': 'Barcha tadqiqotchilar uchun',
        'title_ru': 'Для всех исследователей',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Barcha tadqiqotchilar uchun</h4>
          <p class="mb-0">Jurnal barcha hudud va muassasalardan bo'lgan tadqiqotchilar uchun ochiq. Mavzu jurnal qamroviga mos bo'lsa, maqola ko'rib chiqiladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tavsiyalar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Maqolani jurnal talablari asosida tayyorlang.</li>
            <li>Adabiyotlar ro'yxatini aniq va to'liq shakllantiring.</li>
            <li>Ochiq ma'lumotlar va ilovalarni iloji boricha taqdim eting.</li>
          </ul>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Barcha tadqiqotchilar uchun</h4>
          <p class="mb-0">Jurnal barcha hudud va muassasalardan bo'lgan tadqiqotchilar uchun ochiq. Mavzu jurnal qamroviga mos bo'lsa, maqola ko'rib chiqiladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tavsiyalar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Maqolani jurnal talablari asosida tayyorlang.</li>
            <li>Adabiyotlar ro'yxatini aniq va to'liq shakllantiring.</li>
            <li>Ochiq ma'lumotlar va ilovalarni iloji boricha taqdim eting.</li>
          </ul>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Barcha tadqiqotchilar uchun</h4>
          <p class="mb-0">Jurnal barcha hudud va muassasalardan bo'lgan tadqiqotchilar uchun ochiq. Mavzu jurnal qamroviga mos bo'lsa, maqola ko'rib chiqiladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tavsiyalar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Maqolani jurnal talablari asosida tayyorlang.</li>
            <li>Adabiyotlar ro'yxatini aniq va to'liq shakllantiring.</li>
            <li>Ochiq ma'lumotlar va ilovalarni iloji boricha taqdim eting.</li>
          </ul>
        </section>
        '''
    }
}

def update_pages(only_missing=False):
    # Initialize database connection
    dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    
    current_time = int(time.time())
    
    # Get all existing pages
    existing_pages = dbc.pages.get().exec()
    existing_aliases = {page['alias']: page for page in existing_pages} if existing_pages else {}
    
    # Update or create each page
    for alias, page_data in PAGES_DATA.items():
        if alias in existing_aliases:
            if only_missing:
                print(f"Skipping existing page: {page_data['title']}")
                continue
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


def _parse_args():
    parser = argparse.ArgumentParser(description='Seed/update static pages')
    parser.add_argument(
        '--only-missing',
        action='store_true',
        help='Create only missing pages and keep existing content untouched',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    update_pages(only_missing=args.only_missing)
