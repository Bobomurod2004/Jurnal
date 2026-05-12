--
-- PostgreSQL database dump
--

\restrict gKVeBjTbEeeYfKUXAeK1sMb7ovy8LFzPfKM9mx8M1BrSGQPWgXKcOLaqkNnji3r

-- Dumped from database version 17.7
-- Dumped by pg_dump version 17.7

-- Started on 2026-01-27 16:48:00

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 217 (class 1259 OID 24678)
-- Name: author_profile; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.author_profile (
    id integer NOT NULL,
    user_id integer,
    name text,
    organization text,
    email text,
    "position" text,
    address_street text,
    address_country text,
    address_city text,
    address_zip text,
    phone text,
    orcid text,
    created_at integer,
    department text,
    updated_at integer
);


ALTER TABLE public.author_profile OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 24683)
-- Name: author_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.author_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.author_profile_id_seq OWNER TO postgres;

--
-- TOC entry 5168 (class 0 OID 0)
-- Dependencies: 218
-- Name: author_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.author_profile_id_seq OWNED BY public.author_profile.id;


--
-- TOC entry 219 (class 1259 OID 24684)
-- Name: editor_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.editor_assignments (
    id integer NOT NULL,
    submission_id integer NOT NULL,
    editor_id integer NOT NULL,
    assigned_by integer NOT NULL,
    assigned_at bigint NOT NULL,
    status text DEFAULT 'pending'::text,
    editor_comment text,
    editor_file text,
    reviewed_at bigint,
    created_at bigint DEFAULT EXTRACT(epoch FROM now()),
    updated_at bigint DEFAULT EXTRACT(epoch FROM now())
);


ALTER TABLE public.editor_assignments OWNER TO postgres;

--
-- TOC entry 5169 (class 0 OID 0)
-- Dependencies: 219
-- Name: TABLE editor_assignments; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.editor_assignments IS 'Назначения статей редакторам для проверки';


--
-- TOC entry 5170 (class 0 OID 0)
-- Dependencies: 219
-- Name: COLUMN editor_assignments.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.editor_assignments.status IS 'Статус проверки: pending, reviewed, rejected';


--
-- TOC entry 5171 (class 0 OID 0)
-- Dependencies: 219
-- Name: COLUMN editor_assignments.editor_comment; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.editor_assignments.editor_comment IS 'Комментарий редактора по статье';


--
-- TOC entry 5172 (class 0 OID 0)
-- Dependencies: 219
-- Name: COLUMN editor_assignments.editor_file; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.editor_assignments.editor_file IS 'Путь к файлу, прикрепленному редактором';


--
-- TOC entry 220 (class 1259 OID 24692)
-- Name: editor_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.editor_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.editor_assignments_id_seq OWNER TO postgres;

--
-- TOC entry 5173 (class 0 OID 0)
-- Dependencies: 220
-- Name: editor_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.editor_assignments_id_seq OWNED BY public.editor_assignments.id;


--
-- TOC entry 221 (class 1259 OID 24693)
-- Name: editor_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.editor_notifications (
    id integer NOT NULL,
    editor_id integer NOT NULL,
    assignment_id integer NOT NULL,
    message text NOT NULL,
    is_read boolean DEFAULT false,
    created_at bigint DEFAULT EXTRACT(epoch FROM now())
);


ALTER TABLE public.editor_notifications OWNER TO postgres;

--
-- TOC entry 5174 (class 0 OID 0)
-- Dependencies: 221
-- Name: TABLE editor_notifications; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.editor_notifications IS 'Уведомления для редакторов о новых назначениях';


--
-- TOC entry 222 (class 1259 OID 24700)
-- Name: editor_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.editor_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.editor_notifications_id_seq OWNER TO postgres;

--
-- TOC entry 5175 (class 0 OID 0)
-- Dependencies: 222
-- Name: editor_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.editor_notifications_id_seq OWNED BY public.editor_notifications.id;


--
-- TOC entry 223 (class 1259 OID 24701)
-- Name: editorial_board; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.editorial_board (
    id integer NOT NULL,
    title text,
    full_name text NOT NULL,
    organization text,
    biography text,
    order_group integer,
    image text
);


ALTER TABLE public.editorial_board OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 24706)
-- Name: editorial_board_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.editorial_board_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.editorial_board_id_seq OWNER TO postgres;

