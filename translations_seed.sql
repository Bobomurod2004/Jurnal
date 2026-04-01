--
-- PostgreSQL database dump
--

\restrict ocXOpGz2tW8iR24MM5uJCwaNZhBFbEEqARP0HF2uOjyE7E3n6fGaKDPj0DZn7ED

-- Dumped from database version 17.8
-- Dumped by pg_dump version 17.8

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: translations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.translations (id, alias, content, content_uz, content_ru, created_at) FROM stdin;
1141	my_purchases_desc		Sotib olingan maqola va jurnallarni ko'rish	Просмотр купленных статей и журналов	\N
1391	no_items_description	No news or announcements available yet			\N
1367	register_info_1	The electronic scientific-methodological journal 'Philology Issues' uses the information provided here to create a personal page for you.			\N
1368	register_info_2	Electronic scientific-methodological journal 'Philology Issues' also wants to use your e-mail address to send you offers and information about related products and services. In particular, the Editorial Office can offer access to a wider range of information that may be of interest to you, including advice and resources on how to publish it.			\N
1547	about	About	Biz haqimizda	О нас	1750642943
1548	contact	Contact	Aloqa	Контакты	1750642943
1549	archive	Archive	Arxiv	Архив	1750642943
1550	language	Language	Til	Язык	1750642943
1551	settings	Settings	Sozlamalar	Настройки	1750642943
1552	save	Save	Saqlash	Сохранить	1750642943
1553	edit	Edit	Tahrirlash	Редактировать	1750642943
1554	delete	Delete	O'chirish	Удалить	1750642943
1555	view	View	Ko'rish	Просмотр	1750642943
1087	language_uz	O'zbek	O'zbek	O'zbek	\N
1088	language_ru	Русский	Русский	Русский	\N
1089	language_en	English	English	English	\N
1090	login	Login	Kirish	Вход	\N
1091	login_to_account	Login to Account	Hisobga kirish	Вход в аккаунт	\N
1085	alias	en	uz	ru	\N
1174	address_information		Manzil ma'lumotlari	Информация об адресе	\N
1144	article_count		maqola	статей	\N
1142	articles_section		Maqolalar	Статьи	\N
1163	change_password		Parolni o'zgartirish	Изменить пароль	\N
1135	citations		Iqtiboslar	Цитирования	\N
1139	confirm_delete		O'chirish	Удалить	\N
1180	confirm_password		Parolni tasdiqlang	Подтвердите пароль	\N
1128	created		Yaratilgan	Создано	\N
1115	delete_article		Maqolani o'chirish	Удалить статью	\N
1156	delete_current		Joriyni o'chirish	Удалить текущее	\N
1145	download_issue_pdf		Jurnalni yuklab olish	Скачать журнал	\N
1113	download_pdf		PDF yuklab olish	Скачать PDF	\N
1118	draft		Qoralama	Черновик	\N
1143	issues_section		Jurnallar	Журналы	\N
1153	main_information		Asosiy ma'lumot	Основная информация	\N
1140	my_purchases_title		Mening xaridlarim	Мои покупки	\N
1179	new_password		Yangi parol	Новый пароль	\N
1196	no_payments		To'lovlar mavjud emas	Нет платежей	\N
1167	orcid		ORCID	ORCID	\N
1181	password_updated		Parol muvaffaqiyatli yangilandi	Пароль успешно обновлен	\N
1192	payment_actions		Harakatlar	Действия	\N
1208	payment_pending		Kutilmoqda	Ожидается	\N
1193	payment_proof		To'lov tasdiqnomasi	Подтверждение оплаты	\N
1190	payment_status		Holat	Статус	\N
1188	payment_type		To'lov turi	Тип платежа	\N
1152	profile		Profil	Профиль	\N
1154	profile_photo		Profil rasmi	Фото профиля	\N
1119	published		Nashr etilgan	Опубликовано	\N
1130	reason		Sabab	Причина	\N
1110	research_article		Ilmiy maqola	Научная статья	\N
1164	save_information		Ma'lumotlarni saqlash	Сохранить информацию	\N
1168	search_by_orcid		ORCID bo'yicha qidirish	Поиск по ORCID	\N
1127	submit_first_article		Birinchi maqolangizni yuboring	Подать первую статью	\N
1095	register	Register	Ro'yxatdan o'tish	Регистрация	\N
1096	or	or	yoki	или	\N
1098	email_placeholder	johndoe@example.com	misol@mail.com	primer@mail.com	\N
1099	password_placeholder	Password	Parol	Пароль	\N
1100	my_account	My Account	Mening hisobim	Мой аккаунт	\N
1101	logout	Logout	Chiqish	Выйти	\N
1104	my_payments	My Payments	Mening to'lovlarim	Мои платежи	\N
1105	my_profile	My Profile	Mening profilim	Мой профиль	\N
1107	guides	Guides	Qo'llanmalar	Руководства	\N
1199	subscription_duration		Muddat	Длительность	\N
1198	subscription_price		Narx	Цена	\N
1121	under_review		Ko'rib chiqilmoqda	На рассмотрении	\N
1146	view_full_issue		To'liq jurnalni ko'rish	Просмотр журнала	\N
1185	subscription_section	Choose Your Subscription Plan	Obuna	Подписка	\N
1186	payment_history	Payment History	To'lovlar tarixi	История платежей	\N
1202	month	month	oy	месяц	\N
1148	days_left	days left	kun qoldi	дней осталось	\N
1151	subscribe_now	Subscribe Now	Hozir obuna bo'ling	Подписаться сейчас	\N
1155	update_photo		Rasmni yangilash	Обновить фото	\N
1129	updated		Yangilangan	Обновлено	\N
1114	view_article		Maqolani ko'rish	Просмотр статьи	\N
1203	year		yil	год	\N
1195	delete_payment	Delete Payment	To'lovni o'chirish	Удалить платеж	\N
1187	payment_date	Payment Date	To'lov sanasi	Дата платежа	\N
1201	subscribe	Subscribe	Obuna bo'lish	Подписаться	\N
1206	new_issues	New Issues	Yangi sonlar	Новые выпуски	\N
1209	payment_paid	Paid	To'langan	Оплачено	\N
1210	payment_rejected	Rejected	Rad etilgan	Отклонено	\N
1086	website_title	Philology Matters	Filologiya masalalari	Вопросы филологии	\N
1111	open_access	Open access	Ochiq foydalanish	Открытый доступ	\N
1158	last_name	Last Name	Familiya	Фамилия	\N
1161	country	Country	Mamlakat	Страна	\N
2179	journal_metrics	journal_metrics			1772094904
1162	choose_country	Choose a country	Mamlakatni tanlang	Выберите страну	\N
1132	issue	Issue	Son	Выпуск	\N
1133	views	Views	Ko'rishlar	Просмотры	\N
1124	my_articles_title	My Articles	Mening maqolalarim	Мои статьи	\N
1117	view_issue	View Issue	Sonni ko'rish	Просмотр выпуска	\N
1189	payment_amount	Amount	Summa	Сумма	\N
1171	organization	Organization	Tashkilot	Организация	\N
1172	department	Department	Bo'lim	Отдел	\N
1173	position	Position	Lavozim	Должность	\N
1176	city	City	Shahar	Город	\N
1178	phone	Phone	Telefon	Телефон	\N
1093	password	Password	Parol	Пароль	\N
1131	volume	Volume	Jild	Том	\N
1138	cancel	Cancel	Bekor qilish	Отмена	\N
1157	first_name	First name	Ism	Имя	\N
1170	full_author_name	Full author name	To'liq muallif ismi	Полное имя автора	\N
1175	street	Street	Ko'cha	Улица	\N
1183	my_payments_title	My Payments	Mening to'lovlarim	Мои платежи	\N
1191	payment_note	Payment Note	Izoh	Примечание	\N
1205	all_articles	All Articles	Barcha maqolalar	Все статьи	\N
1212	payment_issue		Jurnal soni	Выпуск журнала	\N
1214	upload_payment_proof	Upload Payment Proof	To'lov tasdiqnomasini yuklash	Загрузка подтверждения оплаты	\N
1216	select_file	Select File	Faylni tanlang	Выберите файл	\N
1217	upload	Upload	Yuklash	Загрузить	\N
1218	delete_payment_confirmation	Delete Payment	To'lovni o'chirish	Удаление платежа	\N
1220	submit_new_article	Submit New Article	Yangi maqola yuborish	Подать новую статью	\N
1221	basic_information	Basic Information	Asosiy ma'lumot	Основная информация	\N
1251	special_issue_question	Is this a special issue or collection of articles?	Bu maxsus sonmi?	Это специальный выпуск?	\N
1244	keywords_desc	About keywords	Maqola uchun kalit so'zlar	Ключевые слова для статьи	\N
1223	data_availability	Data Availability	Ma'lumotlar mavjudligi	Доступность данных	\N
1224	data_availability_desc	About the data	Tadqiqot ma'lumotlarining ochiq bo'lishi	Открытость исследовательских данных	\N
1225	copyright	Copyright	Mualliflik huquqi	Авторское право	\N
1227	file_upload	File Upload	Fayl yuklash	Загрузка файлов	\N
1228	file_upload_desc	File Upload section	Maqola fayllarini yuklash	Загрузка файлов статьи	\N
1229	ethical_standards	Ethical Standards	Axloqiy standartlar	Этические стандарты	\N
1232	consent_publication_desc	Consent for publication	Qatnashchilardan rozilik olish	Получение согласия от участников	\N
1233	acknowledgements	Acknowledgements	Minnatdorchilik	Благодарности	\N
1234	acknowledgements_desc	Acknowledgements section	Yordamchilarni e'tirof etish	Признание помощников	\N
1235	permissions	Permissions	Ruxsatlar	Разрешения	\N
1238	word_count_desc	About word count	Maqoladagi so'zlar soni	Количество слов в статье	\N
1241	competing_interests	Competing Interests	Qarama-qarshi manfaatlar	Конкурирующие интересы	\N
1243	keywords	Keywords	Kalit so'zlar	Ключевые слова	\N
1245	classification	Classification	Tasnif	Классификация	\N
1248	open_access_editorial_desc	About open access and editorial services	Nashr etish variantlari	Варианты публикации	\N
1249	title	Title	Sarlavha	Название	\N
1250	abstract	Abstract	Annotatsiya	Аннотация	\N
1252	yes	Yes	Ha	Да	\N
1253	no	No	Yo'q	Нет	\N
1254	select_one_option	Select one option.	Birini tanlang	Выберите один вариант	\N
1259	i_confirm	I confirm	Tasdiqlayapman	Подтверждаю	\N
1260	you_should_confirm	You should confirm.	Siz tasdiqlaishingiz kerak.	Вы должны подтвердить.	\N
1263	file_with_author_details	File with author details	Muallif tafsilotlari bilan fayl	Файл с данными автора	\N
1265	download	Download	Yuklab olish	Скачать	\N
1266	update_file_with_author_details	Update file (with author details)	Faylni yangilash (muallif tafsilotlari bilan)	Обновить файл (с данными автора)	\N
1268	uploaded	Uploaded	Yuklandi	Загружено	\N
1269	you_should_upload_files	You should upload files.	Siz fayllarni yuklashingiz kerak.	Вы должны загрузить файлы.	\N
1272	acknowledgements_text	I confirm that each person named in the "Acknowledgements" section of the manuscript has been notified of their inclusion and has approved it.	Men qo'lyozmaning "Minnatdorchilik" bo'limida qayd etilgan har bir kishi o'z kiritilganligi haqida xabardor qilingan va uni ma'qullaganini tasdiqlayapman.	Я подтверждаю, что каждый человек, указанный в разделе "Благодарности" рукописи, был уведомлен о своем включении и одобрил его.	\N
1273	previously_published_question	Are you using previously published materials in this article?	Siz ushbu maqolada ilgari nashr etilgan materiallardan foydalanyapsizmi?	Используете ли вы в этой статье ранее опубликованные материалы?	\N
1274	word_count_instruction	Please indicate the word count of your article.	Iltimos, maqolangizning so'zlar sonini ko'rsating.	Пожалуйста, укажите количество слов в вашей статье.	\N
1275	word_count_field_required	This field must be completed for review.	Ushbu maydonni ko'rib chiqish uchun to'ldirish kerak.	Это поле должно быть заполнено для рассмотрения.	\N
1276	corresponding_author	Corresponding author	Mas'ul muallif	Корреспондентский автор	\N
1277	current_corresponding_author	Current corresponding author	Joriy mas'ul muallif	Текущий корреспондентский автор	\N
1279	i_am_corresponding_author	I am corresponding author	Men mas'ul muallifman	Я корреспондентский автор	\N
1280	subauthors	Subauthor(s)	Hammuallif(lar)	Соавтор(ы)	\N
2180	no_results	no_results			1772097501
1281	current_subauthors_list	Current subauthors list	Joriy hammuallif(lar) ro'yxati	Текущий список соавторов	\N
1282	delete_this_author	Delete this author	Ushbu muallifni o'chirish	Удалить этого автора	\N
1284	add_new_author	Add new author	Yangi muallif qo'shish	Добавить нового автора	\N
1285	select_corresponding_author	Select corresponding author	Mas'ul muallifni tanlang	Выберите корреспондентского автора	\N
1211	payment_subscription	Subscription for	Obuna	Подписка	\N
1213	payment_article	Article Payment	Maqola	Статья	\N
1350	annual_plan	Annual Plan			\N
1351	annual_plan_desc	Best value for regular readers			\N
1339	article_access_info	You will get access to the articles after payment verification			\N
1349	cancel_anytime	Cancel anytime			\N
1342	download_access	Download any article in PDF format			\N
1343	early_access	Get early access to new issues			\N
1356	early_access_new_issues	Early access to new issues			\N
1363	email_confirm	Confirm E-mail			\N
1354	everything_in_monthly	Everything in monthly plan			\N
1361	first_name_placeholder	John			\N
1347	full_article_access	Full access to all articles			\N
1362	last_name_placeholder	Doe			\N
1344	monthly_plan	Monthly Plan			\N
1345	monthly_plan_desc	Perfect for short-term access			\N
1341	optional	optional			\N
1364	password_confirm	Confirm Password			\N
1337	payment_guide	Payment Guide			\N
1359	payment_processing	Processing			\N
1358	payment_unpaid	Unpaid			\N
1346	per_month	per month			\N
1352	per_year	per year			\N
1289	new_keyword	New keyword	Yangi kalit so'z	Новое ключевое слово	\N
1291	add_at_least_keywords	Add at least 3 keywords	Kamida 3 ta kalit so'z qo'shing	Добавьте минимум 3 ключевых слова	\N
1293	search_classifications	Search classifications	Tasniflarni qidirish	Поиск классификаций	\N
1294	start_typing	Start typing	Yozishni boshlang	Начните вводить	\N
1295	selected_classifications	Selected classifications	Tanlangan tasniflar	Выбранные классификации	\N
1296	add_at_least_classification	Add at least 1 classification.	Kamida 1 ta tasnif qo'shing.	Добавьте минимум 1 классификацию.	\N
1299	save_as_draft	Save as draft	Qoralama sifatida saqlash	Сохранить как черновик	\N
1300	saved	Saved	Saqlandi	Сохранено	\N
1301	review_article	Review article	Maqolani ko'rib chiqish	Рассмотреть статью	\N
1302	submitted	Submitted	Yuborildi	Отправлено	\N
1303	form_errors_title	There are errors on form	Formada xatolar mavjud	В форме есть ошибки	\N
1305	choose_author	Choose author	Muallifni tanlang	Выберите автора	\N
1306	author_orcid	ORCID author	Muallif ORCID	ORCID автора	\N
1308	failed_to_load_submission	Failed to load submission	Maqolani yuklashda xatolik	Ошибка загрузки статьи	\N
1309	failed_to_save_draft	Failed to save draft	Qoralamani saqlashda xatolik	Ошибка сохранения черновика	\N
1310	failed_to_submit_article	Failed to submit article	Maqolani yuborishda xatolik	Ошибка отправки статьи	\N
1311	are_you_sure_delete_draft	Are you sure you want to delete this draft?	Qoralama maqolani o'chirmoqchimisiz?	Вы уверены, что хотите удалить черновик?	\N
1313	try_again	Try again	Qayta urinib ko'ring	Попробуйте еще раз	\N
1315	please_enter_orcid	Please enter ORCID	Iltimos, ORCID kiriting	Пожалуйста, введите ORCID	\N
1317	fill_required_fields_colon	Fill required fields:	Majburiy maydonlarni to'ldiring:	Заполните обязательные поля:	\N
1319	valid_email_required	Valid email required	To'g'ri email manzilini kiriting	Введите правильный email адрес	\N
1320	failed_to_create_author	Failed to create author	Muallifni yaratishda xatolik	Ошибка создания автора	\N
1321	unknown_error	Unknown error	Noma'lum xatolik	Неизвестная ошибка	\N
1322	error_title_required	Title is required	Sarlavha talab qilinadi	Название обязательно	\N
1325	error_specify_dataset	Specify if this includes a dataset	Ma'lumotlar to'plami borligini aniqlang	Укажите, есть ли связанный набор данных	\N
1327	error_upload_required_files	Please upload required files	Iltimos, zarur fayllarni yuklang	Пожалуйста, загрузите необходимые файлы	\N
1329	error_consent_required	Consent for publication is required	Nashr etish uchun rozilik talab qilinadi	Согласие на публикацию обязательно	\N
1332	error_word_count_exceeds	Word count exceeds the limit	So'zlar soni chegaradan oshib ketdi	Количество слов превышает лимит	\N
1333	error_author_details_incomplete	Author details are incomplete	Muallif ma'lumotlari to'liq emas	Данные автора неполные	\N
1335	error_keywords_required	Keywords are required	Kalit so'zlar talab qilinadi	Ключевые слова обязательны	\N
1336	error_select_classifications	Select appropriate classifications	Tegishli tasniflarni tanlang	Выберите подходящие классификации	\N
1355	priority_support	Priority support			\N
1357	proceed_subscription	Proceed with Subscription			\N
1360	register_title	Register			\N
1353	save_percent	Save 17%			\N
1340	selected_file	Selected file			\N
1338	subscription_activation_info	Your subscription will be activated after payment verification			\N
1348	unlimited_downloads	Unlimited article downloads			\N
1092	email	E-mail	E-pochta	Эл. почта	\N
1102	my_articles	My Articles	Mening maqolalarim	Мои статьи	\N
1106	submit_article	Submit Article	Maqola yuborish	Подать статью	\N
1159	patronymic	Patronymic	Otasining ismi	Отчество	\N
1204	unlimited_access	Get unlimited access to all articles	Cheksiz kirish	Неограниченный доступ	\N
2181	registration_successful	registration_successful			1772097903
1215	proof_requirements	Please upload a clear image or PDF of your payment receipt	To'lov tasdiqnomasi sifatida bank cheki yoki to'lov skrinshotini yuklang	Загрузите банковскую квитанцию или скриншот оплаты в качестве подтверждения	\N
1288	current_keywords_list	Current keywords list	Joriy kalit so'zlar ro'yxati	Текущий список ключевых слов	\N
1418	footer_crossref	Crossref DOI			\N
1461	access_required	Access Required			\N
1366	agree_notifications	I want to receive resources and offers from the department.			\N
1365	agree_terms	I agree to the terms			\N
1387	all	All			\N
1388	announcement	Announcement			\N
1457	article_id	Article ID			\N
1370	back_to_login	Back to login			\N
1398	back_to_news	Back to news			\N
1451	call_for_papers	Call for Papers: Special Issue on Cognitive Linguistics			\N
1456	cite	Cite			\N
1446	conferences	Conferences			\N
1430	days	days			\N
1460	download_full_article	Download Full Article			\N
1423	footer_articles_issues	Articles & Issues			\N
1426	footer_contact	Contact			\N
1419	footer_eissn	E-ISSN			\N
1424	footer_submit_subscribe	Submit & Subscribe			\N
1425	footer_subscribe_journal	Subscribe to Journal			\N
1416	hero_image_alt	Language and Health			\N
1394	home	Home			\N
1452	international_conference	International Conference on Applied Linguistics 2025			\N
1454	journal_cover	Journal Cover			\N
1450	linguistic_markers_story_recall	Linguistic markers of story recall can help differentiate mild cognitive impairment from normal aging			\N
1379	menu_aims_scope	Aims and Scope			\N
1406	menu_all_issues	All Issues			\N
1374	menu_author_instructions	Instructions for Authors			\N
1408	menu_collections	Collections			\N
1402	menu_conferences	Video Guide			\N
1405	menu_current_issue	Current Issue			\N
1376	menu_editing_services	Site Editing Services			\N
1381	menu_editorial_board	Editorial Board			\N
1375	menu_editorial_policy	Editorial Policy			\N
1413	menu_for_all	For All Researchers			\N
1380	menu_journal_info	Journal Information			\N
1378	menu_journal_metrics	Journal Metrics			\N
1404	menu_latest_articles	Latest Articles			\N
1410	menu_most_cited	Most Cited Articles			\N
1409	menu_most_read	Most Read Articles			\N
1382	menu_news_calls	News and Calls for Papers			\N
1407	menu_special_issues	Special Issues			\N
1373	menu_submission_guidelines	Submission Guidelines			\N
1385	news_and_announcements	News and Announcements			\N
1386	news_page_description	Latest journal news and important announcements			\N
1401	next	Next			\N
1384	no_announcements_available	No announcements available yet			\N
1393	no_announcements_description	No announcements available yet			\N
1396	no_content_available	No content available			\N
1390	no_items_available	No items available			\N
1383	no_news_available	No news available yet			\N
1392	no_news_description	No news available yet			\N
1400	previous	Previous			\N
1395	published_by	Published by			\N
1459	published_online	Published online			\N
1389	read_more	Read more			\N
1458	received	Received			\N
1371	register_button	Register			\N
1369	register_info_3	You can opt out of receiving these communications at any time by clicking the unsubscribe button. More information can be found in the Publisher's Privacy Policy.			\N
1399	related_articles	Related articles			\N
1455	share	Share			\N
1397	share_this_article	Share this article			\N
1449	submit_application	Submit application			\N
1448	submit_paper_text	If you want to submit a paper, click the button below. Our team will be happy to assist you. You can also register on our site.			\N
1462	subscription_required_message	You need to have an active subscription or purchase this article to access the full content.			\N
1544	abstract_preview	Abstract Preview			\N
1510	actions	Actions			\N
1497	address	Address			\N
1481	aims_and_goals	Aims and Goals			\N
1524	amount	Amount			\N
1194	upload_proof	Upload Proof	Tasdiqnoma yuklash	Загрузить подтверждение	\N
1427	about_journal	About the Journal	Jurnal haqida	О журнале	\N
1422	footer_about_journal	About Journal	Jurnal haqida	О журнале	\N
1377	menu_about_journal	About the Journal	Jurnal haqida	О журнале	\N
1435	editor_name	Gulandom Bakieva	Gulandom Boqiyeva	Гуландом Бакиева	\N
1434	view_editorial_board	View editorial board	Tahrir hay’ati bilan tanishing	Посмотреть редакционную коллегию	\N
1403	menu_view_all	View All Articles and Issues	Barcha maqolalar va sonlarni ko‘rish	Посмотреть все статьи и выпуски	\N
1411	menu_subscribe	Subscribe	Obuna bo‘lish	Подписаться	\N
1415	menu_guide_for_authors	Guide for authors	Mualliflar uchun qo‘llanma	Руководство для авторов	\N
1439	most_downloaded	Most downloaded	Eng ko‘p yuklab olinganlar	Наиболее скачиваемые	\N
1437	articles	Articles	Maqolalar	Статьи	\N
1440	most_popular	Most popular	Eng mashhurlar	Самые популярные	\N
1444	news	News	Yangiliklar	Новости	\N
1453	view_pdf	View PDF	PDFni ko‘rish	Посмотреть PDF	\N
1447	view_all_news	View all news	Barcha yangiliklarni ko‘rish	Посмотреть все новости	\N
1445	announcements	Announcements	E’lonlar	Объявления	\N
1222	basic_info_desc	All your basic information	Maqola sarlavhasi va annotatsiyasi	Название статьи и аннотация	\N
1465	altmetric	Downloads	Yuklab olishlar	Загрузки	\N
1231	consent_for_publication	Consent for Publication	Nashr etish uchun rozilik	Согласие на публикацию	\N
1236	permissions_desc	About permissions	Oldindan nashr etilgan materiallar	Ранее опубликованные материалы	\N
1246	classification_desc	About classification	Ilmiy sohalar bo'yicha tasnif	Классификация по научным областям	\N
1258	copyright_confirmation_text	Confirm that you have seen, read and understood the publisher's guidance on copyright and author rights.	Siz nashriyotning mualliflik huquqi va muallif huquqlari bo'yicha ko'rsatmalarini ko'rganingiz, o'qiganingiz va tushunganingizni tasdiqlang.	Подтвердите, что вы видели, прочитали и поняли руководящие принципы издателя по авторским правам и правам авторов.	\N
1518	annual	Annual			\N
1484	another_one	Another one			\N
1474	article	Article			\N
1477	articles_for_this_issue_will_be_available_soon	Articles for this issue will be available soon			\N
1475	articles_in_this_issue	articles in this issue			\N
1521	cancel_subscription	Cancel Subscription			\N
1489	contact_description	Have questions? We'd love to help. Fill out the form below and we'll get back to you shortly.			\N
1496	contact_information	Contact Information			\N
1488	contact_us	Contact Us			\N
1515	create_first_submission	Create First Submission			\N
1466	crossref	CrossRef			\N
1519	current_plan	Current Plan			\N
1543	doi_label	DOI			\N
1468	download_all_issue	Download all issue			\N
1523	download_invoice	Download Invoice			\N
1478	editorial_board	Editorial Board			\N
1479	editorial_board_description	The Editorial Board is a team of scholars who ensure the scientific quality of the journal and determine its development directions.			\N
1528	failed	Failed			\N
1500	faq	FAQ			\N
1531	filter	Filter			\N
1471	full_issue_access_required	Full issue access required			\N
1490	full_name	Full Name			\N
1522	invoice	Invoice			\N
1485	issues	Issues			\N
1498	journal_address	123 Test Street, Test City, 12345			\N
1509	last_updated	Last Updated			\N
1492	message	Message			\N
1464	metrics	Metrics			\N
1517	monthly	Monthly			\N
1470	next_issue	Next issue			\N
1540	no_articles_found	No articles found			\N
1541	no_articles_found_desc	No articles match your search criteria. Try adjusting your filters.			\N
1513	no_submissions	No Submissions			\N
1514	no_submissions_desc	You haven't submitted any articles yet.			\N
1483	one_more_other_page	One more other page			\N
1482	other_page	Other page			\N
1480	pages	Pages			\N
1526	paid	Paid			\N
1527	pending	Pending			\N
1469	previous_issue	Previous issue			\N
1493	privacy_policy_agreement	I agree to the privacy policy terms			\N
1494	privacy_policy_description	Your information will only be used to respond to your message and will never be shared with third parties.			\N
1542	published_in	Published in			\N
1487	purchase	Purchase			\N
1473	purchase_issue	Purchase Issue			\N
1472	purchase_this_issue_or_subscribe_to_get_full_access_to_all_content	Purchase this issue or subscribe to get full access to all content.			\N
1476	purchase_this_issue_or_subscribe_to_view	Purchase this issue or subscribe to view			\N
1499	quick_links	Quick Links			\N
1539	results_found	results found			\N
1467	scopus	Scopus			\N
1529	search	Search			\N
1530	search_placeholder	Search by title, author or keywords...			\N
1495	send_message	Send Message			\N
1546	show_less	Show Less			\N
1545	show_more	Show More			\N
1532	sort_by	Sort by			\N
1538	sort_most_cited	Most Cited			\N
1537	sort_most_viewed	Most Viewed			\N
1533	sort_newest	Newest First			\N
1534	sort_oldest	Oldest First			\N
1535	sort_title_az	Title (A-Z)			\N
1536	sort_title_za	Title (Z-A)			\N
1525	status	Status			\N
1505	status_accepted	Accepted			\N
1502	status_draft	Draft			\N
1506	status_published	Published			\N
1507	status_rejected	Rejected			\N
1503	status_submitted	Submitted			\N
1504	status_under_review	Under Review			\N
1491	subject	Subject			\N
1508	submission_date	Submission Date			\N
1501	submission_status	Submission Status			\N
1516	subscription_plans	Subscription Plans			\N
1486	toggle_issues	Toggle Issues			\N
1520	upgrade	Upgrade			\N
1511	view_details	View Details			\N
1463	view_subscription_options	View Subscription Options			\N
1512	withdraw_submission	Withdraw Submission			\N
1165	author_information		Muallif ma'lumotlari	Информация об авторе	\N
1160	cannot_change_email		Siz elektron pochtani o'zgartira olmaysiz.	Вы не можете изменить электронную почту.	\N
1112	closed_access		Yopiq kirish	Закрытый доступ	\N
1097	login_with_orcid	Login with ORCID	ORCID orqali kirish	Войти через ORCID	\N
1103	my_purchases	My Purchases	Mening xaridlarim	Мои покупки	\N
1108	welcome	Welcome	Xush kelibsiz	Добро пожаловать	\N
1109	control_info	Here you can manage your information or submit new articles	Bu yerda siz ma'lumotlaringizni boshqarishingiz yoki yangi maqolalar yuborishingiz mumkin	Здесь вы можете управлять своей информацией или подавать новые статьи	\N
1116	edit_article	Edit Article	Maqolani tahrirlash	Редактировать статью	\N
1122	in_process	Under Review	Ko'rib chiqilmoqda	На рассмотрении	\N
1123	accepted	Accepted	Qabul qilingan	Принято	\N
2182	show_password	show_password			1772098242
1125	my_articles_desc	Your submitted articles and their status.	Bu yerda siz maqolalaringizni boshqarishingiz yoki yangi maqolalar yuborishingiz mumkin	Здесь вы можете управлять своими статьями или подавать новые	\N
1147	active_subscription	Active subscription until	Sizning obunangiz faol:	У вас активна подписка до:	\N
1149	subscription_banner_title	Get Full Access	Barcha maqolalarga cheksiz kirish	Получите неограниченный доступ ко всем статьям	\N
1150	subscription_banner_text	Subscribe to get unlimited access to all articles and issues	Barcha maqolalarga, arxivlarga va kelgusi nashrlarni o'qish uchun Philology Matters'ga obuna bo'ling.	Подпишитесь на Philology Matters, чтобы получить полный доступ ко всем статьям, включая архивы и предстоящие публикации.	\N
1177	postal_code	Postal Code	Pochta indeksi	Почтовый индекс	\N
1184	my_payments_desc	View and manage your payment history	To'lovlar tarixi va obuna ma'lumotlari	История платежей и информация о подписке	\N
1278	change_corresponding_author	Change corresponding author	Mas'ul muallifni o'zgartirish	Изменить корреспондентского автора	\N
1283	no_subauthors_added_yet	No subauthors added yet.	Hali hammuallif(lar) qo'shilmagan.	Соавторы еще не добавлены.	\N
1287	keywords_instruction	Enter keywords below. Press Enter or comma after each keyword. Keywords can contain multiple words, e.g. "blended learning" or "linguistic worldview".	Quyida kalit so'zlarni kiriting. Har bir kalit so'zdan keyin Enter yoki vergul bosing. Kalit so'zlar bir nechta so'zni o'z ichiga olishi mumkin, masalan "aralash ta'lim" yoki "lingvistik dunyo manzarasi".	Введите ключевые слова ниже. Нажмите Enter или запятую после каждого ключевого слова. Ключевые слова могут содержать несколько слов, например, "смешанное обучение" или "лингвистическая картина мира".	\N
1292	classification_instruction	Select up to 3 classifications to make it easier for researchers to find your work when it is published.	Ishingiz nashr etilganda tadqiqotchilarga topishini osonlashtirish uchun 3 tagacha tasnifni tanlang.	Выберите до 3 классификаций, чтобы исследователям было легче найти вашу работу при публикации.	\N
1314	complete_author_profile_first	Complete author profile first	Avval muallif profilini to'ldiring	Сначала заполните профиль автора	\N
1316	invalid_orcid_format	Invalid ORCID format. Enter in correct format: 0000-0000-0000-0000	Noto'g'ri ORCID formati. To'g'ri formatda kiriting: 0000-0000-0000-0000	Неверный формат ORCID. Введите в правильном формате: 0000-0000-0000-0000	\N
1324	error_specify_special_issue	Please specify if it is a special issue	Iltimos, maxsus son ekanligini aniqlang	Пожалуйста, укажите, является ли это специальным выпуском	\N
1328	error_address_ethical	Ethical considerations must be addressed	Axloqiy masalalar ko'rib chiqilishi kerak	Этические вопросы должны быть рассмотрены	\N
1331	error_specify_previously_published	Specify if this work has been published elsewhere	Ushbu ish boshqa joyda nashr etilganligini aniqlang	Укажите, была ли эта работа опубликована ранее	\N
1136	delete_confirmation		Qoralama maqolani o'chirish	Удаление черновика статьи	\N
1137	delete_confirmation_text		Siz rostdan ham ushbu qoralama maqolani o'chirmoqchimisiz? Bu harakat qaytarib bo'lmaydi va maqola butunlay o'chiriladi.	Вы уверены, что хотите удалить этот черновик статьи? Это действие нельзя отменить, и статья будет удалена навсегда.	\N
1134	downloads		Yuklab olishlar	Загрузки	\N
1166	edit_author_info		Bu yerda siz muallif ma'lumotlaringizni tahrirlashingiz mumkin	Здесь вы можете редактировать информацию об авторе	\N
1126	no_articles		Siz hali maqola yubormadingiz.	Вы еще не подали ни одной статьи.	\N
1169	orcid_check_text		Iltimos, ORCID bizning ma'lumotlar bazasida mavjudligini tekshiring. Agar xatolikka duch kelsangiz, biz bilan bog'laning	Пожалуйста, проверьте наличие ORCID в нашей базе данных. Если вы столкнулись с ошибками, свяжитесь с нами	\N
1120	rejected		Rad etilgan	Отклонено	\N
1182	save_changes		O'zgarishlarni saqlash	Сохранить изменения	\N
1200	subscription_features	Subscription Benefits	Imkoniyatlar	Возможности	\N
1207	article_downloads	Article Downloads	Maqolalarni yuklab olish	Скачивание статей	\N
1219	delete_payment_text	Are you sure you want to delete this payment? This action cannot be undone.	Siz rostdan ham ushbu to'lovni o'chirmoqchimisiz? Bu harakat qaytarib bo'lmaydi.	Вы уверены, что хотите удалить этот платеж? Это действие нельзя отменить.	\N
1226	copyright_desc	About copyright	Nashriyot qoidalarini tasdiqlash	Подтверждение правил публикации	\N
1230	ethical_standards_desc	About ethical standards	Tadqiqot axloqiy qoidalari	Этические правила исследования	\N
1237	word_count	Word Count	So'zlar soni	Количество слов	\N
1239	authors_information	Authors Information	Mualliflar ma'lumotlari	Информация об авторах	\N
1240	authors_information_desc	About authors	Asosiy va hammuallif ma'lumotlari	Основной автор и соавторы	\N
1242	competing_interests_desc	About competing interests	Moliyaviy yoki boshqa manfaatlar	Финансовые или другие интересы	\N
1247	open_access_editorial	Open Access and Editorial Services	Ochiq kirish va tahririy xizmatlar	Открытый доступ и редакционные услуги	\N
1255	fill_required_field	This field is required.	Majburiy maydonni to'ldiring	Заполните обязательное поле	\N
1665	admin_login	Login	Kirish	Войти	1769045788
1748	admin_btn_search	Search	Qidirish	Поиск	1769048050
1664	admin_logout	Logout	Chiqish	Выйти	1769045788
1663	admin_settings	Settings	Sozlamalar	Настройки	1769045788
1810	admin_status_published	Published	Nashr qilingan	Опубликовано	1769048438
1813	admin_placeholder_user_id	User ID	Foydalanuvchi ID	ID пользователя	1769048438
1256	data_sharing_policy_text	Authors are encouraged to share their research data and include data availability statements in their articles. For further information, see our data sharing policy.	Mualliflar tadqiqot ma'lumotlarini bo'lishishga va maqolalarida ma'lumotlar mavjudligi haqida bayonot kiritishga rag'batlantiriladi. Qo'shimcha ma'lumot uchun ma'lumotlarni bo'lish siyosatimizga qarang.	Авторам рекомендуется делиться исследовательскими данными и включать в свои статьи заявления о доступности данных. Для получения дополнительной информации см. нашу политику обмена данными.	\N
1257	dataset_question	Is there a dataset associated with this submission?	Ushbu maqola bilan bog'liq ma'lumotlar to'plami bormi?	Есть ли набор данных, связанный с этой статьей?	\N
1261	file_upload_requirements_text	The files required for submission to this journal are shown below. You may also submit images, tables, supplementary material and other relevant materials that are in line with the file guidelines.	Ushbu jurnalga yuborish uchun zarur bo'lgan fayllar quyida ko'rsatilgan. Siz shuningdek fayl yo'riqnomalariga mos keladigan rasmlar, jadvallar, qo'shimcha materiallar va boshqa tegishli materiallarni taqdim etishingiz mumkin.	Файлы, необходимые для подачи в этот журнал, показаны ниже. Вы также можете представить изображения, таблицы, дополнительные материалы и другие соответствующие материалы, соответствующие руководящим принципам файлов.	\N
1262	double_blind_review_explanation	Why do I need two versions of my article? The journal operates double-blind peer review, which means your identity is not revealed to reviewers. For this, we need a version of your manuscript without identifying information. We also need a version with author details to expedite publication if your article is accepted.	Nima uchun maqolamning ikki versiyasi kerak? Jurnal ikki tomonlama ko'r-ko'rona ekspert baholashni amalga oshiradi, ya'ni sizning shaxsingiz ekspertlarga oshkor qilinmaydi. Buning uchun bizga sizning qo'lyozmangizning shaxsini aniqlaydigan ma'lumotlarsiz versiyasi kerak. Shuningdek, agar maqolangiz qabul qilinsa, nashr etishni tezlashtirish uchun muallif tafsilotlari bo'lgan versiya ham kerak.	Почему мне нужны две версии моей статьи? Журнал использует двойное слепое рецензирование, что означает, что ваша личность не раскрывается рецензентам. Для этого нам нужна версия вашей рукописи без идентифицирующей информации. Нам также нужна версия с авторскими данными для ускорения публикации, если ваша статья будет принята.	\N
1264	file_without_author_details	File without author details	Muallif tafsilotlarisiz fayl	Файл без данных автора	\N
1267	update_file_without_author_details	Update file (without author details)	Faylni yangilash (muallif tafsilotlarisiz)	Обновить файл (без данных автора)	\N
1270	ethical_standards_text	The files required for submission to this journal are shown below. You may also submit images, tables, supplementary material and other relevant materials that are in line with the file guidelines.	Ushbu jurnal uchun yuborish uchun zarur bo'lgan fayllar quyida ko'rsatilgan. Siz shuningdek fayl yo'riqnomalariga mos keladigan rasmlar, jadvallar, qo'shimcha materiallar va boshqa tegishli materiallarni taqdim etishingiz mumkin.	Файлы, необходимые для подачи в этот журнал, показаны ниже. Вы также можете представить изображения, таблицы, дополнительные материалы и другие соответствующие материалы, соответствующие руководящим принципам файлов.	\N
1271	consent_for_publication_text	I confirm that all individuals who can be identified from the manuscript (for example, in clinical reports) have given written consent to the manuscript and publication, or if they cannot consent themselves or are deceased, their guardians or next of kin have been given the opportunity to review the final statement.	Men qo'lyozmadan aniqlanishi mumkin bo'lgan barcha ishtirokchilar (masalan, klinik hisobotlarda) qo'lyozma va nashr etish uchun yozma rozilik berganini yoki agar ular o'zlari rozilik bera olmasalar yoki vafot etgan bo'lsalar, ularning vasiylarining yoki yaqin qarindoshlarining yakuniy bayonotni ko'rib chiqish imkoniyati berilganini tasdiqlayapman.	Я подтверждаю, что все лица, которые могут быть идентифицированы из рукописи (например, в клинических отчетах), дали письменное согласие на рукопись и публикацию, или если они не могут дать согласие сами или умерли, их опекунам или ближайшим родственникам была предоставлена возможность просмотреть окончательное заявление.	\N
1197	subscription_type		Obuna turi	Тип подписки	\N
1286	competing_interests_text	Do you or any of your co-authors have any relevant financial or non-financial competing interests? Even if you have nothing to declare, you must always include a disclosure statement in your manuscript.	Siz yoki sizning hammuallif(lar)ingizda biron-bir moliyaviy yoki moliyaviy bo'lmagan qarama-qarshi manfaatlar bormi? Agar hech narsa e'lon qilishingiz kerak bo'lmasa ham, siz har doim qo'lyozmangizda oshkor qilish bayonotini kiritishingiz kerak.	Есть ли у вас или у ваших соавторов какие-либо соответствующие финансовые или нефинансовые конкурирующие интересы? Даже если вам нечего заявлять, вы всегда должны включать заявление о раскрытии информации в свою рукопись.	\N
1290	keyword_placeholder	Type a keyword and press Enter / Type them over comma	Kalit so'zni yozing va Enter bosing / Ularni vergul orqali yozing	Введите ключевое слово и нажмите Enter / Введите их через запятую	\N
1669	admin_guest	Guest	Mehmon	Гость	1769045788
1750	admin_users_tariff	Tariff	Tarif	Тариф	1769048050
1751	admin_users_valid_until	Valid until	Amal qilish muddati	Действует до	1769048050
1668	admin_user_or_guest	User	Foydalanuvchi	Пользователь	1769045788
1752	admin_badge_premium	Premium	Premium	Премиум	1769048050
2090	admin_label_for_verified	For verified	Tasdiqlanganlar uchun	Для верифицированных	1769056098
1814	admin_btn_apply	Apply	Qo'llash	Применить	1769048438
2072	admin_label_short_info	Short Description	Qisqa tavsif	Краткое описание	1769055922
1297	open_access_editorial_text	If your article is accepted for publication, you will have the option to publish it as open access. If your manuscript requires significant technical revisions, we will provide information about relevant editorial services. For more details, please refer to the author guidelines.	Agar maqolangiz nashr etish uchun qabul qilinsa, siz uni ochiq kirish sifatida nashr etish imkoniyatiga ega bo'lasiz. Agar qo'lyozmangiz sezilarli texnik qayta ishlashni talab qilsa, biz tegishli tahririy xizmatlar haqida ma'lumot beramiz. Qo'shimcha ma'lumot uchun muallif ko'rsatmalariga qarang.	Если ваша статья принята к публикации, у вас будет возможность опубликовать ее с открытым доступом. Если ваша рукопись требует значительных технических изменений, мы предоставим информацию о соответствующих редакционных услугах. Для получения дополнительной информации, пожалуйста, обратитесь к руководящим принципам для авторов.	\N
1298	open_author_guidelines	Open author guidelines	Muallif ko'rsatmalarini ochish	Открыть руководящие принципы для авторов	\N
1304	jump_to_section	Jump to section	Bo'limga o'tish	Перейти к разделу	\N
1307	author_not_found_message	Could not find author with such ORCID. Add author information please	Bunday ORCID bilan muallif topilmadi. Iltimos, muallif ma'lumotlarini qo'shing	Не удалось найти автора с таким ORCID. Пожалуйста, добавьте информацию об авторе	\N
1312	failed_to_delete_submission	Failed to delete submission	Maqolani o'chirishda xatolik	Ошибка удаления статьи	\N
1318	author_name_too_short	Author name should be at least 2 characters	Muallif ismi kamida 2 ta belgidan iborat bo'lishi kerak	Имя автора должно состоять минимум из 2 символов	\N
1323	error_abstract_too_short	Abstract is too short	Annotatsiya juda qisqa	Аннотация слишком короткая	\N
1326	error_accept_copyright	You must accept the copyright terms	Mualliflik huquqi shartlarini qabul qilishingiz kerak	Вы должны принять условия авторских прав	\N
1330	error_provide_acknowledgments	Please provide acknowledgments	Iltimos, minnatdorchilik bildiring	Пожалуйста, укажите благодарности	\N
1334	error_disclose_competing_interests	Disclose any competing interests	Qarama-qarshi manfaatlarni oshkor qiling	Раскройте конкурирующие интересы	\N
1556	video_guides	video_guides			1752611933
1557	menu_series_masters	menu_series_masters			1752611933
1558	menu_series_phd	menu_series_phd			1752611933
1559	masters_subscription	masters_subscription			1752611933
1560	filters	filters			1752612108
1562	category	category			1752612108
1563	all_categories	all_categories			1752612108
1564	access_type	access_type			1752612108
1565	all_access_types	all_access_types			1752612108
1567	paid_access	paid_access			1752612108
1568	subscription_access	subscription_access			1752612108
1570	clear_filters	clear_filters			1752612108
1571	purchase_issue_confirmation	purchase_issue_confirmation			1752612108
1572	purchase_issue_text	purchase_issue_text			1752612108
1573	price	price			1752612108
1574	confirm_purchase	confirm_purchase			1752612108
1575	processing	processing			1752612108
1576	purchase_created_successfully	purchase_created_successfully			1752612108
1577	purchase_failed	purchase_failed			1752612108
1578	issue_cover	issue_cover			1752612118
1579	access_subscription_or_purchase	access_subscription_or_purchase			1752612118
1581	access_subscription_only	access_subscription_only			1752612118
1582	subscription_only	subscription_only			1752612118
1583	access_purchase_only	access_purchase_only			1752612118
1584	purchase_only	purchase_only			1752612118
1585	all_articles_description	all_articles_description			1752765402
1586	search_articles	search_articles			1752765402
1587	filter_by_issue	filter_by_issue			1752765402
1588	all_issues	all_issues			1752765402
1589	filter_by_volume	filter_by_volume			1752765403
1590	all_volumes	all_volumes			1752765403
1591	filter_by_year	filter_by_year			1752765403
1592	filter_by_access	filter_by_access			1752765403
1593	open_access_filter	open_access_filter			1752765403
1594	paid_access_filter	paid_access_filter			1752765403
1595	subscription_access_filter	subscription_access_filter			1752765403
1596	cited_by	cited_by			1752765403
1597	references	references			1752765403
1598	introduction	introduction			1752765420
1599	outline	outline			1752765420
1601	privacy_policy	privacy_policy			1756567214
1602	search_by_name	search_by_name			1757738543
1603	author_without_orcid	author_without_orcid			1757738543
1604	author_name	author_name			1757738543
1605	create_author	create_author			1757738543
1606	no_purchased_articles	no_purchased_articles			1757738792
1607	subscription_access_all_content	subscription_access_all_content			1757738792
1608	browse_all_issues	browse_all_issues			1757738792
1609	free_plan_info	free_plan_info			1757738792
1610	submission_guidelines_desc	submission_guidelines_desc			1757740033
1611	author_instructions_desc	author_instructions_desc			1757740033
1612	editorial_policy_desc	editorial_policy_desc			1757740033
1614	journal_metrics_desc	journal_metrics_desc			1757740033
1615	editorial_board_desc	editorial_board_desc			1757740033
1616	subscription_guide	subscription_guide			1757740033
1617	subscription_guide_desc	subscription_guide_desc			1757740033
1618	payment_guide_desc	payment_guide_desc			1757740033
1613	aims_scope_desc	Aims and Scope	Maqsad va yo‘nalishlar	Цели и задачи	1757740033
1600	submission_guidelines	Submission Guidelines	Maqolani topshirish bo‘yicha ko‘rsatmalar	Требования к подаче рукописей	1756567214
1619	subscription_benefits	subscription_benefits			1757740033
1561	all_years	all_years	Hammasi		1752612108
1566	free_access	free_access	Bepul kirish		1752612108
1620	subscription_benefits_desc	subscription_benefits_desc			1757740033
1428	about_journal_text	"Philology Matters" electronic scientific-methodological journal is one of the leading academic journals recommended by the Higher Attestation Commission under the Ministry of Higher Education, Science and Innovation of the Republic of Uzbekistan for publishing dissertation results in the fields of 10.00.00 – Philological Sciences and 13.00.00 – Pedagogical Sciences.	“Filologiya masalalari” elektron ilmiy-metodik jurnali Oʻzbekiston Respublikasi Oliy ta'lim, fan va innovatsiyalar vazirligi huzuridagi Oliy attestatsiya komissiyasi tomonidan tavsiya etilgan 10.00.00 – FILOLOGIYA FANLARI; 13.00.00 – PEDAGOGIKA FANLARI yoʻnalishlari boʻyicha dissertatsiya natijalarini chop etish uchun moʻljallangan yetakchi ilmiy jurnallardan biri.	Электронный научно-методический журнал «Вопросы филологии» является одним из ведущих научных изданий, рекомендованных Высшей аттестационной комиссией при Министерстве высшего образования, науки и инноваций Республики Узбекистан для публикации результатов диссертаций по направлениям 10.00.00 – Филологические науки и 13.00.00 – Педагогические науки.	\N
1417	hero_subtitle	Open access	Ochiq foydalanish	Открытый доступ	\N
1372	menu_submit_article	Submit Article	Maqola yuborish	Отправить статью	\N
1429	learn_more_aims	Learn more about aims and goals	Maqsad va vazifalar haqida batafsil ma’lumot oling	Узнать больше о целях и задачах	\N
1433	editor_in_chief	Editor-in-Chief	Bosh muharrir	Главный редактор	\N
1436	editor_affiliation	Doctor of Sciences in Philology, Professor	Filologiya fanlari doktori, professor	Доктор филологических наук, профессор	\N
1431	time_to_first_decision	Time to first decision	Birinchi qarorgacha bo‘lgan vaqt	Срок до первого решения	\N
1414	menu_submit_your_article	Submit your article	Maqolangizni yuboring	Отправьте свою статью	\N
1432	view_all_insights	View all insights	Barcha insaytlarni ko‘rish	Посмотреть все инсайты	\N
1438	latest_published	Latest published	So‘nggi chop etilganlar	Последние публикации	\N
1441	latest_publications_day	Latest publications of the month	Oy davomidagi so‘nggi nashrlar	Последние публикации месяца	\N
1442	view_all_articles	View all articles	Barcha maqolalarni ko‘rish	Посмотреть все статьи	\N
1443	more_from_journal	More from Philology Matters	"Filologiya masalalari" jurnalidan xabarlar	Больше из «Вопросы филологии»	\N
1659	admin_translations	Translations	Tarjimalar	Переводы	1769045788
1661	admin_payments	Payments	To'lovlar	Оплаты	1769045788
1666	admin_role_admin	Administrator	Administrator	Администратор	1769045788
1671	admin_dashboard_title	Dashboard	Boshqaruv paneli	Панель управления	1769047796
1744	admin_users_email_placeholder	Enter email...	Emailni kiriting...	Введите email...	1769048050
1745	admin_users_author_orcid	Author (ORCID)	Muallif (ORCID)	Автор (ORCID)	1769048050
1651	admin_my_assignments	My Assignments	Mening tayinlovlarim	Мои назначения	1769045788
1652	admin_assignments	Assignments	Tayinlovlar	Назначения редакторам	1769045788
1653	admin_content	Website Content	Sayt kontenti	Контент сайта	1769045788
1654	admin_issues	Issues	Nashrlar	Выпуски	1769045788
1655	admin_articles	Articles	Maqolalar	Статьи	1769045788
1656	admin_news	News	Yangiliklar	Новости	1769045788
1657	admin_announcements	Announcements	E'lonlar	Объявления	1769045788
1658	admin_tariffs	Tariffs	Tariflar	Тарифные планы	1769045788
1660	admin_finance	Finance	Moliya	Финансы	1769045788
2056	admin_msg_no_references	No references	Manbalar yo'q	Нет референсов	1769054633
1650	admin_editor_tasks	Editor Tasks	Muharrir vazifalari	Редакторские задачи	1769045788
1746	admin_users_orcid_placeholder	Enter ORCID...	ORCIDni kiriting...	Введите ORCID...	1769048050
1622	sidebar_outline	Outline	Mundarija	Содержание	1769042340
1623	home_news_tab	News	Yangiliklar	Новости	1769042340
1624	home_announcements_tab	Announcements	E'lonlar	Объявления	1769042340
1639	news_last_updated	Latest news and announcements	So'nggi yangiliklar va e'lonlar	Последние новости и объявления	1769042596
1640	footer_doi_value	10.36078	10.36078	10.36078	1769042596
1641	footer_eissn_value	2181-1237	2181-1237	2181-1237	1769042596
1642	admin_home	Home	Bosh sahifa	Главная	1769045788
1643	admin_users	Users	Foydalanuvchilar	Пользователи	1769045788
1649	admin_my_tasks	My Tasks	Mening vazifalarim	Мои задачи	1769045788
1644	admin_authors	Authors	Mualliflar	Авторы	1769045788
1645	admin_editors	Editors	Muharrirlar	Редакторы	1769045788
1647	admin_documents	Documents	Hujjatlar	Документы	1769045788
1648	admin_submission_articles	Submissions	Maqolalar yuborish	Подача статей	1769045788
1646	admin_submissions_section	Submissions	Yuborilganlar	Подачи	1769045788
1741	admin_users_patronymic	Patronymic	Otasining ismi	Отчество	1769048050
1688	admin_login_page_title	Login - FM-Admin	Kirish - FM-Admin	Вход в систему - FM-Admin	1769047871
1694	admin_login_forgot_password	Forgot password?	Parolni unutdingizmi?	Забыли пароль?	1769047871
1816	admin_submissions_col_user	User	Foydalanuvchi	Пользователь	1769048438
1633	stat_2_value	9 days	9 kun	9 дней	1769042596
1634	stat_2_text	Decision after review	Taqrizdan keyingi qaror	Решение после рецензии	1769042596
1701	admin_error_editor_required	Access denied. Editor rights required.	Kirish taqiqlangan. Muharrir huquqlari talab qilinadi.	Доступ запрещен. Требуются права редактора.	1769047940
1702	admin_error_admin_or_editor_required	Access denied. Administrator or Editor rights required.	Kirish taqiqlangan. Administrator yoki Muharrir huquqlari talab qilinadi.	Доступ запрещен. Требуются права администратора или редактора.	1769047940
1703	admin_error_fill_all_fields	Please fill in all fields	Iltimos, barcha maydonlarni to'ldiring	Пожалуйста, заполните все поля	1769047940
1737	admin_users_title	Users	Foydalanuvchilar	Пользователи	1769048050
1738	admin_users_add_btn	Add User	Foydalanuvchi qo'shish	Добавить пользователя	1769048050
1739	admin_users_name	Name	Ism	Имя	1769048050
2096	admin_label_price_rub	Price (RUB)	Narx (RUB)	Цена (₽)	1769056098
1679	admin_stats_total_users	Total Users	Jami foydalanuvchilar	Всего пользователей	1769047796
1682	admin_chart_published_articles_6m	Published Articles (6 months)	Chop etilgan maqolalar (6 oy)	Опубликованные статьи (за 6 месяцев)	1769047796
1680	admin_stats_total_users_desc	Registered users	Ro'yxatdan o'tgan foydalanuvchilar	Зарегистрированных пользователей	1769047796
1681	admin_chart_submissions_by_status	Submissions by Status	Status bo'yicha arizalar	Подачи по статусам	1769047796
1683	admin_recent_submissions	Recent Submissions	So'nggi arizalar	Последние подачи	1769047796
1695	admin_login_show_password	Show password	Parolni ko'rsatish	Показать пароль	1769047871
1689	admin_login_header	Login to Admin Panel	Boshqaruv paneliga kirish	Вход в административную панель	1769047871
1690	admin_login_email_label	Email Address	Email manzil	Email адрес	1769047871
1696	admin_login_remember_me	Remember me on this device	Ushbu qurilmada eslab qolish	Запомнить меня на этом устройстве	1769047871
1704	admin_error_invalid_credentials	Invalid email or password	Noto'g'ri email yoki parol	Неверный email или пароль	1769047940
1705	admin_welcome_body	Welcome	Xush kelibsiz	Добро пожаловать	1769047940
1740	admin_users_surname	Surname	Familiya	Фамилия	1769048050
2057	admin_msg_no_citations	No citations	Iqtiboslar yo'q	Нет цитирований	1769054633
2091	admin_label_per_month	/mo	/oy	/мес	1769056098
2092	admin_title_add_tariff	Add Tariff	Tarif qo'shish	Добавить тариф	1769056098
2093	admin_label_description	Description	Tavsif	Описание	1769056098
1691	admin_login_email_placeholder	your@email.com	sizning@email.com	your@email.com	1769047871
1684	admin_unknown_author	Unknown Author	Noma'lum muallif	Неизвестный автор	1769047796
1692	admin_login_password_label	Password	Parol	Пароль	1769047871
1693	admin_login_password_placeholder	Your password	Sizning parolingiz	Ваш пароль	1769047871
1697	admin_login_no_account	No account?	Hisobingiz yo'qmi?	Нет аккаунта?	1769047871
1685	admin_top_articles	Top Articles by Views	Ko'rishlar bo'yicha eng yaxshi maqolalar	Топ статей по просмотрам	1769047796
1742	admin_users_name_placeholder	Enter name...	Ism kiriting...	Введите имя...	1769048050
1743	admin_users_email	Email	Email	Email	1769048050
2097	admin_label_price_uzs	Price (UZS)	Narx (UZS)	Цена (UZS)	1769056098
1686	admin_views_short	views	ko'rish	просм.	1769047796
1687	admin_chart_published_articles_label	Published Articles	Chop etilgan maqolalar	Опубликованные статьи	1769047796
1698	admin_login_register	Register	Ro'yxatdan o'tish	Зарегистрироваться	1769047871
1706	admin_success_logout	You have successfully logged out	Siz tizimdan muvaffaqiyatli chiqdingiz	Вы успешно вышли из системы	1769047940
2094	admin_label_description_uz	Description (UZ)	Tavsif (UZ)	Описание (UZ)	1769056098
1699	admin_error_no_access	You do not have access to the admin panel	Sizda boshqaruv paneliga kirish huquqi yo'q	У вас нет доступа к административной панели	1769047940
1700	admin_error_admin_required	Access denied. Administrator rights required.	Kirish taqiqlangan. Administrator huquqlari talab qilinadi.	Доступ запрещен. Требуются права администратора.	1769047940
2095	admin_label_description_ru	Description (RU)	Tavsif (RU)	Описание (RU)	1769056098
2098	admin_label_price_usd	Price (USD)	Narx (USD)	Цена ($)	1769056098
2100	admin_title_edit_tariff	Edit Tariff	Tarifni tahrirlash	Редактировать тариф	1769056098
1672	admin_dashboard_subtitle	Overview of statistics and journal activity	Statistika va jurnal faoliyati sharhi	Обзор статистики и активности журнала	1769047796
1674	admin_stats_total_articles_desc	Published articles in the journal	Jurnaldagi chop etilgan maqolalar	Опубликованных статей в журнале	1769047796
1675	admin_stats_active_submissions	Active Submissions	Faol arizalar	Активные подачи	1769047796
1676	admin_stats_active_submissions_desc	Under review	Ko'rib chiqilmoqda	В процессе рассмотрения	1769047796
1677	admin_stats_total_views	Total Views	Jami ko'rishlar	Всего просмотров	1769047796
1678	admin_stats_total_views_desc	Total number of article views	Maqolalarni ko'rishlar soni	Общее количество просмотров статей	1769047796
1758	admin_users_edit_title	Edit User	Foydalanuvchini tahrirlash	Редактирование пользователя	1769048050
1789	admin_authors_edit_title	Edit Author	Muallifni tahrirlash	Редактирование автора	1769048213
1768	admin_users_rules_accepted	Rules accepted at	Qoidalar qabul qilingan vaqt	Время принятия правил	1769048050
2061	admin_label_issue_no	Issue Number	Nashr raqami	Номер выпуска	1769055922
1774	admin_users_sub_end_date	Subscription end date	Obuna tugash sanasi	Дата окончания подписки	1769048050
1662	admin_profile	Profile	Profil	Профиль	1769045788
1667	admin_role_editor	Editor	Muharrir	Редактор	1769045788
1670	admin_not_authorized	Not authorized	Avtorizatsiyadan o'tmagan	Не авторизован	1769045788
1817	admin_submissions_col_title	Title	Nomi	Название	1769048438
2062	admin_placeholder_issue_no	Issue no...	Nashr raqami...	Номер...	1769055922
2063	admin_label_status_published	Published	Nashr qilingan	Опубликован	1769055922
2064	admin_label_status_draft	Draft	Qoralama	В работе	1769055922
1790	admin_authors_organization	Organization	Tashkilot	Организация	1769048213
1769	admin_users_last_online	Last online	Oxirgi onlayn	Последний онлайн	1769048050
1753	admin_badge_regular	Regular	Oddiy	Обычный	1769048050
2065	admin_label_by_subscription	By Subscription	Obuna bo'yicha	По подписке	1769055922
1775	admin_users_new_password_msg	Password for new user:	Yangi foydalanuvchi uchun parol:	Пароль для нового пользователя:	1769048050
1781	admin_option_all	All	Barchasi	Все	1769048213
1761	admin_label_id	ID	ID	ID	1769048050
1621	sidebar_other_pages	Other Pages	Boshqa sahifalar	Другие страницы	1769042340
1762	admin_users_country	Country	Mamlakat	Страна	1769048050
1782	admin_authors_has_articles_yes	Has articles	Maqolalari bor	Есть статьи	1769048213
1760	admin_btn_save	Save	Saqlash	Сохранить	1769048050
1754	admin_btn_edit	Edit	Tahrirlash	Редактировать	1769048050
1783	admin_authors_has_articles_no	No articles	Maqolalari yo'q	Нет статей	1769048213
1759	admin_btn_back	Back	Orqaga	Назад	1769048050
1776	admin_authors_title	Authors	Mualliflar	Авторы	1769048213
1770	admin_users_created_at	Created at	Yaratilgan sana	Дата создания	1769048050
1784	admin_authors_col_name	Author Name	Muallif ismi	Имя автора	1769048213
1785	admin_authors_linked_user	Linked User	Bog'langan foydalanuvchi	Связанный пользователь	1769048213
1771	admin_users_registered_at	Registered at	Ro'yxatdan o'tgan vaqt	Время регистрации	1769048050
1772	admin_tariff_verified_only	(for verified)	(tasdiqlanganlar uchun)	(для верифицированных)	1769048050
1777	admin_authors_search_btn	Find Author	Muallifni topish	Найти автора	1769048213
1778	admin_authors_add_btn	Add Author	Muallif qo'shish	Добавить автора	1769048213
1786	admin_authors_as_main	As Author	Muallif sifatida	Как Автор	1769048213
1773	admin_tariff_verified_hint	Tariffs for verified users are available only after document upload	Tasdiqlangan foydalanuvchilar uchun tariflar faqat hujjatlar yuklanganidan keyin mavjud	Тарифы для верифицированных пользователей доступны только после загрузки документов	1769048050
1763	admin_option_not_selected	Not selected	Tanlanmagan	Не выбрано	1769048050
1779	admin_search_by_full_name	Search by full name	To'liq ism bo'yicha qidirish	Поиск по полному имени	1769048213
1747	admin_btn_clear	Clear	Tozalash	Очистить	1769048050
1787	admin_authors_as_co	As Co-author	Hammuallif sifatida	Как Соавтор	1769048213
2058	admin_issues_title	Issues	Nashrlar	Выпуски	1769055922
1780	admin_authors_has_articles	Has articles	Maqolalari bor	Наличие статей	1769048213
2059	admin_btn_add_issue	Add Issue	Nashr qo'shish	Добавить выпуск	1769055922
1625	home_more_from	More from Philology Matters	Philology Matters'dan ko'proq	Больше от Philology Matters	1769042340
1626	home_submit_title	Submit Paper for Publication	Nashr qilish uchun maqola yuborish	Отправить статью для публикации	1769042340
1755	admin_pagination_showing	Showing	Ko'rsatilmoqda	Показано	1769048050
1756	admin_pagination_of	of	dan	из	1769048050
1764	admin_users_region	Region	Viloyat	Регион	1769048050
1765	admin_users_role	Role	Rol	Роль	1769048050
1766	admin_users_blocked	Blocked	Bloklangan	Заблокирован	1769048050
1788	admin_authors_create_title	Create Author	Muallif yaratish	Создание автора	1769048213
1757	admin_pagination_entries	entries	yozuvlar	записей	1769048050
2060	admin_placeholder_volume	Volume...	Jild...	Том...	1769055922
1767	admin_users_notifications	Notifications	Xabarnomalar	Уведомления	1769048050
1822	admin_label_not_specified	Not specified	Ko'rsatilmagan	Не указан	1769048438
1835	admin_btn_cancel	Cancel	Bekor qilish	Отмена	1769048438
1836	admin_btn_save_changes	Save changes	O'zgarishlarni saqlash	Сохранить изменения	1769048438
1840	admin_btn_back_to_list	Back to list	Ro'yxatga qaytish	Назад к списку	1769048438
1841	admin_section_basic_info	Basic Info	Asosiy ma'lumotlar	Основная информация	1769048438
1832	admin_submissions_edit_title	Edit Submission	Arizani tahrirlash	Редактирование подачи	1769048438
1842	admin_label_abstract	Abstract	Annotatsiya	Аннотация	1769048438
1806	admin_label_status	Status	Holat	Статус	1769048438
1837	admin_js_error_saving	Error saving: 	Saqlashda xatolik: 	Ошибка при сохранении: 	1769048438
1843	admin_label_keywords	Keywords	Kalit so'zlar	Ключевые слова	1769048438
1807	admin_option_all_statuses	All Statuses	Barcha holatlar	Все статусы	1769048438
2066	admin_label_free	Free	Bepul	Бесплатно	1769055922
2067	admin_btn_show_all_articles	Show all articles	Barcha maqolalarni ko'rsatish	Показать все статьи	1769055922
1838	admin_js_error_request	Error sending request	So'rov yuborishda xatolik	Ошибка при отправке запроса	1769048438
1844	admin_label_word_count	Word Count	So'zlar soni	Количество слов	1769048438
1812	admin_label_user_id	User ID	Foydalanuvchi ID	Пользователь ID	1769048438
1800	admin_option_not_selected_m	Not selected	Tanlanmagan	Не выбран	1769048213
1801	admin_authors_search_user_title	Find User	Foydalanuvchini topish	Найти пользователя	1769048213
1803	admin_js_search_user_not_found	User with this email not found in the list	Ushbu emailga ega foydalanuvchi ro'yxatda topilmadi	Пользователь с таким email не найден в списке доступных пользователей	1769048213
1804	admin_submissions_title	Article Submissions	Maqola topshirish	Подача статей	1769048438
1808	admin_status_draft	Draft	Qoralama	Черновик	1769048438
1815	admin_btn_reset	Reset	Tozalash	Сбросить	1769048438
1809	admin_status_in_process	In Process	Jarayonda	В процессе	1769048438
1818	admin_submissions_col_author	Main Author	Asosiy muallif	Основной автор	1769048438
1819	admin_submissions_col_date	Created Date	Yaratilgan sana	Дата создания	1769048438
1820	admin_submissions_col_review_status	Review Status	Tekshirish holati	Статус проверки	1769048438
2073	admin_label_short_info_uz	Short Description (UZ)	Qisqa tavsif (UZ)	Краткое описание (узб)	1769055922
2074	admin_label_short_info_ru	Short Description (RU)	Qisqa tavsif (RU)	Краткое описание (рус)	1769055922
2075	admin_label_subscription_enabled	Subscription enabled	Obuna yoqilgan	Подписка включена	1769055922
1749	admin_users_subscription	Subscription	Obuna	Подписка	1769048050
1792	admin_authors_city	City	Shahar	Город	1769048213
1793	admin_authors_street	Street	Ko'cha	Улица	1769048213
1794	admin_authors_zip	Zip Code	Pochta indeksi	Почтовый индекс	1769048213
1799	admin_label_user	User	Foydalanuvchi	Пользователь	1769048213
1833	admin_label_notes	Notes	Eslatmalar	Заметки	1769048438
1834	admin_placeholder_notes	Submission notes	Ariza bo'yicha eslatmalar	Заметки к подаче	1769048438
2068	admin_title_create_issue	Create Issue	Nashr yaratish	Создание выпуска	1769055922
2069	admin_title_edit_issue	Edit Issue	Nashrni tahrirlash	Редактирование выпуска	1769055922
2070	admin_label_year	Year	Yil	Год	1769055922
2071	admin_label_category	Category	Kategoriya	Категория	1769055922
1823	admin_label_no_title	No title	Nomsiz	Без названия	1769048438
1824	admin_review_status_not_assigned	Not assigned	Tayinlanmagan	Не назначено	1769048438
1825	admin_review_status_assigned	Assigned	Tayinlangan	Назначено	1769048438
1839	admin_submissions_detail_title	Submission #	Ariza #	Подача статьи #	1769048438
1845	admin_section_admin_response	Administration Response	Ma'muriyat javobi	Ответ администрации	1769048438
1811	admin_status_rejected	Rejected	Rad etilgan	Отклонено	1769048438
1821	admin_col_actions	Actions	Amallar	Действия	1769048438
1791	admin_authors_position	Position	Lavozim	Должность	1769048213
1805	admin_filter_title	Filters	Filtrlar	Фильтры	1769048438
1826	admin_review_status_in_review	In review	Tekshiruvda	На проверке	1769048438
1827	admin_review_status_reviewed	Reviewed	Tekshirildi	Проверено	1769048438
1828	admin_review_status_approved	Approved	Tasdiqlandi	Одобрено	1769048438
1829	admin_review_status_rejected	Rejected	Rad etildi	Отклонено	1769048438
1830	admin_btn_view	View	Ko'rish	Просмотр	1769048438
1831	admin_btn_assign_editors	Assign editors	Muharrirlarni tayinlash	Назначить редакторов	1769048438
1795	admin_authors_phone	Phone	Telefon	Телефон	1769048213
1796	admin_label_orcid	ORCID	ORCID	ORCID	1769048213
1797	admin_authors_department	Department	Bo'lim	Отдел	1769048213
1798	admin_authors_updated_at	Updated at	Yangilangan sana	Дата обновления	1769048213
1898	admin_col_reviewed_at	Reviewed	Tekshirilgan	Проверено	1769048700
1899	admin_msg_article_not_found	Article not found	Maqola topilmadi	Статья не найдена	1769048700
1900	admin_msg_no_assignments	No assignments	Tayinlovlar yo'q	Нет назначений	1769048700
1860	admin_label_main_author	Main Author	Asosiy muallif	Основной автор	1769048438
1861	admin_label_co_authors	Co-authors	Hammualliflar	Соавторы	1769048439
1862	admin_authors_not_specified	Authors not specified	Mualliflar ko'rsatilmagan	Авторы не указаны	1769048439
1863	admin_section_files	Files	Fayllar	Файлы	1769048439
1856	admin_prop_competing_interests	Competing Interests	Manfaatlar to'qnashuvi	Конкурирующие интересы	1769048438
1857	admin_section_dates	Dates	Sanalar	Даты	1769048438
1858	admin_section_submission_author	Submission Author	Ariza muallifi	Автор подачи	1769048438
1859	admin_section_article_authors	Article Authors	Maqola mualliflari	Авторы статьи	1769048438
1875	admin_col_file	File	Fayl	Файл	1769048439
1876	admin_tooltip_download_file	Download file	Faylni yuklab olish	Скачать файл	1769048439
1877	admin_label_no_file	No file	Fayl yo'q	Нет файла	1769048439
1878	admin_documents_edit_title	Edit Document	Hujjatni tahrirlash	Редактирование документа	1769048439
1879	admin_editors_title	Editors	Muharrirlar	Редакторы	1769048700
1880	admin_btn_add_editor	Add Editor	Muharrir qo'shish	Добавить редактора	1769048700
1881	admin_label_specialization	Specialization	Ixtisoslik	Специализация	1769048700
1882	admin_placeholder_specialization	Enter specialization...	Ixtisoslikni kiriting...	Введите специализацию...	1769048700
1883	admin_col_stats	Statistics	Statistika	Статистика	1769048700
1884	admin_stats_pending	Pending: 	Kutilmoqda: 	Ожидает: 	1769048700
1885	admin_stats_reviewed	Reviewed: 	Tekshirildi: 	Проверено: 	1769048700
1886	admin_stats_rejected	Rejected: 	Rad etildi: 	Отклонено: 	1769048700
1887	admin_editor_new_title	New Editor	Yangi muharrir	Новый редактор	1769048700
1888	admin_editor_spec_not_specified	Specialization not specified	Ixtisoslik ko'rsatilmagan	Специализация не указана	1769048700
1889	admin_label_password	Password	Parol	Пароль	1769048700
1890	admin_hint_auto_password	Automatically generated password	Avtomatik yaratilgan parol	Автоматически сгенерированный пароль	1769048700
1891	admin_btn_create_editor	Create Editor	Muharrir yaratish	Создать редактора	1769048700
1892	admin_stats_total_assignments	Total assignments	Jami tayinlovlar	Всего назначений	1769048700
2076	admin_label_is_paid_issue	Paid issue	Pullik nashr	Платный выпуск	1769055922
2077	admin_label_cover	Cover	Muqova	Обложка	1769055922
2078	admin_label_publication_date	Publication Date	Nashr sanasi	Дата публикации	1769055922
2101	admin_title_delete_tariff	Delete Tariff	Tarifni o'chirish	Удалить тариф	1769056098
1897	admin_col_assigned_at	Assigned	Tayinlangan	Назначено	1769048700
2183	hide_password	hide_password			1772098242
1893	admin_stats_pending_assignments	Pending review	Tekshiruv kutilmoqda	Ожидает проверки	1769048700
2102	admin_label_warning	Warning!	Diqqat!	Внимание!	1769056098
1846	admin_label_admin_notes	Admin Notes	Ma'muriyat eslatmalari	Заметки администрации	1769048438
1847	admin_section_extra_properties	Extra Properties	Qo'shimcha xususiyatlar	Дополнительные свойства	1769048438
1848	admin_prop_special	Special Article	Maxsus maqola	Специальная статья	1769048438
1849	admin_prop_dataset	Dataset	Ma'lumotlar to'plami	Набор данных	1769048438
1855	admin_prop_corr_author	Corresponding Author	Mas'ul muallif	Корреспондирующий автор	1769048438
1864	admin_file_authors	Authors File	Mualliflar fayli	Файл с авторами	1769048439
1865	admin_file_anonymized	Anonymized File	Anonimlashtirilgan fayl	Анонимизированный файл	1769048439
1866	admin_files_not_uploaded	Files not uploaded	Fayllar yuklanmagan	Файлы не загружены	1769048439
1850	admin_prop_copyright_check	Copyright Check	Mualliflik huquqini tekshirish	Проверка авторских прав	1769048438
1867	admin_user_not_found_msg	User not found (ID: 	Foydalanuvchi topilmadi (ID: 	Пользователь не найден (ID: 	1769048439
1868	admin_documents_title	Documents	Hujjatlar	Документы	1769048439
1869	admin_label_verification_status	Verification Status	Tekshirish holati	Статус верификации	1769048439
1870	admin_verification_pending	Pending	Kutilmoqda	Ожидает	1769048439
1871	admin_verification_verified	Verified	Tasdiqlangan	Проверено	1769048439
1872	admin_verification_rejected	Rejected	Rad etilgan	Отклонено	1769048439
1873	admin_label_work_title	Work Title	Ish nomi	Название работы	1769048439
1874	admin_placeholder_search_title	Search by title	Nomi bo'yicha qidirish	Поиск по названию	1769048439
1894	admin_label_articles_count	Articles Count	Maqolalar soni	Количество статей	1769048700
1895	admin_section_editor_assignments	Editor Assignments	Muharrir tayinlovlari	Назначения редактора	1769048700
1896	admin_col_article	Article	Maqola	Статья	1769048700
1852	admin_prop_consent_obtained	Consent Obtained	Rozilik olingan	Согласие получено	1769048438
1853	admin_prop_acknowledgements	Acknowledgements	Minnatdorchilik	Благодарности	1769048438
1854	admin_prop_prior_works	Used Prior Works	Oldingi ishlar ishlatilgan	Использованы предыдущие работы	1769048438
1851	admin_prop_ethical_check	Ethical Check	Axloqiy tekshirish	Этическая проверка	1769048438
1945	admin_filter_all_status	admin_filter_all_status	admin_filter_all_status	admin_filter_all_status	1769052818
1946	admin_users_id_placeholder	admin_users_id_placeholder	admin_users_id_placeholder	admin_users_id_placeholder	1769052818
1921	admin_option_all_editors	All Editors	Barcha muharrirlar	Все редакторы	1769048700
1922	admin_label_submission_id	Submission ID	Ariza ID	ID статьи	1769048700
1923	admin_label_submission_title	Submission Title	Ariza nomi	Название статьи	1769048700
1926	admin_review_title_view	View Review	Tekshiruvni ko'rish	Просмотр проверки	1769048700
1927	admin_btn_back_to_assignments	Back to Assignments	Tayinlovlarga qaytish	Назад к назначениям	1769048700
1928	admin_section_your_review	Your Review	Sizning tekshiruvingiz	Ваша проверка	1769048700
1929	admin_label_decision	Decision	Qaror	Решение	1769048700
1930	admin_decision_approve	Approve	Ma'qullash	Одобрить	1769048700
1931	admin_decision_reject	Reject	Rad etish	Отклонить	1769048700
1933	admin_placeholder_comment	Comment on status change	Holatni o'zgartirish bo'yicha izoh	Комментарий к изменению статуса	1769048700
1934	admin_hint_comment	Describe your opinion, comments, and recommendations	Maqola bo'yicha fikringiz, izoh va tavsiyalarni yozing	Опишите ваше мнение о статье, замечания и рекомендации для автора	1769048700
1935	admin_label_attach_file	Attach File	Fayl biriktirish	Прикрепить файл	1769048700
1936	admin_hint_attach_file	You can attach a file with detailed comments (PDF, DOC, DOCX, TXT)	Batafsil izohlar bilan fayl biriktirishingiz mumkin (PDF, DOC, DOCX, TXT)	Вы можете прикрепить файл с подробными замечаниями (PDF, DOC, DOCX, TXT)	1769048700
1937	admin_label_current_file	Current File	Joriy fayl	Текущий файл	1769048700
1938	admin_btn_save_review	Save Review	Tekshiruvni saqlash	Сохранить проверку	1769048700
1906	admin_btn_back_to_submissions	Back to submissions	Arizalar bo'limiga qaytish	Назад к подачам	1769048700
1939	admin_section_review_result	Review Result	Tekshiruv natijasi	Результат проверки	1769048700
1940	admin_label_reviewed_at	Reviewed at	Tekshirilgan vaqt	Дата проверки	1769048700
1942	admin_section_assignment_details	Assignment Details	Tayinlov tafsilotlari	Детали назначения	1769048700
1943	admin_label_assignment_id	Assignment ID	Tayinlov ID	ID назначения	1769048700
1944	admin_label_assigned_at	Assigned at	Tayinlangan vaqt	Дата назначения	1769048700
1947	admin_announcements_title	Announcements	E'lonlar	Объявления	1769054342
1948	admin_btn_add_announcement	Add Announcement	E'lon qo'shish	Добавить объявление	1769054342
1949	admin_announcement_title_col	Announcement Title	E'lon nomi	Название объявления	1769054342
1950	admin_announcement_published_at	Published At	Nashr qilingan sana	Дата публикации	1769054342
1951	admin_announcement_create_title	Create Announcement	E'lon yaratish	Создание объявления	1769054342
1952	admin_announcement_edit_title	Edit Announcement	E'lonni tahrirlash	Редактирование объявления	1769054342
2106	admin_msg_error_delete_tariff	Error deleting tariff	Tarifni o'chirishda xatolik yuz berdi	Ошибка удаления тарифа	1769056098
1932	admin_label_comment	Comment	Izoh	Комментарий	1769048700
1802	admin_js_search_user_prompt	Enter user email to search:	Qidirish uchun foydalanuvchi emailini kiriting:	Введите email пользователя для поиска:	1769048213
1902	admin_editor_edit_title	Edit Editor	Muharrirni tahrirlash	Редактирование редактора	1769048700
1904	admin_placeholder_specialization_examples	e.g. Mathematics, Physics, Chemistry	masalan: Matematika, Fizika, Kimyo	Например: Математика, Физика, Химия	1769048700
1905	admin_assign_editors_title	Assign Editors	Muharrirlarni tayinlash	Назначение редакторов	1769048700
1908	admin_badge_already_assigned	Already assigned	Allaqachon tayinlangan	Уже назначен	1769048700
1909	admin_msg_no_editors_found	No editors found	Muharrirlar topilmadi	Редакторы не найдены	1769048700
1910	admin_msg_no_editors_desc	No registered editors in the system yet.	Tizimda hali ro'yxatdan o'tgan muharrirlar yo'q.	В системе пока нет зарегистрированных редакторов.	1769048700
1917	admin_title_assigned_editors	Assigned Editors	Tayinlangan muharrirlar	Уже назначенные редакторы	1769048700
1918	admin_my_assignments_title	My Assignments	Mening tayinlovlarim	Мои назначения	1769048700
1919	admin_editor_assignments_title	Editor Assignments	Muharrir tayinlovlari	Назначения редакторам	1769048700
1920	admin_label_editor	Editor	Muharrir	Редактор	1769048700
1924	admin_msg_editor_not_found	Editor not found	Muharrir topilmadi	Редактор не найден	1769048700
1925	admin_review_title_pending	Review Article	Maqolani tekshirish	Проверка статьи	1769048700
1941	admin_label_attached_file	Attached File	Biriktirilgan fayl	Прикрепленный файл	1769048700
1911	admin_btn_assign_selected	Assign Selected	Tanlanganlarni tayinlash	Назначить выбранных редакторов	1769048700
1912	admin_section_article_info	Article Info	Maqola haqida ma'lumot	Информация о статье	1769048700
1913	admin_label_title	Title	Nomi	Название	1769048700
1914	admin_label_submitted_at	Submitted at	Topshirilgan vaqti	Дата подачи	1769048700
1915	admin_label_anonymized_file	Anonymized File	Anonimlashtirilgan fayl	Анонимный файл	1769048700
1916	admin_btn_download	Download	Yuklab olish	Скачать	1769048700
1907	admin_title_select_editors	Select Editors	Muharrirlarni tanlang	Выберите редакторов	1769048700
1983	admin_section_article_basic_info	Basic Information	Asosiy ma'mulotlar	Основная информация	1769054444
1990	admin_label_subscription_enable	Subscription Enabled	Obuna yoqilgan	Подписка включена	1769054444
1991	admin_label_is_paid	Paid Article	Pullik maqola	Платная статья	1769054444
1992	admin_label_price	Price	Narxi	Цена	1769054444
1993	admin_section_content_blocks	Content Blocks	Kontent bloklari	Блоки контента	1769054444
1994	admin_btn_add_block	Add Block	Blok qo'shish	Добавить блок	1769054444
1997	admin_btn_add_reference	Add Reference	Manba qo'shish	Добавить референс	1769054444
1998	admin_btn_add_citation	Add Citation	Iqtibos qo'shish	Добавить цитирование	1769054444
1954	admin_label_title_en	Title (EN)	Sarlavha (EN)	Название (en)	1769054342
1955	admin_label_title_ru	Title (ru)	Nomi (ru)	Название (ru)	1769054342
1956	admin_label_title_uz	Title (uz)	Nomi (uz)	Название (uz)	1769054342
1958	admin_label_content_ru	Content (RU)	Kontent (RU)	Контент (ru)	1769054342
2103	admin_msg_delete_tariff_warning	When deleting the tariff {name}, all users using this tariff will be moved to normal mode (no tariff).	{name} tarifini o'chirib tashlaganingizda, ushbu tarifdan foydalanadigan barcha foydalanuvchilar oddiy rejimga (tarifsiz) o'tkaziladi.	При удалении тарифа {name} все пользователи, использующие этот тариф, будут переведены на обычный режим (без тарифа).	1769056098
2104	admin_msg_confirm_delete_tariff	Are you sure you want to delete this tariff?	Haqiqatan ham ushbu tarifni o'chirib tashlamoqchimisiz?	Вы уверены, что хотите удалить этот тариф?	1769056098
2105	admin_btn_delete_tariff	Delete Tariff	Tarifni o'chirish	Удалить тариф	1769056098
1965	admin_source_type_electronic_journal_article	Electronic Journal Article	Elektron ilmiy jurnaldagi maqola	Статья в электронном научном журнале	1769054444
1953	admin_label_all	All	Barchasi	Все	1769054342
1967	admin_source_type_electronic_magazine_article	Electronic Magazine/Newspaper Article	Elektron jurnal/gazetadagi maqola	Статья в электронном журнале/газете	1769054444
1968	admin_source_type_blog	Blog/Blog Comments	Blog/Blogdagi kommentlar	Блог/Комментарии в блоге	1769054444
1969	admin_source_type_book_chapter	Edited Book Chapters / Reference Entries	Tahrir qilingan kitob boblari va ma’lumotnomalardagi maqolalar	Главы редактируемых книг и статьи в справочниках	1769054444
1957	admin_label_content_en	Content (EN)	Kontent (EN)	Контент (en)	1769054342
1970	admin_source_type_online_dictionary	Online Dictionary	Onlayn lug'at	Онлайн-словарь	1769054444
1971	admin_source_type_print_dictionary	Print Dictionary	Bosma lug'at	Печатный словарь	1769054444
1972	admin_source_type_conference	Conference Presentations and Materials	Konferensiya taqdimotlari va materiallari	Презентации и материалы конференций	1769054444
1964	admin_source_type_journal_article	Print Journal Article	Bosma ilmiy jurnaldagi maqola	Статья в печатном научном журнале	1769054444
1973	admin_source_type_online_conference	Online Conference Presentations and Materials	Onlayn konferensiya taqdimotlari va materiallari	Презентации и материалы онлайн-конференций	1769054444
1966	admin_source_type_magazine_article	Magazine/Newspaper Article	Jurnal/Gazetadagi maqola	Статья в журнале/газете	1769054444
1974	admin_source_type_thesis	Published Dissertation or Thesis	Nashr etilgan dissertatsiya yoki tezis manbalari	Опубликованные диссертации или тезисы	1769054444
1975	admin_articles_title	Articles	Maqolalar	Статьи	1769054444
1976	admin_btn_add_article	Add Article	Maqola qo'shish	Добавить статью	1769054444
1977	admin_label_article_title	Article Title	Maqola nomi	Название статьи	1769054444
1978	admin_label_author	Author	Muallif	Автор	1769054444
1979	admin_label_search_by_full_name	Search by full name	To'liq ism bo'yicha qidirish	Поиск по полному имени	1769054444
1980	admin_label_issue	Issue	Nashr	Выпуск	1769054444
1981	admin_label_all_issues	All Issues	Barcha nashrlar	Все выпуски	1769054444
1982	admin_btn_content	Content	Tarkib	Содержание	1769054444
1984	admin_label_subauthors	Co-authors	Hammualliflar	Соавторы	1769054444
1985	admin_label_additional_info	Additional Information	Qo'shimcha ma'lumotlar	Дополнительная информация	1769054444
1986	admin_label_date_sent	Date Sent	Yuborilgan sana	Дата отправки	1769054444
1987	admin_label_date_accept	Date Accepted	Qabul qilingan sana	Дата принятия	1769054444
1988	admin_label_pdf_files	PDF Files	PDF fayllar	PDF файлы	1769054444
1989	admin_hint_pdf_upload	Select PDF files to upload. You can select multiple files.	Yuklash uchun PDF-fayllarni tanlang. Bir nechta faylni tanlashingiz mumkin.	Выберите PDF файлы для загрузки. Можно выбрать несколько файлов.	1769054444
1995	admin_col_order	Order	Tartib	Порядок	1769054444
1996	admin_col_type	Type	Turi	Тип	1769054444
1959	admin_label_content_uz	Content (UZ)	Kontent (UZ)		1769054342
1960	admin_label_cover_image	Cover Image (upload)	Muqova rasmi (yuklash)	Обложка (загрузить)	1769054342
1962	admin_source_type_edited_book	Edited Books	Tahrir ostidagi bosma/elektron kitoblar	Редактируемые книги	1769054444
1963	admin_source_type_coauthored_book	Co-authored Books	Hammualliflikdagi bosma/elektron kitoblar	Книги в соавторстве	1769054444
2030	admin_label_publisher	Publisher	Nashriyot	Издательство	1769054520
2032	admin_label_volume	Volume	Jild	Том	1769054520
2018	admin_placeholder_orcid	Enter ORCID...	ORCID kiriting...	Введите ORCID...	1769054520
2019	admin_label_article	Article	Maqola	Статья	1769054520
2020	admin_label_references	References	Manbalar	Референсы	1769054520
2021	admin_label_citations	Citations	Iqtiboslar	Цитирования	1769054520
2023	admin_hint_keywords_sep	Enter keywords separated by commas	Kalit so'zlarni vergul bilan ajratib kiriting	Введите ключевые слова через запятую	1769054520
2024	admin_label_created_at	Created At	Yaratilgan vaqti	Дата создания	1769054520
2026	admin_label_chapter_title	Chapter Title	Bob nomi	Название главы	1769054520
2027	admin_label_word_term	Word/Term	So'z/Atama	Слово/Термин	1769054520
2028	admin_label_thesis_type	Thesis Type	Dissertatsiya turi	Тип диссертации	1769054520
2029	admin_label_source_title	Source Title	Manba nomi	Название источника	1769054520
2033	admin_label_edition	Edition	Nashr	Издание	1769054520
2034	admin_label_page_start	Page Start	Bosh sahifa	Начальная страница	1769054520
2035	admin_label_page_end	Page End	Oxirgi sahifa	Конечная страница	1769054520
2036	admin_label_conference_country	Conference Country	Konferensiya mamlakati	Страна конференции	1769054520
2037	admin_label_conference_city	Conference City	Konferensiya shahri	Город конференции	1769054520
2038	admin_label_defense_place	Defense Place	Himoya joyi	Место защиты	1769054520
2012	admin_msg_no_content_blocks	No content blocks	Kontent bloklari yo'q	Нет блоков контента	1769054444
2013	admin_tooltip_up	Up	Yuqoriga	Вверх	1769054444
2014	admin_tooltip_down	Down	Pastga	Вниз	1769054444
2015	admin_label_not_selected	Not selected	Tanlanmagan	Не выбран	1769054520
2016	admin_placeholder_article_title	Enter title...	Sarlavhani kiriting...	Введите название...	1769054520
2017	admin_placeholder_author_name	Enter author name...	Muallif ismini kiriting...	Введите имя автора...	1769054520
2022	admin_placeholder_keywords_sep	Separate with commas	Vergullar bilan ajrating	Разделите запятыми	1769054520
2025	admin_label_organization_name	Organization Name	Tashkilot nomi	Название организации	1769054520
2031	admin_label_publication_place	Publication Place	Nashr joyi	Место издания	1769054520
2039	admin_label_university	University	Universitet	Университет	1769054520
2040	admin_label_access_date	Access Date	Murojaat sanasi	Дата обращения	1769054520
2046	admin_label_current_files	Current files	Joriy fayllar	Текущие файлы	1769054633
2047	admin_msg_author_already_added	This author is already added to the co-authors list	Ushbu muallif allaqachon hammualliflar ro'yxatiga qo'shilgan	Этот автор уже добавлен в список соавторов	1769054633
2048	admin_msg_title_required	Title is required	Sarlavha kiritilishi shart	Название обязательно	1769054633
2049	admin_msg_error_add	Error adding	Qo'shishda xatolik	Ошибка добавления	1769054633
2050	admin_msg_error_delete	Error deleting	O'chirishda xatolik	Ошибка удаления	1769054633
2051	admin_msg_error_save	Error saving	Saqlashda xatolik	Ошибка сохранения	1769054633
2052	admin_msg_unknown_error	Unknown error	Nomalum xatolik	Неизвестная ошибка	1769054633
2053	admin_label_text	Text	Matn	Текст	1769054633
2054	admin_label_image	Image	Rasm	Изображение	1769054633
2055	admin_label_table	Table	Jadval	Таблица	1769054633
2079	admin_news_title	News	Yangiliklar	Новости	1769056010
2080	admin_label_status_archived	Archived	Arxivlangan	Архив	1769056010
2081	admin_title_create_news	Create News	Yangilik yaratish	Создание новости	1769056010
2011	admin_msg_searching	Searching...	Qidirilmoqda...	Поиск...	1769054444
2082	admin_title_edit_news	Edit News	Yangilikni tahrirlash	Редактирование новости	1769056010
2083	admin_label_upload_cover	Upload Cover	Muqova yuklash	Обложка (загрузить)	1769056010
2084	admin_tariffs_title	Tariffs	Tariflar	Тарифы	1769056098
2085	admin_btn_add_tariff	Add Tariff	Tarif qo'shish	Добавить тариф	1769056098
2086	admin_label_amount_rub	Amount (RUB)	Summa (RUB)	Сумма (₽)	1769056098
2087	admin_label_amount_uzs	Amount (UZS)	Summa (UZS)	Summa (UZS)	1769056098
2088	admin_label_amount_usd	Amount (USD)	Summa (USD)	Сумма ($)	1769056098
2089	admin_label_default	Default	Standart	По умолчанию	1769056098
2008	admin_placeholder_search_ref	Enter title or author...	Sarlavha yoki muallifni kiriting...	Введите название или автора...	1769054444
2184	dashboard	dashboard			1772103684
2185	menu	menu			1772103684
2186	other	other			1772103684
2009	admin_label_add_new_ref	Add new reference to article	Maqolaga yangi manba qo'shish	Добавить новый референс к статье	1769054444
1999	admin_modal_block_title	Content Block	Kontent bloki	Блок контента	1769054444
2006	admin_modal_insert_ref_title	Insert Reference Link	Manbaga havola qo'shish	Вставка ссылки на референс	1769054444
2007	admin_label_search_ref	Reference Search	Manba qidirish	Поиск референса	1769054444
2000	admin_label_block_type	Block Type	Blok turi	Тип блока	1769054444
2001	admin_label_block_title	Block Title	Blok nomi	Название блока	1769054444
2003	admin_btn_insert_ref	Insert reference link	Manbaga havola qo'shish	Вставить ссылку на референс	1769054444
2004	admin_label_image_desc	Image Description	Rasm tavsifi	Описание изображения	1769054444
2005	admin_label_table_input	Table (insert HTML or text)	Jadval (HTML yoki matn kiriting)	Таблица (вставьте HTML или текст)	1769054444
2118	admin_msg_sync_success	Translations successfully synchronized with mainweb	Tarjimalar mainweb bilan muvaffaqiyatli sinxronlandi	Переводы успешно синхронизированы с mainweb	1769056197
2123	admin_payments_title	Payments	To'lovlar	Оплаты	1769056353
2129	admin_msg_error_saving	Error saving	Saqlashda xatolik yuz berdi	Ошибка при сохранении	1769056353
2130	admin_msg_request_error	Request error	So'rovda xatolik yuz berdi	Ошибка при отправке запроса	1769056353
2141	admin_author_search_title	Author Search	Muallifni qidirish	Поиск автора	1769056635
2142	admin_label_search_method	Search method	Qidirish usuli	Способ поиска	1769056635
2145	admin_label_author_orcid	Author ORCID	Muallif ORCID	ORCID автора	1769056635
2146	admin_label_author_without_orcid	Author without ORCID	ORCID'siz muallif	Автор без ORCID	1769056635
1901	admin_msg_no_assignments_desc	This editor has no assigned articles yet.	Ushbu muharrirga hali maqolalar tayinlanmagan.	Этому редактору пока не назначены статьи для проверки.	1769048700
1903	admin_hint_specialization	Specify the editor's area of scientific interest	Muharrirning ilmiy qiziqish sohasini ko'rsating	Укажите область научных интересов редактора	1769048700
1961	admin_source_type_book	Print/Electronic Books	Bosma/Elektron kitoblar	Печатные/Электронные книги	1769054444
2010	admin_msg_search_prompt	Enter a query to search for references	Manbalarni qidirish uchun so'rov kiriting	Введите запрос для поиска референсов	1769054444
2107	admin_translations_title	Translations	Tarjimalar	Переводы	1769056197
2108	admin_btn_sync_translations	Sync with mainweb	Mainweb bilan sinxronlash	Синхронизировать с mainweb	1769056197
2109	admin_msg_synchronizing	Synchronizing...	Sinxronlanmoqda...	Синхронизация...	1769056197
2111	admin_placeholder_search_translations	Search by text or alias...	Matn yoki alias bo'yicha qidirish...	Поиск по тексту или алиасу...	1769056197
2112	admin_btn_find	Find	Topish	Найти	1769056197
2113	admin_label_alias	Alias	Alias	Алиас	1769056197
2114	admin_label_uzbek	Uzbek	O'zbekcha	Узбекский	1769056197
2115	admin_label_russian	Russian	Ruscha	Русский	1769056197
2119	admin_msg_sync_error	Synchronization error	Sinxronlashda xatolik yuz berdi	Ошибка синхронизации	1769056197
2131	admin_btn_add	admin_btn_add	admin_btn_add	admin_btn_add	1769056524
2132	admin_stats_published	admin_stats_published	admin_stats_published	admin_stats_published	1769056526
2133	admin_label_filters	admin_label_filters	admin_label_filters	admin_label_filters	1769056532
2134	admin_label_status_pending	admin_label_status_pending	admin_label_status_pending	admin_label_status_pending	1769056532
2135	admin_label_status_paid	admin_label_status_paid	admin_label_status_paid	admin_label_status_paid	1769056532
2136	admin_label_status_rejected	admin_label_status_rejected	admin_label_status_rejected	admin_label_status_rejected	1769056532
2137	admin_label_amount	admin_label_amount	admin_label_amount	admin_label_amount	1769056532
2138	admin_label_updated_at	admin_label_updated_at	admin_label_updated_at	admin_label_updated_at	1769056532
2139	admin_label_file	admin_label_file	admin_label_file	admin_label_file	1769056532
2140	admin_label_actions	admin_label_actions	admin_label_actions	admin_label_actions	1769056532
2120	admin_label_error	Error			1769056197
2124	admin_label_all_statuses	All statuses	Barcha holatlar	Все статусы	1769056353
2125	admin_msg_no_file	No file	Fayl yo'q	Нет файла	1769056353
2126	admin_title_edit_payment	Edit Payment	To'lovni tahrirlash	Редактирование платежа	1769056353
2143	admin_label_by_orcid	By ORCID	ORCID bo'yicha	По ORCID	1769056635
2002	admin_hint_reference_syntax	[[number]] — is a link to a reference, the link will be automatically inserted when displaying the article.	[[son]] — bu manbaga havola, havola maqolani ko'rsatishda avtomatik ravishda almashtiriladi.	[[число]] — это ссылка на референс, ссылка будет автоматически подставлена при отображении статьи.	1769054444
2110	admin_msg_synchronized	Synchronized!	Sinxronlandi!	Синхронизировано!	1769056197
2116	admin_label_english	English	Inglizcha	Английский	1769056197
2117	admin_title_edit_translation	Edit Translation	Tarjimani tahrirlash	Редактирование перевода	1769056197
2121	admin_msg_network_error	Network error	Tarmoq xatosi	Ошибка сети	1769056197
2122	admin_msg_network_error_sync	Network error during synchronization	Sinxronlashda tarmoq xatosi yuz berdi	Ошибка сети при синхронизации	1769056197
2127	admin_btn_view_current_file	View current file	Joriy faylni ko'rish	Просмотреть текущий файл	1769056353
2128	admin_msg_file_not_uploaded	File not uploaded	Fayl yuklanmagan	Файл не загружен	1769056353
2144	admin_label_by_name	By name	Ism bo'yicha	По имени	1769056635
1673	admin_stats_total_articles	Total Articles	Jami maqolalar	Всего статей	1769047796
2147	admin_label_author_name	Author Name	Muallif ismi	Имя автора	1769056635
2148	admin_placeholder_author_name_example	John Doe	Ivan Ivanov	Иван Иванов	1769056635
2149	admin_label_found_authors	Found Authors	Topilgan mualliflar	Найденные авторы	1769056635
2150	admin_btn_create_new_author	Create New Author	Yangi muallif yaratish	Создать нового автора	1769056635
2151	admin_msg_author_not_found_create	Author not found. Fill in info to create new.	Muallif topilmadi. Yangi yaratish uchun ma'lumotlarni to'ldiring.		1769056635
2152	admin_label_author_full_name	Author Full Name	Muallifning to'liq ismi	Полное имя автора	1769056635
2153	admin_btn_find_author	Find Author	Muallifni topish	Найти автора	1769056635
2154	admin_btn_create_author	Create Author	Muallif yaratish	Создать автора	1769056635
2155	admin_js_msg_enter_author_name	Please enter author name	Iltimos, muallif ismini kiriting	Пожалуйста, введите имя автора	1769056635
2156	admin_js_msg_author_name_min	Author name must be at least 2 characters	Muallif ismi kamida 2 ta belgidan iborat bo'lishi kerak	Имя автора должно содержать минимум 2 символа	1769056635
2157	admin_js_msg_enter_orcid	Please enter ORCID	Iltimos, ORCID kiriting	Пожалуйста, введите ORCID	1769056635
2158	admin_js_msg_invalid_orcid	Invalid ORCID format	ORCID formati noto'g'ri	Неверный формат ORCID	1769056635
2159	admin_js_msg_search_error	Search error	Qidirishda xatolik yuz berdi	Ошибка поиска	1769056635
2160	admin_js_msg_network_error_search	Network error during search	Qidirishda tarmoq xatosi yuz berdi	Ошибка сети при поиске автора	1769056635
2161	admin_js_msg_fill_author_name	Please fill in author name	Iltimos, muallif ismini to'ldiring	Пожалуйста, заполните имя автора	1769056635
2162	admin_js_msg_invalid_email	Invalid email format	Email formati noto'g'ri	Неверный формат email	1769056635
2163	admin_js_msg_create_error	Error creating author	Muallifni yaratishda xatolik yuz berdi	Ошибка создания автора	1769056635
2164	admin_js_msg_network_error_create	Network error during author creation	Muallifni yaratishda tarmoq xatosi yuz berdi	Ошибка сети при создании автора	1769056635
2165	admin_label_no_orcid	No ORCID	ORCID'siz	Без ORCID	1769056635
2166	admin_tooltip_delete_author	Delete Author	Muallifni o'chirish	Удалить автора	1769056731
2167	admin_btn_add_author	Add Author	Muallif qo'shish	Добавить автора	1769056731
2168	admin_page_title_default	Admin	Admin	Админ	1769056771
2169	admin_sidebar_logo_text	FM-Admin	FM-Admin	FM-Admin	1769056771
2170	admin_label_organization	admin_label_organization	admin_label_organization	admin_label_organization	1769067009
2171	admin_label_department	admin_label_department	admin_label_department	admin_label_department	1769067009
2172	admin_label_position	admin_label_position	admin_label_position	admin_label_position	1769067009
2173	admin_label_address	admin_label_address	admin_label_address	admin_label_address	1769067009
2174	admin_label_city	admin_label_city	admin_label_city	admin_label_city	1769067009
2175	admin_label_country	admin_label_country	admin_label_country	admin_label_country	1769067009
2176	admin_label_zip	admin_label_zip	admin_label_zip	admin_label_zip	1769067009
2177	admin_label_phone	admin_label_phone	admin_label_phone	admin_label_phone	1769067009
2178	admin_label_email	admin_label_email	admin_label_email	admin_label_email	1769067009
2187	admin_role_user	admin_role_user	admin_role_user	admin_role_user	1772104755
2188	admin_label_users	admin_label_users	admin_label_users	admin_label_users	1772154915
2189	admin_btn_delete		O'chirish		1772154915
2218	register_with_google	register_with_google			1772856533
2220	subscribe_to_get_access_to_this_issue	subscribe_to_get_access_to_this_issue			1772856796
2190	admin_stats_total	admin_stats_total	admin_stats_total	admin_stats_total	1772164362
2191	admin_status_submitted	admin_status_submitted	admin_status_submitted	admin_status_submitted	1772168335
2192	admin_users_second_name	admin_users_second_name	admin_users_second_name	admin_users_second_name	1772174131
2193	admin_users_father_name	admin_users_father_name	admin_users_father_name	admin_users_father_name	1772174131
2194	select_scientific_area	select_scientific_area			1772273777
2195	classification_min_three_hint	classification_min_three_hint			1772273777
2196	available_classifications	available_classifications			1772273777
2197	login_with_google	login_with_google			1772347262
2198	menu_categories	menu_categories			1772456597
2199	notifications	notifications			1772496266
2200	uploading	uploading			1772517239
2201	upload_failed	upload_failed			1772517239
2202	notifications_marked_read	notifications_marked_read			1772517294
2204	dashboard_overview_text	dashboard_overview_text			1772692807
2205	latest_submissions	latest_submissions			1772692807
2206	view_all	view_all			1772692807
2207	open	open			1772692807
2208	quick_actions	quick_actions			1772692807
2209	notifications_desc	notifications_desc			1772692807
2210	profile_desc	profile_desc			1772692807
2211	guides_desc	guides_desc			1772692807
2212	submit_article_desc	submit_article_desc			1772692807
2213	admin_stats_archived	admin_stats_archived	admin_stats_archived	admin_stats_archived	1772793176
1094	remember_me		Kiritilgan kod eslab qolsinmi		\N
2219	purchase_this_issue_to_get_access	purchase_this_issue_to_get_access			1772856749
2222	complete_profile_required	complete_profile_required			1772870397
2224	academic_position	academic_position			1772870984
2225	not_specified	not_specified			1772870984
2226	student	student			1772870984
2227	postgraduate	postgraduate			1772870984
2228	doctor_science	doctor_science			1772870984
2229	supporting_document	supporting_document			1772870984
2230	upload_document	upload_document			1772870984
2231	supporting_document_hint	supporting_document_hint			1772870984
2232	password_modal_hint	password_modal_hint			1772870984
2233	deleting	deleting			1772870984
2234	confirm_delete_photo	confirm_delete_photo			1772870984
2235	delete_failed	delete_failed			1772870984
2236	document_uploaded	document_uploaded			1772870984
2237	upload_error_prefix	upload_error_prefix			1772870984
2238	orcid_enter_prompt	orcid_enter_prompt			1772870984
2239	searching	searching			1772870984
2240	orcid_not_found_fill_manually	orcid_not_found_fill_manually			1772870984
2241	search_failed_try_again	search_failed_try_again			1772870984
2242	enter_new_password	enter_new_password			1772870984
2243	confirm_new_password	confirm_new_password			1772870984
2244	passwords_do_not_match	passwords_do_not_match			1772870984
2245	password_update_failed	password_update_failed			1772870984
2269	verified	verified			1772883365
2270	current_password	current_password			1773052068
2271	enter_current_password	enter_current_password			1773052068
2272	admin_msg_loading	admin_msg_loading	admin_msg_loading	admin_msg_loading	1773745160
2273	admin_label_citation	admin_label_citation	admin_label_citation	admin_label_citation	1773745160
2274	admin_label_source_type	admin_label_source_type	admin_label_source_type	admin_label_source_type	1773745160
2275	admin_label_select	admin_label_select	admin_label_select	admin_label_select	1773745160
2276	admin_label_date	admin_label_date	admin_label_date	admin_label_date	1773745160
2277	admin_label_link	admin_label_link	admin_label_link	admin_label_link	1773745160
2278	admin_msg_no_results	admin_msg_no_results	admin_msg_no_results	admin_msg_no_results	1773745160
2279	admin_msg_error_search	admin_msg_error_search	admin_msg_error_search	admin_msg_error_search	1773745160
2280	admin_confirm_delete	admin_confirm_delete	admin_confirm_delete	admin_confirm_delete	1773745160
2281	admin_msg_error_loading	admin_msg_error_loading	admin_msg_error_loading	admin_msg_error_loading	1773745160
2282	verify_and_continue	verify_and_continue			1773825677
2283	resend_code	resend_code			1773825677
1412	menu_for_uzgumya	For UzGUMya Researchers	UzDJTU tadqiqotchilari uchun		\N
1631	stat_1_value	5 days	5 kun	5 дней	1769042596
1632	stat_1_text	To first decision	Birinchi qarorgacha vaqt	До первого решения	1769042596
2099	admin_label_user_limit	Duration (days)	Muddat (kun)	Срок (дней)	1769056098
1420	footer_copyright	Copyright © 2026 Uzbekistan State World Languages University.	Mualliflik huquqi © 2026 O'zbekiston Davlat Jahon tillari universiteti.	Авторское право © 2026 Узбекский государственный университет мировых языков.	\N
1421	footer_rights	All rights reserved.	Barcha huquqlar himoyalangan.	Все права защищены.	\N
2215	admin_translations_help_text	admin_translations_help_text	admin_translations_help_text	admin_translations_help_text	1772797077
2216	admin_msg_required	admin_msg_required	admin_msg_required	admin_msg_required	1772797077
2268	no_articles_yet	no_articles_yet			1772871024
1635	stat_3_value	18 days	18 kun	18 дней	1769042596
1636	stat_3_text	Submission to acceptance	Qabul qilinishigacha vaqt	До принятия	1769042596
1637	stat_4_value	5 days	5 kun	5 дней	1769042596
1638	stat_4_text	Acceptance to online publication	Onlayn nashrgacha vaqt	До онлайн-публикации	1769042596
1580	access_free	access_free	Kirish bepul		1752612118
1569	apply_filters	apply_filters	Filterni qo'llash		1752612108
2217	admin_label_doi_link	admin_label_doi_link	admin_label_doi_link	admin_label_doi_link	1772844930
\.


--
-- Name: translations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.translations_id_seq', 2283, true);


--
-- PostgreSQL database dump complete
--

\unrestrict ocXOpGz2tW8iR24MM5uJCwaNZhBFbEEqARP0HF2uOjyE7E3n6fGaKDPj0DZn7ED