--
-- TOC entry 5176 (class 0 OID 0)
-- Dependencies: 224
-- Name: editorial_board_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.editorial_board_id_seq OWNED BY public.editorial_board.id;


--
-- TOC entry 225 (class 1259 OID 24707)
-- Name: files; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.files (
    id integer NOT NULL,
    name text,
    filepath text,
    upload_time bigint,
    comment text,
    filesize bigint,
    created_at integer
);


ALTER TABLE public.files OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 24712)
-- Name: files_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.files_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.files_id_seq OWNER TO postgres;

--
-- TOC entry 5177 (class 0 OID 0)
-- Dependencies: 226
-- Name: files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.files_id_seq OWNED BY public.files.id;


--
-- TOC entry 227 (class 1259 OID 24713)
-- Name: fix_classifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fix_classifications (
    id integer NOT NULL,
    name text NOT NULL,
    name_uz text NOT NULL,
    name_ru text NOT NULL
);


ALTER TABLE public.fix_classifications OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 24718)
-- Name: fix_classifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fix_classifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fix_classifications_id_seq OWNER TO postgres;

--
-- TOC entry 5178 (class 0 OID 0)
-- Dependencies: 228
-- Name: fix_classifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fix_classifications_id_seq OWNED BY public.fix_classifications.id;


--
-- TOC entry 229 (class 1259 OID 24719)
-- Name: fix_country; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fix_country (
    id integer NOT NULL,
    name text,
    name_uz text,
    name_ru text,
    created_at integer
);


ALTER TABLE public.fix_country OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 24724)
-- Name: fix_country_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fix_country_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fix_country_id_seq OWNER TO postgres;

--
-- TOC entry 5179 (class 0 OID 0)
-- Dependencies: 230
-- Name: fix_country_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fix_country_id_seq OWNED BY public.fix_country.id;


--
-- TOC entry 231 (class 1259 OID 24725)
-- Name: fix_issue_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fix_issue_categories (
    id integer NOT NULL,
    alias text NOT NULL,
    name text NOT NULL,
    name_uz text NOT NULL,
    name_ru text NOT NULL
);


ALTER TABLE public.fix_issue_categories OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 24730)
-- Name: fix_issue_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fix_issue_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fix_issue_categories_id_seq OWNER TO postgres;

--
-- TOC entry 5180 (class 0 OID 0)
-- Dependencies: 232
-- Name: fix_issue_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fix_issue_categories_id_seq OWNED BY public.fix_issue_categories.id;


--
-- TOC entry 233 (class 1259 OID 24731)
-- Name: issues; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issues (
    id integer NOT NULL,
    title text,
    title_uz text,
    title_ru text,
    vol_no text,
    issue_no text,
    year integer,
    category text,
    shortinfo text,
    shortinfo_uz text,
    shortinfo_ru text,
    price double precision,
    price_uz double precision,
    price_ru double precision,
    subscription_enable boolean DEFAULT false,
    is_paid boolean DEFAULT false,
    cover_image text,
    table_of_contents_file text,
    created_at integer
);


ALTER TABLE public.issues OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 24738)
-- Name: issues_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.issues_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.issues_id_seq OWNER TO postgres;

--
-- TOC entry 5181 (class 0 OID 0)
-- Dependencies: 234
-- Name: issues_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.issues_id_seq OWNED BY public.issues.id;


--
-- TOC entry 235 (class 1259 OID 24739)
-- Name: news; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.news (
    id integer NOT NULL,
    type text DEFAULT 'news'::text NOT NULL,
    title text,
    title_ru text,
    title_uz text,
    content text,
    content_ru text,
    content_uz text,
    status text DEFAULT 'draft'::text,
    created_at bigint,
    published_at bigint,
    author_id integer,
    cover_image text
);


ALTER TABLE public.news OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 24746)
-- Name: news_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.news_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.news_id_seq OWNER TO postgres;

--
-- TOC entry 5182 (class 0 OID 0)
-- Dependencies: 236
-- Name: news_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.news_id_seq OWNED BY public.news.id;


--
-- TOC entry 237 (class 1259 OID 24747)
-- Name: pages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pages (
    id integer NOT NULL,
    alias text,
    title text,
    title_uz text,
    title_ru text,
    content text,
    content_uz text,
    content_ru text,
    last_update bigint,
    created_at integer
);


ALTER TABLE public.pages OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 24752)
-- Name: pages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pages_id_seq OWNER TO postgres;

--
-- TOC entry 5183 (class 0 OID 0)
-- Dependencies: 238
-- Name: pages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pages_id_seq OWNED BY public.pages.id;


--
-- TOC entry 239 (class 1259 OID 24753)
-- Name: payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    user_id integer,
    status text DEFAULT 'unpaid'::text,
    currency text DEFAULT 'usd'::text,
    payment_type text,
    payment_date bigint,
    amount double precision,
    ids integer[],
    proof text,
    note text,
    created_at integer
);


ALTER TABLE public.payments OWNER TO postgres;

--
-- TOC entry 240 (class 1259 OID 24760)
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payments_id_seq OWNER TO postgres;

--
-- TOC entry 5184 (class 0 OID 0)
-- Dependencies: 240
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- TOC entry 241 (class 1259 OID 24761)
-- Name: publication_citations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.publication_citations (
    id integer NOT NULL,
    publication_id integer,
    title text,
    authors text,
    doi text,
    doi_link text,
    wos_link text,
    scopus_link text,
    gscholar_link text,
    created_at integer
);


ALTER TABLE public.publication_citations OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 24766)
-- Name: publication_citations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.publication_citations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.publication_citations_id_seq OWNER TO postgres;

--
-- TOC entry 5185 (class 0 OID 0)
-- Dependencies: 242
-- Name: publication_citations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.publication_citations_id_seq OWNED BY public.publication_citations.id;


--
-- TOC entry 243 (class 1259 OID 24767)
-- Name: publication_figures; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.publication_figures (
    id integer NOT NULL,
    publication_id integer,
    title text,
    filepath text,
    order_id integer,
    created_at integer
);


ALTER TABLE public.publication_figures OWNER TO postgres;

--
-- TOC entry 244 (class 1259 OID 24772)
-- Name: publication_figures_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.publication_figures_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.publication_figures_id_seq OWNER TO postgres;

--
-- TOC entry 5186 (class 0 OID 0)
-- Dependencies: 244
-- Name: publication_figures_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.publication_figures_id_seq OWNED BY public.publication_figures.id;


--
-- TOC entry 245 (class 1259 OID 24773)
-- Name: publication_parts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.publication_parts (
    id integer NOT NULL,
    publication_id integer,
    title text,
    content text,
    order_id integer,
    created_at integer
);


ALTER TABLE public.publication_parts OWNER TO postgres;

--
-- TOC entry 246 (class 1259 OID 24778)
-- Name: publication_parts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.publication_parts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.publication_parts_id_seq OWNER TO postgres;

--
-- TOC entry 5187 (class 0 OID 0)
-- Dependencies: 246
-- Name: publication_parts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.publication_parts_id_seq OWNED BY public.publication_parts.id;


--
-- TOC entry 263 (class 1259 OID 24973)
-- Name: publication_refs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.publication_refs (
    id integer NOT NULL,
    publication_id integer,
    source_type text,
    authors text,
    organization_name text,
    publication_year integer,
    publication_date text,
    title text,
    chapter_title text,
    thesis_type text,
    source_title text,
    publisher_name text,
    publication_place text,
    volume text,
    issue text,
    page_start text,
    page_end text,
    edition text,
    conference_country text,
    conference_city text,
    word_term text,
    defense_place text,
    university_name text,
    doi text,
    url text,
    web_of_science_url text,
    google_scholar_url text,
    access_date text,
    created_at integer
);


ALTER TABLE public.publication_refs OWNER TO postgres;

--
-- TOC entry 261 (class 1259 OID 24967)
-- Name: publication_refs_backup; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.publication_refs_backup (
    id integer,
    publication_id integer,
    title text,
    authors text,
    doi text,
    doi_link text,
    wos_link text,
    scopus_link text,
    gscholar_link text,
    created_at integer,
    resource text,
    web_link text
);


ALTER TABLE public.publication_refs_backup OWNER TO postgres;

--
-- TOC entry 262 (class 1259 OID 24972)
-- Name: publication_refs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.publication_refs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.publication_refs_id_seq OWNER TO postgres;

--
-- TOC entry 5188 (class 0 OID 0)
-- Dependencies: 262
-- Name: publication_refs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.publication_refs_id_seq OWNED BY public.publication_refs.id;


--
-- TOC entry 247 (class 1259 OID 24785)
-- Name: publications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.publications (
    id integer NOT NULL,
    title text,
    title_uz text,
    title_ru text,
    main_author_id integer,
    subauthor_ids integer[],
    issue_id integer,
    abstract text,
    abstract_uz text,
    abstract_ru text,
    doi text,
    doi_link text,
    page_range text,
    author_position_key text,
    academic_title_key text,
    academic_degree_key text,
    series_key text,
    keywords text[],
    additional text,
    stat_views integer,
    stat_alt integer,
    stat_crossref integer,
    stat_wos integer,
    stat_scopus integer,
    date_sent bigint,
    date_accept bigint,
    date_publish bigint,
    stage text,
    comments text,
    file_ids integer[],
    is_paid boolean DEFAULT false,
    price double precision,
    price_uz double precision,
    price_ru double precision,
    subscription_enable boolean DEFAULT false,
    created_at integer,
    keywords_uz text[] DEFAULT '{}'::text[],
    keywords_ru text[] DEFAULT '{}'::text[],
    current_views integer DEFAULT 0
);


ALTER TABLE public.publications OWNER TO postgres;

--
-- TOC entry 248 (class 1259 OID 24795)
-- Name: publications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.publications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.publications_id_seq OWNER TO postgres;

--
-- TOC entry 5189 (class 0 OID 0)
-- Dependencies: 248
-- Name: publications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.publications_id_seq OWNED BY public.publications.id;


--
-- TOC entry 249 (class 1259 OID 24796)
-- Name: settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.settings (
    id integer NOT NULL,
    k text,
    v text,
    created_at integer
);


ALTER TABLE public.settings OWNER TO postgres;

--
-- TOC entry 250 (class 1259 OID 24801)
-- Name: settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.settings_id_seq OWNER TO postgres;

--
-- TOC entry 5190 (class 0 OID 0)
-- Dependencies: 250
-- Name: settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.settings_id_seq OWNED BY public.settings.id;


--
-- TOC entry 251 (class 1259 OID 24802)
-- Name: submissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.submissions (
    id integer NOT NULL,
    user_id integer,
    status text DEFAULT 'draft'::text,
    title text,
    abstract text,
    is_special boolean,
    is_dataset boolean,
    check_copyright boolean,
    keywords text[],
    classifications text[],
    check_ethical boolean,
    check_consent boolean,
    check_acknowledgements boolean,
    is_used_previous boolean,
    word_count integer,
    is_corresponding_author boolean,
    main_author_id integer,
    sub_author_ids integer[],
    is_competing_interests boolean,
    notes text,
    file_authors text,
    file_anonymized text,
    created_date bigint,
    updated_at integer,
    editor_review_status text DEFAULT 'not_assigned'::text
);


ALTER TABLE public.submissions OWNER TO postgres;

--
-- TOC entry 5191 (class 0 OID 0)
-- Dependencies: 251
-- Name: COLUMN submissions.editor_review_status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.submissions.editor_review_status IS 'Статус редакторской проверки: not_assigned, assigned, in_review, reviewed, approved, rejected';


--
-- TOC entry 252 (class 1259 OID 24809)
-- Name: submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.submissions_id_seq OWNER TO postgres;

--
-- TOC entry 5192 (class 0 OID 0)
-- Dependencies: 252
-- Name: submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.submissions_id_seq OWNED BY public.submissions.id;


--
-- TOC entry 253 (class 1259 OID 24810)
-- Name: tariffs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tariffs (
    id integer NOT NULL,
    name text NOT NULL,
    name_uz text,
    name_ru text,
    description text,
    description_uz text,
    description_ru text,
    price_rub double precision DEFAULT 0,
    price_uzs double precision DEFAULT 0,
    price_usd double precision DEFAULT 0,
    user_limit integer DEFAULT 0,
    duration_days integer DEFAULT 30,
    is_default boolean DEFAULT false,
    created_at bigint,
    updated_at bigint,
    is_verified boolean DEFAULT false
);


ALTER TABLE public.tariffs OWNER TO postgres;

--
-- TOC entry 254 (class 1259 OID 24821)
-- Name: tariffs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tariffs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tariffs_id_seq OWNER TO postgres;

--
-- TOC entry 5193 (class 0 OID 0)
-- Dependencies: 254
-- Name: tariffs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tariffs_id_seq OWNED BY public.tariffs.id;


--
-- TOC entry 255 (class 1259 OID 24822)
-- Name: translations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.translations (
    id integer NOT NULL,
    alias text,
    content text,
    content_uz text,
    content_ru text,
    created_at integer
);


ALTER TABLE public.translations OWNER TO postgres;

--
-- TOC entry 256 (class 1259 OID 24827)
-- Name: translations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.translations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.translations_id_seq OWNER TO postgres;

--
-- TOC entry 5194 (class 0 OID 0)
-- Dependencies: 256
-- Name: translations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.translations_id_seq OWNED BY public.translations.id;


--
-- TOC entry 257 (class 1259 OID 24828)
-- Name: user_doc_uploads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_doc_uploads (
    id integer NOT NULL,
    user_id integer,
    work_title text,
    file_path text,
    verification_status text,
    created_at bigint,
    updated_at bigint
);


ALTER TABLE public.user_doc_uploads OWNER TO postgres;

--
-- TOC entry 258 (class 1259 OID 24833)
-- Name: user_doc_uploads_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_doc_uploads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_doc_uploads_id_seq OWNER TO postgres;

--
-- TOC entry 5195 (class 0 OID 0)
-- Dependencies: 258
-- Name: user_doc_uploads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_doc_uploads_id_seq OWNED BY public.user_doc_uploads.id;


--
-- TOC entry 259 (class 1259 OID 24834)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name text,
    second_name text,
    father_name text,
    email text,
    password text,
    country_id integer,
    region text,
    rolename text DEFAULT 'user'::text,
    is_blocked boolean DEFAULT false,
    is_notify boolean DEFAULT false,
    accept_rules_time bigint,
    last_online bigint,
    created_at integer,
    register_time integer,
    token text,
    avatar text,
    subscription_end_date bigint,
    tariff_id integer,
    editor_specialization text
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 260 (class 1259 OID 24842)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 5196 (class 0 OID 0)
-- Dependencies: 260
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 4856 (class 2604 OID 24843)
-- Name: author_profile id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.author_profile ALTER COLUMN id SET DEFAULT nextval('public.author_profile_id_seq'::regclass);


--
-- TOC entry 4857 (class 2604 OID 24844)
-- Name: editor_assignments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_assignments ALTER COLUMN id SET DEFAULT nextval('public.editor_assignments_id_seq'::regclass);


--
-- TOC entry 4861 (class 2604 OID 24845)
-- Name: editor_notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_notifications ALTER COLUMN id SET DEFAULT nextval('public.editor_notifications_id_seq'::regclass);


--
-- TOC entry 4864 (class 2604 OID 24846)
-- Name: editorial_board id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editorial_board ALTER COLUMN id SET DEFAULT nextval('public.editorial_board_id_seq'::regclass);


--
-- TOC entry 4865 (class 2604 OID 24847)
-- Name: files id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.files ALTER COLUMN id SET DEFAULT nextval('public.files_id_seq'::regclass);


--
-- TOC entry 4866 (class 2604 OID 24848)
-- Name: fix_classifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fix_classifications ALTER COLUMN id SET DEFAULT nextval('public.fix_classifications_id_seq'::regclass);


--
-- TOC entry 4867 (class 2604 OID 24849)
-- Name: fix_country id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fix_country ALTER COLUMN id SET DEFAULT nextval('public.fix_country_id_seq'::regclass);


--
-- TOC entry 4868 (class 2604 OID 24850)
-- Name: fix_issue_categories id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fix_issue_categories ALTER COLUMN id SET DEFAULT nextval('public.fix_issue_categories_id_seq'::regclass);


--
-- TOC entry 4869 (class 2604 OID 24851)
-- Name: issues id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues ALTER COLUMN id SET DEFAULT nextval('public.issues_id_seq'::regclass);


--
-- TOC entry 4872 (class 2604 OID 24852)
-- Name: news id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.news ALTER COLUMN id SET DEFAULT nextval('public.news_id_seq'::regclass);


--
-- TOC entry 4875 (class 2604 OID 24853)
-- Name: pages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pages ALTER COLUMN id SET DEFAULT nextval('public.pages_id_seq'::regclass);


--
-- TOC entry 4876 (class 2604 OID 24854)
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- TOC entry 4879 (class 2604 OID 24855)
-- Name: publication_citations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publication_citations ALTER COLUMN id SET DEFAULT nextval('public.publication_citations_id_seq'::regclass);


--
-- TOC entry 4880 (class 2604 OID 24856)
-- Name: publication_figures id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publication_figures ALTER COLUMN id SET DEFAULT nextval('public.publication_figures_id_seq'::regclass);


--
-- TOC entry 4881 (class 2604 OID 24857)
-- Name: publication_parts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publication_parts ALTER COLUMN id SET DEFAULT nextval('public.publication_parts_id_seq'::regclass);


--
-- TOC entry 4905 (class 2604 OID 24976)
-- Name: publication_refs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publication_refs ALTER COLUMN id SET DEFAULT nextval('public.publication_refs_id_seq'::regclass);


--
-- TOC entry 4882 (class 2604 OID 24859)
-- Name: publications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publications ALTER COLUMN id SET DEFAULT nextval('public.publications_id_seq'::regclass);


--
-- TOC entry 4888 (class 2604 OID 24860)
-- Name: settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings ALTER COLUMN id SET DEFAULT nextval('public.settings_id_seq'::regclass);


--
-- TOC entry 4889 (class 2604 OID 24861)
-- Name: submissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.submissions ALTER COLUMN id SET DEFAULT nextval('public.submissions_id_seq'::regclass);


--
-- TOC entry 4892 (class 2604 OID 24862)
-- Name: tariffs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tariffs ALTER COLUMN id SET DEFAULT nextval('public.tariffs_id_seq'::regclass);


--
-- TOC entry 4899 (class 2604 OID 24863)
-- Name: translations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.translations ALTER COLUMN id SET DEFAULT nextval('public.translations_id_seq'::regclass);


--
-- TOC entry 4900 (class 2604 OID 24864)
-- Name: user_doc_uploads id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_doc_uploads ALTER COLUMN id SET DEFAULT nextval('public.user_doc_uploads_id_seq'::regclass);


--
-- TOC entry 4901 (class 2604 OID 24865)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 5116 (class 0 OID 24678)
-- Dependencies: 217
-- Data for Name: author_profile; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5118 (class 0 OID 24684)
-- Dependencies: 219
-- Data for Name: editor_assignments; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5120 (class 0 OID 24693)
-- Dependencies: 221
-- Data for Name: editor_notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5122 (class 0 OID 24701)
-- Dependencies: 223
-- Data for Name: editorial_board; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5124 (class 0 OID 24707)
-- Dependencies: 225
-- Data for Name: files; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5126 (class 0 OID 24713)
-- Dependencies: 227
-- Data for Name: fix_classifications; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5128 (class 0 OID 24719)
-- Dependencies: 229
-- Data for Name: fix_country; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5130 (class 0 OID 24725)
-- Dependencies: 231
-- Data for Name: fix_issue_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5132 (class 0 OID 24731)
-- Dependencies: 233
-- Data for Name: issues; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5134 (class 0 OID 24739)
-- Dependencies: 235
-- Data for Name: news; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5136 (class 0 OID 24747)
-- Dependencies: 237
-- Data for Name: pages; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5138 (class 0 OID 24753)
-- Dependencies: 239
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5140 (class 0 OID 24761)
-- Dependencies: 241
-- Data for Name: publication_citations; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5142 (class 0 OID 24767)
-- Dependencies: 243
-- Data for Name: publication_figures; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5144 (class 0 OID 24773)
-- Dependencies: 245
-- Data for Name: publication_parts; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5162 (class 0 OID 24973)
-- Dependencies: 263
-- Data for Name: publication_refs; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5160 (class 0 OID 24967)
-- Dependencies: 261
-- Data for Name: publication_refs_backup; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5146 (class 0 OID 24785)
-- Dependencies: 247
-- Data for Name: publications; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5148 (class 0 OID 24796)
-- Dependencies: 249
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5150 (class 0 OID 24802)
-- Dependencies: 251
-- Data for Name: submissions; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5152 (class 0 OID 24810)
-- Dependencies: 253
-- Data for Name: tariffs; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5154 (class 0 OID 24822)
-- Dependencies: 255
-- Data for Name: translations; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5156 (class 0 OID 24828)
-- Dependencies: 257
-- Data for Name: user_doc_uploads; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5158 (class 0 OID 24834)
-- Dependencies: 259
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 5197 (class 0 OID 0)
-- Dependencies: 218
-- Name: author_profile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5198 (class 0 OID 0)
-- Dependencies: 220
-- Name: editor_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5199 (class 0 OID 0)
-- Dependencies: 222
-- Name: editor_notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5200 (class 0 OID 0)
-- Dependencies: 224
-- Name: editorial_board_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5201 (class 0 OID 0)
-- Dependencies: 226
-- Name: files_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5202 (class 0 OID 0)
-- Dependencies: 228
-- Name: fix_classifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5203 (class 0 OID 0)
-- Dependencies: 230
-- Name: fix_country_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5204 (class 0 OID 0)
-- Dependencies: 232
-- Name: fix_issue_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5205 (class 0 OID 0)
-- Dependencies: 234
-- Name: issues_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5206 (class 0 OID 0)
-- Dependencies: 236
-- Name: news_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5207 (class 0 OID 0)
-- Dependencies: 238
-- Name: pages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5208 (class 0 OID 0)
-- Dependencies: 240
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5209 (class 0 OID 0)
-- Dependencies: 242
-- Name: publication_citations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5210 (class 0 OID 0)
-- Dependencies: 244
-- Name: publication_figures_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5211 (class 0 OID 0)
-- Dependencies: 246
-- Name: publication_parts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5212 (class 0 OID 0)
-- Dependencies: 262
-- Name: publication_refs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5213 (class 0 OID 0)
-- Dependencies: 248
-- Name: publications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5214 (class 0 OID 0)
-- Dependencies: 250
-- Name: settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5215 (class 0 OID 0)
-- Dependencies: 252
-- Name: submissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5216 (class 0 OID 0)
-- Dependencies: 254
-- Name: tariffs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5217 (class 0 OID 0)
-- Dependencies: 256
-- Name: translations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5218 (class 0 OID 0)
-- Dependencies: 258
-- Name: user_doc_uploads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 5219 (class 0 OID 0)
-- Dependencies: 260
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--



--
-- TOC entry 4907 (class 2606 OID 24875)
-- Name: author_profile author_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.author_profile
    ADD CONSTRAINT author_profile_pkey PRIMARY KEY (id);


--
-- TOC entry 4909 (class 2606 OID 24877)
-- Name: editor_assignments editor_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_assignments
    ADD CONSTRAINT editor_assignments_pkey PRIMARY KEY (id);


--
-- TOC entry 4914 (class 2606 OID 24879)
-- Name: editor_notifications editor_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_notifications
    ADD CONSTRAINT editor_notifications_pkey PRIMARY KEY (id);


--
-- TOC entry 4918 (class 2606 OID 24881)
-- Name: editorial_board editorial_board_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editorial_board
    ADD CONSTRAINT editorial_board_pkey PRIMARY KEY (id);


--
-- TOC entry 4920 (class 2606 OID 24883)
-- Name: files files_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);


--
-- TOC entry 4922 (class 2606 OID 24885)
-- Name: fix_classifications fix_classifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fix_classifications
    ADD CONSTRAINT fix_classifications_pkey PRIMARY KEY (id);


--
-- TOC entry 4924 (class 2606 OID 24887)
-- Name: fix_country fix_country_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fix_country
    ADD CONSTRAINT fix_country_pkey PRIMARY KEY (id);


--
-- TOC entry 4926 (class 2606 OID 24889)
-- Name: fix_issue_categories fix_issue_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fix_issue_categories
    ADD CONSTRAINT fix_issue_categories_pkey PRIMARY KEY (id);


--
-- TOC entry 4928 (class 2606 OID 24891)
-- Name: issues issues_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues
    ADD CONSTRAINT issues_pkey PRIMARY KEY (id);


--
-- TOC entry 4930 (class 2606 OID 24893)
-- Name: news news_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.news
    ADD CONSTRAINT news_pkey PRIMARY KEY (id);


--
-- TOC entry 4932 (class 2606 OID 24895)
-- Name: pages pages_alias_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pages
    ADD CONSTRAINT pages_alias_key UNIQUE (alias);


--
-- TOC entry 4934 (class 2606 OID 24897)
-- Name: pages pages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pages
    ADD CONSTRAINT pages_pkey PRIMARY KEY (id);


--
-- TOC entry 4936 (class 2606 OID 24899)
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- TOC entry 4938 (class 2606 OID 24901)
-- Name: publication_citations publication_citations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publication_citations
    ADD CONSTRAINT publication_citations_pkey PRIMARY KEY (id);


--
-- TOC entry 4940 (class 2606 OID 24903)
-- Name: publication_figures publication_figures_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publication_figures
    ADD CONSTRAINT publication_figures_pkey PRIMARY KEY (id);


--
-- TOC entry 4942 (class 2606 OID 24905)
-- Name: publication_parts publication_parts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publication_parts
    ADD CONSTRAINT publication_parts_pkey PRIMARY KEY (id);


--
-- TOC entry 4964 (class 2606 OID 24980)
-- Name: publication_refs publication_refs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publication_refs
    ADD CONSTRAINT publication_refs_pkey PRIMARY KEY (id);


--
-- TOC entry 4944 (class 2606 OID 24909)
-- Name: publications publications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_pkey PRIMARY KEY (id);


--
-- TOC entry 4946 (class 2606 OID 24911)
-- Name: settings settings_k_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_k_key UNIQUE (k);


--
-- TOC entry 4948 (class 2606 OID 24913)
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- TOC entry 4950 (class 2606 OID 24915)
-- Name: submissions submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_pkey PRIMARY KEY (id);


--
-- TOC entry 4952 (class 2606 OID 24917)
-- Name: tariffs tariffs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tariffs
    ADD CONSTRAINT tariffs_pkey PRIMARY KEY (id);


--
-- TOC entry 4954 (class 2606 OID 24919)
-- Name: translations translations_alias_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_alias_key UNIQUE (alias);


--
-- TOC entry 4956 (class 2606 OID 24921)
-- Name: translations translations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_pkey PRIMARY KEY (id);


--
-- TOC entry 4958 (class 2606 OID 24923)
-- Name: user_doc_uploads user_doc_uploads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_doc_uploads
    ADD CONSTRAINT user_doc_uploads_pkey PRIMARY KEY (id);


--
-- TOC entry 4960 (class 2606 OID 24925)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4962 (class 2606 OID 24927)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4910 (class 1259 OID 24928)
-- Name: idx_editor_assignments_editor_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_editor_assignments_editor_id ON public.editor_assignments USING btree (editor_id);


--
-- TOC entry 4911 (class 1259 OID 24929)
-- Name: idx_editor_assignments_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_editor_assignments_status ON public.editor_assignments USING btree (status);


--
-- TOC entry 4912 (class 1259 OID 24930)
-- Name: idx_editor_assignments_submission_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_editor_assignments_submission_id ON public.editor_assignments USING btree (submission_id);


--
-- TOC entry 4915 (class 1259 OID 24931)
-- Name: idx_editor_notifications_editor_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_editor_notifications_editor_id ON public.editor_notifications USING btree (editor_id);


--
-- TOC entry 4916 (class 1259 OID 24932)
-- Name: idx_editor_notifications_is_read; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_editor_notifications_is_read ON public.editor_notifications USING btree (is_read);


--
-- TOC entry 4965 (class 2606 OID 24933)
-- Name: editor_assignments editor_assignments_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_assignments
    ADD CONSTRAINT editor_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- TOC entry 4966 (class 2606 OID 24938)
-- Name: editor_assignments editor_assignments_editor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_assignments
    ADD CONSTRAINT editor_assignments_editor_id_fkey FOREIGN KEY (editor_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4967 (class 2606 OID 24943)
-- Name: editor_assignments editor_assignments_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_assignments
    ADD CONSTRAINT editor_assignments_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE;


--
-- TOC entry 4968 (class 2606 OID 24948)
-- Name: editor_notifications editor_notifications_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_notifications
    ADD CONSTRAINT editor_notifications_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.editor_assignments(id) ON DELETE CASCADE;


--
-- TOC entry 4969 (class 2606 OID 24953)
-- Name: editor_notifications editor_notifications_editor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.editor_notifications
    ADD CONSTRAINT editor_notifications_editor_id_fkey FOREIGN KEY (editor_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4970 (class 2606 OID 24958)
-- Name: users users_tariff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_tariff_id_fkey FOREIGN KEY (tariff_id) REFERENCES public.tariffs(id);


-- Completed on 2026-01-27 16:48:00

--
-- PostgreSQL database dump complete
--

\unrestrict gKVeBjTbEeeYfKUXAeK1sMb7ovy8LFzPfKM9mx8M1BrSGQPWgXKcOLaqkNnji3r
