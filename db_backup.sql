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

COPY public.author_profile (id, user_id, name, organization, email, "position", address_street, address_country, address_city, address_zip, phone, orcid, created_at, department, updated_at) FROM stdin;
8	\N	Oybek Akhmedov	Uzbekistan State World Languages University	oybekakhmedov1978@gmail.com	Doctor of Siences in Philology (DSc), professor		Uzbekistan	Tashkent			0009-0003-3122-1973	1753979032		1753979032
9	\N	Sardora Rakhmonova	Uzbekistan State World Languages University	sardorarakhmonova@gmail.com	Senior Teacher		Uzbekistan	Tashkent			0009-0004-8209-3518	1753979073		1753979073
10	5	Solijon Azizov	O'zbekiston davlat jahon tillari universiteti	soljonazizov1@gmail.com	O'qituvchi	Chilonzor 17	Uzbekistan	Tashkent	100135	933924778	0000-0003-0467-7003	1757763084	Ingliz tili integrallashgan kursi N1	1757763084
11	8	Kuniyuki NOTO	Uzbek State World Languages University	uzdjtu@uzswlu.uz	 senior lecturer	Uchtepa Zakovat-4	Uzbekistan	Tashkent	xxxxx	*998712300344	0009-0002-5609-8441	1762627497	Yapon filologiysi kafedrasi	1762627497
\.


--
-- TOC entry 5118 (class 0 OID 24684)
-- Dependencies: 219
-- Data for Name: editor_assignments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.editor_assignments (id, submission_id, editor_id, assigned_by, assigned_at, status, editor_comment, editor_file, reviewed_at, created_at, updated_at) FROM stdin;
3	17	7	1	1757739001	pending	\N	\N	\N	\N	\N
4	17	6	1	1757739001	pending	\N	\N	\N	\N	\N
\.


--
-- TOC entry 5120 (class 0 OID 24693)
-- Dependencies: 221
-- Data for Name: editor_notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.editor_notifications (id, editor_id, assignment_id, message, is_read, created_at) FROM stdin;
\.


--
-- TOC entry 5122 (class 0 OID 24701)
-- Dependencies: 223
-- Data for Name: editorial_board; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.editorial_board (id, title, full_name, organization, biography, order_group, image) FROM stdin;
\.


--
-- TOC entry 5124 (class 0 OID 24707)
-- Dependencies: 225
-- Data for Name: files; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.files (id, name, filepath, upload_time, comment, filesize, created_at) FROM stdin;
1	Oybek Axmedov.pdf	/static/uploads/articles/2025/08/306b5b7e4ae34b37b1b634e225f10976.pdf	1754375130	PDF для статьи 119	483959	1754375130
\.


--
-- TOC entry 5126 (class 0 OID 24713)
-- Dependencies: 227
-- Data for Name: fix_classifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fix_classifications (id, name, name_uz, name_ru) FROM stdin;
1	Literary Source Studies	Adabiy manbashunoslik	Литературное источниковедение
2	Literary Theory	Adabiyot nazariyasi	Теория литературы
3	Applied and Computational Linguistics	Amaliy va kompyuter lingvistikasi	Прикладная и компьютерная лингвистика
4	Psychology of Religion	Din psixologiyasi	Психология религии
5	Theory and Methodology of E-learning	Elektron taʼlim nazariyasi va metodikasi	Теория и методика электронного обучения
6	Ethnopsychology	Etnopsixologiya	Этнопсихология
7	Folklore Studies	Folklorshunoslik	Фольклористика
8	Military Journalism	Harbiy jurnalistika	Военная журналистика
9	Social Pedagogy	Ijtimoiy pedagogika	Социальная педагогика
10	Social Psychology	Ijtimoiy psixologiya	Социальная психология
11	Psychology of Human Professional Activity	Inson kasbiy faoliyati psixologiyasi	Психология профессиональной деятельности человека
12	Internet Journalism	Internet jurnalistikasi	Интернет-журналистика
13	Theory and Methodology of Vocational Education	Kasb-hunar taʼlimi nazariyasi va metodikasi	Теория и методика профессионального образования
14	Cognitive Linguistics	Kognitiv lingvistika	Когнитивная лингвистика
15	Comparative Studies	Komparativistika	Компаративистика
16	Issues of Comparative Studies	Komparativistika masalalari	Вопросы компаративистики
17	Theory and Methodology of Preschool Education	Maktabgacha taʼlim va tarbiya nazariyasi va metodikasi	Теория и методика дошкольного образования
18	Textual Studies	Matnshunoslik	Текстология
19	Special Pedagogy	Maxsus pedagogika	Специальная педагогика
20	Neurolinguistics	Neyrolingvistika	Нейролингвистика
21	Mass Media Journalism	Ommaviy axborot vositalari jurnalistikasi	Журналистика средств массовой информации
22	Literature of Asian and African Peoples	Osiyo va Afrika xalqlari adabiyoti	Литература народов Азии и Африки
23	Languages of Asian and African Peoples	Osiyo va Afrika xalqlari tili	Языки народов Азии и Африки
24	History of Pedagogical Teachings	Pedagogik taʼlimotlar tarixi	История педагогических учений
25	Pedagogical Theory	Pedagogika nazariyasi	Педагогическая теория
26	Pragmalinguistics	Pragmalingvistika	Прагмалингвистика
27	Psychophysiology	Psixofiziologiya	Психофизиология
28	Psycholinguistics	Psixolingvistika	Психолингвистика
29	History and Theory of Psychology	Psixologiya tarixi va nazariyasi	История и теория психологии
30	Comparative Literature Studies	Qiyosiy adabiyotshunoslik	Сравнительное литературоведение
31	Karakalpak Literature	Qoraqalpoq adabiyoti	Каракалпакская литература
32	Karakalpak Language	Qoraqalpoq tili	Каракалпакский язык
33	Radio Journalism	Radio jurnalistika	Радиожурналистика
34	Developmental Psychology	Rivojlanish psixologiyasi	Психология развития
35	Art Journalism	San'at jurnalistikasi	Арт-журналистика
36	Travel Journalism	Sayohat jurnalistikasi	Туристическая журналистика
37	Sociolinguistics	Sotsiolinvistika	Социолингвистика
38	Sports Journalism	Sport jurnalistikasi	Спортивная журналистика
39	Theory and Methodology of Education	Taʼlim va tarbiya nazariyasi va metodikasi	Теория и методика образования
40	Management in Education	Taʼlimda menejment	Менеджмент в образовании
41	TV Journalism	Telejurnalistika	Тележурналистика
42	Medical and Special Psychology	Tibbiy va maxsus psixologiya	Медицинская и специальная психология
43	Language Theory	Til nazariyasi	Теория языка
44	General Psychology	Umumiy psixologiya	Общая психология
45	Literature of European, American and Australian Peoples	Yevropa, Amerika va Avstraliya xalqlari adabiyoti	Литература народов Европы, Америки и Австралии
46	Languages of European, American and Australian Peoples	Yevropa, Amerika va Avstraliya xalqlari tili	Языки народов Европы, Америки и Австралии
47	Age and Pedagogical Psychology	Yosh va pedagogik psixologiya	Возрастная и педагогическая психология
48	Uzbek Literature	Oʻzbek adabiyoti	Узбекская литература
49	Uzbek Language	Oʻzbek tili	Узбекский язык
50	Personality Psychology	Shaxs psixologiyasi	Психология личности
51	Comparative Translation Studies	Chogʻishtirma tarjimashunoslik	Сравнительное переводоведение
52	Comparative Linguistics	Chogʻishtirma tilshunoslik	Сравнительное языкознание
\.


--
-- TOC entry 5128 (class 0 OID 24719)
-- Dependencies: 229
-- Data for Name: fix_country; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fix_country (id, name, name_uz, name_ru, created_at) FROM stdin;
82	Afghanistan	Afg'oniston	Афганистан	1739573591
83	Albania	Albaniya	Албания	1739573591
84	Algeria	Jazoir	Алжир	1739573591
85	Andorra	Andorra	Андорра	1739573591
86	Angola	Angola	Ангола	1739573591
87	Argentina	Argentina	Аргентина	1739573591
88	Armenia	Armaniston	Армения	1739573591
89	Australia	Avstraliya	Австралия	1739573591
90	Austria	Avstriya	Австрия	1739573591
91	Azerbaijan	Ozarbayjon	Азербайджан	1739573591
92	Bahamas	Bagama orollari	Багамские острова	1739573591
93	Bahrain	Bahrayn	Бахрейн	1739573591
94	Bangladesh	Bangladesh	Бангладеш	1739573591
95	Barbados	Barbados	Барбадос	1739573591
96	Belarus	Belarus	Беларусь	1739573591
97	Belgium	Belgiya	Бельгия	1739573591
98	Belize	Beliz	Белиз	1739573591
99	Benin	Benin	Бенин	1739573591
100	Bhutan	Butan	Бутан	1739573591
101	Bolivia	Boliviya	Боливия	1739573591
102	Bosnia and Herzegovina	Bosniya va Gertsegovina	Босния и Герцеговина	1739573591
103	Botswana	Botsvana	Ботсвана	1739573591
104	Brazil	Braziliya	Бразилия	1739573591
105	Brunei	Bruney	Бруней	1739573591
106	Bulgaria	Bolgariya	Болгария	1739573591
107	Burkina Faso	Burkina-Faso	Буркина-Фасо	1739573591
108	Burundi	Burundi	Бурунди	1739573591
109	Cambodia	Kambodja	Камбоджа	1739573591
110	Cameroon	Kamerun	Камерун	1739573591
111	Canada	Kanada	Канада	1739573591
112	Cape Verde	Kabo-Verde	Кабо-Верде	1739573591
113	Central African Republic	Markaziy Afrika Respublikasi	Центральноафриканская Республика	1739573591
114	Chad	Chad	Чад	1739573591
115	Chile	Chili	Чили	1739573591
116	China	Xitoy	Китай	1739573591
117	Colombia	Kolumbiya	Колумбия	1739573591
118	Comoros	Komor orollari	Коморские острова	1739573591
119	Congo	Kongo	Конго	1739573591
120	Costa Rica	Kosta-Rika	Коста-Рика	1739573591
121	Croatia	Xorvatiya	Хорватия	1739573591
122	Cuba	Kuba	Куба	1739573591
123	Cyprus	Kipr	Кипр	1739573591
124	Czech Republic	Chexiya	Чехия	1739573591
125	Denmark	Daniya	Дания	1739573591
126	Djibouti	Jibuti	Джибути	1739573591
127	Dominica	Dominika	Доминика	1739573591
128	Dominican Republic	Dominikan Respublikasi	Доминиканская Республика	1739573591
129	East Timor	Sharqiy Timor	Восточный Тимор	1739573591
130	Ecuador	Ekvador	Эквадор	1739573591
131	Egypt	Misr	Египет	1739573591
132	El Salvador	El-Salvador	Сальвадор	1739573591
133	Equatorial Guinea	Ekvatorial Gvineya	Экваториальная Гвинея	1739573591
134	Eritrea	Eritreya	Эритрея	1739573591
135	Estonia	Estoniya	Эстония	1739573591
136	Eswatini	Esvatini	Эсватини	1739573591
137	Ethiopia	Efiopiya	Эфиопия	1739573591
138	Fiji	Fiji	Фиджи	1739573591
139	Finland	Finlandiya	Финляндия	1739573591
140	France	Fransiya	Франция	1739573591
141	Gabon	Gabon	Габон	1739573591
142	Gambia	Gambiya	Гамбия	1739573591
143	Georgia	Gruziya	Грузия	1739573591
144	Germany	Germaniya	Германия	1739573591
145	Ghana	Gana	Гана	1739573591
146	Greece	Gretsiya	Греция	1739573591
147	Grenada	Grenada	Гренада	1739573591
148	Guatemala	Gvatemala	Гватемала	1739573591
149	Guinea	Gvineya	Гвинея	1739573591
150	Guinea-Bissau	Gvineya-Bisau	Гвинея-Бисау	1739573591
151	Guyana	Gayana	Гайана	1739573591
152	Haiti	Gaiti	Гаити	1739573591
153	Honduras	Gonduras	Гондурас	1739573591
154	Hungary	Vengriya	Венгрия	1739573591
155	Iceland	Islandiya	Исландия	1739573591
156	India	Hindiston	Индия	1739573591
157	Indonesia	Indoneziya	Индонезия	1739573591
158	Iran	Eron	Иран	1739573591
159	Iraq	Iroq	Ирак	1739573591
160	Ireland	Irlandiya	Ирландия	1739573591
161	Israel	Isroil	Израиль	1739573591
162	Italy	Italiya	Италия	1739573591
163	Jamaica	Yamayka	Ямайка	1739573591
164	Japan	Yaponiya	Япония	1739573591
165	Jordan	Iordaniya	Иордания	1739573591
166	Kazakhstan	Qozog'iston	Казахстан	1739573591
167	Kenya	Keniya	Кения	1739573591
168	Kiribati	Kiribati	Кирибати	1739573591
169	Kuwait	Quvayt	Кувейт	1739573591
170	Kyrgyzstan	Qirg'iziston	Киргизия	1739573591
171	Laos	Laos	Лаос	1739573591
172	Latvia	Latviya	Латвия	1739573591
173	Lebanon	Livan	Ливан	1739573591
174	Lesotho	Lesoto	Лесото	1739573591
175	Liberia	Liberiya	Либерия	1739573591
176	Libya	Liviya	Ливия	1739573591
177	Liechtenstein	Lixtenshteyn	Лихтенштейн	1739573591
178	Lithuania	Litva	Литва	1739573591
179	Luxembourg	Lyuksemburg	Люксембург	1739573591
180	Madagascar	Madagaskar	Мадагаскар	1739573591
181	Malawi	Malavi	Малави	1739573591
182	Malaysia	Malayziya	Малайзия	1739573591
183	Maldives	Maldiv orollari	Мальдивы	1739573591
184	Mali	Mali	Мали	1739573591
185	Malta	Malta	Мальта	1739573591
186	Marshall Islands	Marshall orollari	Маршалловы острова	1739573591
187	Mauritania	Mavritaniya	Мавритания	1739573591
188	Mauritius	Mavrikiy	Маврикий	1739573591
189	Mexico	Meksika	Мексика	1739573591
190	Micronesia	Mikroneziya	Микронезия	1739573591
191	Moldova	Moldova	Молдова	1739573591
192	Monaco	Monako	Монако	1739573591
193	Mongolia	Mo'g'uliston	Монголия	1739573591
194	Montenegro	Chernogoriya	Черногория	1739573591
195	Morocco	Marokash	Марокко	1739573591
196	Mozambique	Mozambik	Мозамбик	1739573591
197	Myanmar	Myanma	Мьянма	1739573591
198	Namibia	Namibiya	Намибия	1739573591
199	Nauru	Nauru	Науру	1739573591
200	Nepal	Nepal	Непал	1739573591
201	Netherlands	Niderlandiya	Нидерланды	1739573591
202	New Zealand	Yangi Zelandiya	Новая Зеландия	1739573591
203	Nicaragua	Nikaragua	Никарагуа	1739573591
204	Niger	Niger	Нигер	1739573591
205	Nigeria	Nigeriya	Нигерия	1739573591
206	North Korea	Shimoliy Koreya	Северная Корея	1739573591
207	North Macedonia	Shimoliy Makedoniya	Северная Македония	1739573591
208	Norway	Norvegiya	Норвегия	1739573591
209	Oman	Ummon	Оман	1739573591
210	Pakistan	Pokiston	Пакистан	1739573591
211	Palau	Palau	Палау	1739573591
212	Palestine	Falastin	Палестина	1739573591
213	Panama	Panama	Панама	1739573591
214	Papua New Guinea	Papua-Yangi Gvineya	Папуа-Новая Гвинея	1739573591
215	Paraguay	Paragvay	Парагвай	1739573591
216	Peru	Peru	Перу	1739573591
217	Philippines	Filippin	Филиппины	1739573591
218	Poland	Polsha	Польша	1739573591
219	Portugal	Portugaliya	Португалия	1739573591
220	Qatar	Qatar	Катар	1739573591
221	Romania	Ruminiya	Румыния	1739573591
222	Russia	Rossiya	Россия	1739573591
223	Rwanda	Ruanda	Руанда	1739573591
224	Saint Kitts and Nevis	Sent-Kits va Nevis	Сент-Китс и Невис	1739573591
225	Saint Lucia	Sent-Lyusiya	Сент-Люсия	1739573591
226	Saint Vincent and the Grenadines	Sent-Vinsent va Grenadinlar	Сент-Винсент и Гренадины	1739573591
227	Samoa	Samoa	Самоа	1739573591
228	San Marino	San-Marino	Сан-Марино	1739573591
229	Sao Tome and Principe	San-Tome va Prinsipi	Сан-Томе и Принсипи	1739573591
230	Saudi Arabia	Saudiya Arabistoni	Саудовская Аравия	1739573591
231	Senegal	Senegal	Сенегал	1739573591
232	Serbia	Serbiya	Сербия	1739573591
233	Seychelles	Seyshel orollari	Сейшельские острова	1739573591
234	Sierra Leone	Syerra-Leone	Сьерра-Леоне	1739573591
235	Singapore	Singapur	Сингапур	1739573591
236	Slovakia	Slovakiya	Словакия	1739573591
237	Slovenia	Sloveniya	Словения	1739573591
238	Solomon Islands	Solomon orollari	Соломоновы острова	1739573591
239	Somalia	Somali	Сомали	1739573591
240	South Africa	Janubiy Afrika	ЮАР	1739573591
241	South Korea	Janubiy Koreya	Южная Корея	1739573591
242	South Sudan	Janubiy Sudan	Южный Судан	1739573591
243	Spain	Ispaniya	Испания	1739573591
244	Sri Lanka	Shri-Lanka	Шри-Ланка	1739573591
245	Sudan	Sudan	Судан	1739573591
246	Suriname	Surinam	Суринам	1739573591
247	Sweden	Shvetsiya	Швеция	1739573591
248	Switzerland	Shveytsariya	Швейцария	1739573591
249	Syria	Suriya	Сирия	1739573591
250	Taiwan	Tayvan	Тайвань	1739573591
251	Tajikistan	Tojikiston	Таджикистан	1739573591
252	Tanzania	Tanzaniya	Танзания	1739573591
253	Thailand	Tailand	Таиланд	1739573591
254	Togo	Togo	Того	1739573591
255	Tonga	Tonga	Тонга	1739573591
256	Trinidad and Tobago	Trinidad va Tobago	Тринидад и Тобаго	1739573591
257	Tunisia	Tunis	Тунис	1739573591
258	Turkey	Turkiya	Турция	1739573591
259	Turkmenistan	Turkmaniston	Туркменистан	1739573591
260	Tuvalu	Tuvalu	Тувалу	1739573591
261	Uganda	Uganda	Уганда	1739573591
262	Ukraine	Ukraina	Украина	1739573591
263	United Arab Emirates	BAA	ОАЭ	1739573591
264	United Kingdom	Buyuk Britaniya	Великобритания	1739573591
265	United States	AQSh	США	1739573591
266	Uruguay	Urugvay	Уругвай	1739573591
267	Uzbekistan	O'zbekiston	Узбекистан	1739573591
268	Vanuatu	Vanuatu	Вануату	1739573591
269	Vatican City	Vatikan	Ватикан	1739573591
270	Venezuela	Venesuela	Венесуэла	1739573591
271	Vietnam	Vetnam	Вьетнам	1739573591
272	Yemen	Yaman	Йемен	1739573591
273	Zambia	Zambiya	Замбия	1739573591
274	Zimbabwe	Zimbabve	Зимбабве	1739573591
\.


--
-- TOC entry 5130 (class 0 OID 24725)
-- Dependencies: 231
-- Data for Name: fix_issue_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fix_issue_categories (id, alias, name, name_uz, name_ru) FROM stdin;
1	phd	PhD Series	PhD Seriyasi	Серия для докторантуры
2	masters	Masters Series	Magistratura seriyasi	Серия магистратуры
3	special	Special Issues	Maxsus sonlar	Специальные выпуски
\.


--
-- TOC entry 5132 (class 0 OID 24731)
-- Dependencies: 233
-- Data for Name: issues; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issues (id, title, title_uz, title_ru, vol_no, issue_no, year, category, shortinfo, shortinfo_uz, shortinfo_ru, price, price_uz, price_ru, subscription_enable, is_paid, cover_image, created_at) FROM stdin;
13	Philology Matters	Filologiya Masalalari	Проблемы филологии	1	2	2025		EDITORIAL BOARD: Roviyajon ABDULLAEVA, Michele BERNARDINI (Italy), Nikolay BOLDIREV (Russia), Guli ERGASHEVA, Dilbar DJUMANOVA, Sobir HAMZAEV, Svetlana IM, Ilyos ISMAILOV, Klimentina ISMAILOVA, Iroda KAXAROVA, Anatoliy LIXODZIEVSKIY, Ono MASAKI (Japan), Abdurakhim NASIROV, Kesava PANIKKAR (India), Richard PATERSON (London), Rodmonga POTAPOVA (Moscow), Khalim SAIDOV, Ilkhom TUKHTASINOV, Makhliyo UMAROVA, Khikmatilla URAZBAEV, Daniel CHARTIER (Canada), Hans-Werner HUNEKE (Germany), Akmal YULDASHEV, Thierry ZARCONE (France), Jamoliddin YAKUBOV	TАHRIR HАY’АTI: Roviyajon ABDULLAYEVA, Mishel BERNАRDINI (Italiya), Nikolay BOLDIREV (Rossiya), Guli ERGАSHEVА, Dilbar JUMАNOVА, Terri ZАRKON (Fransiya), Svetlana IM, Ilyos ISMOILOV, Klimentina ISMAILOVA, Iroda KAXAROVA, Anatoliy LIXODZIYEVSKIY, Ono MАSАKI (Yaponiya), Abdurahim NOSIROV, Kesava PАNIKKАR (Hindiston), Richard PETERSON (London), Rodmonga POTАPOVА (Moskva), Halim SАIDOV, Ilhom TO‘XTАSINOV, Maxliyo UMAROVA, Hikmatillo URAZBAYEV, Akmal YULDASHEV, Hans-Verner XUNEKE (Germaniya), Daniel CHARTE (Kanada), Sobir HAMZAYEV, Jamoliddin YOQUBOV	РЕДАКЦИОННАЯ КОЛЛЕГИЯ: Ровияжон АБДУЛЛАЕВА, Мишель БЕРНАРДИНИ (Италия), Николай БОЛДЫРЕВ (Россия), Дилбар ДЖУМАНОВА, Тьерри ЗАРКОН (Франция), Светлана ИМ, Илёс ИСМОИЛОВ, Климентина ИСМАИЛОВА, Ирода КАХАРОВА, Анатолий ЛИХОДЗИЕВСКИЙ, Оно МАСАКИ (Япония), Абдурахим НОСИРОВ, Кесава ПАНИККАР (Индия), Ричард ПЕТЕРСОН (Лондон), Родмонга ПОТАПОВА (Москва), Халим САИДОВ, Илхом ТУХТАСИНОВ, Махлиё УМАРОВА, Хикматилло УРАЗБАЕВ, Ханс-Вернер ХУНЕКЕ (Германия), Собир ХАМЗАЕВ, Даниэль ЧАРТЬЕ (Канада), Гули ЭРГАШЕВА, Акмал ЮЛДАШЕВ, Жамолиддин ЁКУБОВ	0	0	0	f	f	/static/uploads/issues/2025/08/33ea92b363094b88ad0158002a9d1255.jpg	\N
\.


--
-- TOC entry 5134 (class 0 OID 24739)
-- Dependencies: 235
-- Data for Name: news; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.news (id, type, title, title_ru, title_uz, content, content_ru, content_uz, status, created_at, published_at, author_id, cover_image) FROM stdin;
2	announcement	еуц	3	Theoretical and Applied Linguistics (UZ) - 2024	<p>qweqw</p>	<p>eqw</p>	<p>qwee</p>	draft	1748205430	1735671600	\N	\N
1	news	еуц	ецуе	цуе	<p>цуе</p>	<p>цуе</p>	<p>цуе</p>	published	1748075862	1747940400	\N	\N
3	news	New Research on Linguistic Markers in Story Recall	Новое исследование лингвистических маркеров в воспроизведении историй	Hikoya eslashda lingvistik belgilar bo'yicha yangi tadqiqot	Recent studies have shown significant correlations between linguistic markers and memory recall patterns in narrative comprehension.	Недавние исследования показали значительные корреляции между лингвистическими маркерами и паттернами воспроизведения памяти при понимании нарратива.	So'nggi tadqiqotlar narrativni tushunishda lingvistik belgilar va xotira qayta tiklash naqshlari o'rtasida muhim korrelyatsiyalarni ko'rsatdi.	published	1748206384	1748119984	1	\N
4	news	Digital Humanities Conference 2024 Highlights	Основные моменты конференции по цифровой гуманитаристике 2024	Raqamli gumanitar fanlar konferentsiyasi 2024 asosiy lahzalari	The annual Digital Humanities Conference showcased groundbreaking research in computational linguistics and text analysis.	Ежегодная конференция по цифровой гуманитаристике продемонстрировала прорывные исследования в области компьютерной лингвистики и анализа текста.	Yillik raqamli gumanitar fanlar konferentsiyasi kompyuter lingvistikasi va matn tahlili sohasidagi ilg'or tadqiqotlarni namoyish etdi.	published	1748206384	1748033584	1	\N
5	news	Journal Impact Factor Update	Обновление импакт-фактора журнала	Jurnal ta'sir omili yangilanishi	We are pleased to announce that our journal's impact factor has increased significantly this year.	Мы рады сообщить, что импакт-фактор нашего журнала значительно вырос в этом году.	Bizning jurnalimizning ta'sir omili bu yil sezilarli darajada oshganini e'lon qilishdan mamnunmiz.	published	1748206384	1747947184	1	\N
6	announcement	Call for Papers: Special Issue on Computational Linguistics	Приглашение к публикации: Специальный выпуск по компьютерной лингвистике	Maqolalar uchun chaqiruv: Kompyuter lingvistikasi bo'yicha maxsus son	We invite submissions for our upcoming special issue focusing on recent advances in computational linguistics and natural language processing.	Мы приглашаем к подаче статей для нашего предстоящего специального выпуска, посвященного последним достижениям в области компьютерной лингвистики и обработки естественного языка.	Kompyuter lingvistikasi va tabiiy tilni qayta ishlashdagi so'nggi yutuqlarga bag'ishlangan maxsus sonimiz uchun maqolalar taqdim etishga taklif qilamiz.	published	1748206384	1748119984	1	\N
7	announcement	Extended Deadline: Manuscript Submissions	Продленный срок: Подача рукописей	Uzaytirilgan muddat: Qo'lyozma taqdim etish	Due to high interest, we have extended the submission deadline for our current issue to the end of this month.	В связи с большим интересом мы продлили срок подачи статей для текущего выпуска до конца этого месяца.	Katta qiziqish tufayli joriy son uchun maqola taqdim etish muddatini shu oy oxirigacha uzaytirdik.	published	1748206384	1748033584	1	\N
8	announcement	New Editorial Board Members	Новые члены редакционной коллегии	Tahririyat hay'atining yangi a'zolari	We are excited to welcome three distinguished scholars to our editorial board, bringing expertise in sociolinguistics and discourse analysis.	Мы рады приветствовать трех выдающихся ученых в нашей редакционной коллегии, которые привносят экспертизу в области социолингвистики и дискурс-анализа.	Sotsiolingvistika va diskurs tahlili sohasida tajribaga ega bo'lgan uchta taniqli olimni tahririyat hay'atimizga qabul qilishdan xursandmiz.	published	1748206384	1747947184	1	\N
\.


--
-- TOC entry 5136 (class 0 OID 24747)
-- Dependencies: 237
-- Data for Name: pages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pages (id, alias, title, title_uz, title_ru, content, content_uz, content_ru, last_update, created_at) FROM stdin;
8	editorial_board	editorial_board	\N	\N	editorial_board	\N	\N	0	\N
11	latest_articles	latest_articles	\N	\N	latest_articles	\N	\N	0	\N
12	current_issue	current_issue	\N	\N	current_issue	\N	\N	0	\N
13	all_issues	all_issues	\N	\N	all_issues	\N	\N	0	\N
14	special_issues	special_issues	\N	\N	special_issues	\N	\N	0	\N
15	collections	collections	\N	\N	collections	\N	\N	0	\N
16	most_read_articles	most_read_articles	\N	\N	most_read_articles	\N	\N	0	\N
17	most_cited_articles	most_cited_articles	\N	\N	most_cited_articles	\N	\N	0	\N
1	submission_guidelines	Submission Guidelines	Maqola yuborish bo'yicha ko'rsatmalar	Руководство по подаче статей	\n        <h4 class="text-lg font-medium mb-4">General Guidelines</h4>\n        <p class="mb-4">Please read these guidelines carefully before submitting your manuscript...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Umumiy ko'rsatmalar</h4>\n        <p class="mb-4">Iltimos, qo'lyozmangizni yuborishdan oldin ushbu ko'rsatmalarni diqqat bilan o'qib chiqing...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Общие указания</h4>\n        <p class="mb-4">Пожалуйста, внимательно прочтите эти указания перед отправкой рукописи...</p>\n        	1739770612	\N
2	author_instructions	Instructions for Authors	Mualliflar uchun ko'rsatmalar	Инструкции для авторов	\n        <h4 class="text-lg font-medium mb-4">Manuscript Preparation</h4>\n        <p class="mb-4">Follow these instructions to prepare your manuscript...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Qo'lyozmani tayyorlash</h4>\n        <p class="mb-4">Qo'lyozmangizni tayyorlash uchun ushbu ko'rsatmalarga amal qiling...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Подготовка рукописи</h4>\n        <p class="mb-4">Следуйте этим инструкциям для подготовки вашей рукописи...</p>\n        	1739770612	\N
3	editorial_policy	Editorial Policy	Tahririyat siyosati	Редакционная политика	\n        <h4 class="text-lg font-medium mb-4">Publication Ethics</h4>\n        <p class="mb-4">Our journal follows strict ethical guidelines...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Nashr etish etikasi</h4>\n        <p class="mb-4">Bizning jurnal qat'iy etik ko'rsatmalarga amal qiladi...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Публикационная этика</h4>\n        <p class="mb-4">Наш журнал следует строгим этическим принципам...</p>\n        	1739770612	\N
4	site_editing_services	Site Editing Services	Sayt tahrirlash xizmatlari	Услуги редактирования сайта	\n        <h4 class="text-lg font-medium mb-4">Our Editing Services</h4>\n        <p class="mb-4">We offer professional editing services...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Bizning tahrirlash xizmatlarimiz</h4>\n        <p class="mb-4">Biz professional tahrirlash xizmatlarini taqdim etamiz...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Наши услуги редактирования</h4>\n        <p class="mb-4">Мы предлагаем профессиональные услуги редактирования...</p>\n        	1739770612	\N
5	journal_metrics	Journal Metrics	Jurnal ko'rsatkichlari	Показатели журнала	\n        <h4 class="text-lg font-medium mb-4">Impact and Metrics</h4>\n        <p class="mb-4">View our journal's performance metrics...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Ta'sir va ko'rsatkichlar</h4>\n        <p class="mb-4">Jurnalimizning samaradorlik ko'rsatkichlarini ko'ring...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Влияние и показатели</h4>\n        <p class="mb-4">Просмотрите показатели эффективности нашего журнала...</p>\n        	1739770612	\N
6	aims_scope	Aims and Scope	Maqsad va vazifalar	Цели и задачи	\n        <h4 class="text-lg font-medium mb-4">Journal Focus</h4>\n        <p class="mb-4">Our journal focuses on advancing knowledge in...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Jurnal yo'nalishi</h4>\n        <p class="mb-4">Bizning jurnal bilimlarni rivojlantirishga qaratilgan...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Направление журнала</h4>\n        <p class="mb-4">Наш журнал направлен на развитие знаний в области...</p>\n        	1739770612	\N
7	journal_info	Journal Information	Jurnal haqida ma'lumot	Информация о журнале	\n        <h4 class="text-lg font-medium mb-4">About Our Journal</h4>\n        <p class="mb-4">Learn more about our journal's history and mission...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Bizning jurnal haqida</h4>\n        <p class="mb-4">Jurnalimizning tarixi va vazifasi haqida ko'proq bilib oling...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">О нашем журнале</h4>\n        <p class="mb-4">Узнайте больше об истории и миссии нашего журнала...</p>\n        	1739770612	\N
9	news_calls	News and Calls for Papers	Yangiliklar va maqolalar uchun chaqiruvlar	Новости и приглашения к публикации	\n        <h4 class="text-lg font-medium mb-4">Latest Updates</h4>\n        <p class="mb-4">Stay informed about our latest news and opportunities...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">So'nggi yangilanishlar</h4>\n        <p class="mb-4">Bizning so'nggi yangiliklar va imkoniyatlardan xabardor bo'ling...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Последние обновления</h4>\n        <p class="mb-4">Будьте в курсе наших последних новостей и возможностей...</p>\n        	1739770612	\N
10	conferences	Conferences	Konferentsiyalar	Конференции	\n        <h4 class="text-lg font-medium mb-4">Upcoming Events</h4>\n        <p class="mb-4">Find information about upcoming conferences and events...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Kelgusi tadbirlar</h4>\n        <p class="mb-4">Kelgusi konferentsiyalar va tadbirlar haqida ma'lumot oling...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Предстоящие события</h4>\n        <p class="mb-4">Найдите информацию о предстоящих конференциях и мероприятиях...</p>\n        	1739770612	\N
18	for_uzgumya_researchers	For UzGUMYA Researchers	UzDJTU tadqiqotchilari uchun	Для исследователей УзГУМЯ	\n        <h4 class="text-lg font-medium mb-4">Special Access</h4>\n        <p class="mb-4">Information for UzGUMYA affiliated researchers...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Maxsus kirish</h4>\n        <p class="mb-4">UzDJTU bilan bog'liq tadqiqotchilar uchun ma'lumot...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Специальный доступ</h4>\n        <p class="mb-4">Информация для исследователей, связанных с УзГУМЯ...</p>\n        	1739770612	\N
19	for_all_researchers	For All Researchers	Barcha tadqiqotchilar uchun	Для всех исследователей	\n        <h4 class="text-lg font-medium mb-4">General Access</h4>\n        <p class="mb-4">Information for all researchers...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Umumiy kirish</h4>\n        <p class="mb-4">Barcha tadqiqotchilar uchun ma'lumot...</p>\n        	\n        <h4 class="text-lg font-medium mb-4">Общий доступ</h4>\n        <p class="mb-4">Информация для всех исследователей...</p>\n        	1739770612	\N
\.


--
-- TOC entry 5138 (class 0 OID 24753)
-- Dependencies: 239
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (id, user_id, status, currency, payment_type, payment_date, amount, ids, proof, note, created_at) FROM stdin;
\.


--
-- TOC entry 5140 (class 0 OID 24761)
-- Dependencies: 241
-- Data for Name: publication_citations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.publication_citations (id, publication_id, title, authors, doi, doi_link, wos_link, scopus_link, gscholar_link, created_at) FROM stdin;
\.


--
-- TOC entry 5142 (class 0 OID 24767)
-- Dependencies: 243
-- Data for Name: publication_figures; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.publication_figures (id, publication_id, title, filepath, order_id, created_at) FROM stdin;
\.


--
-- TOC entry 5144 (class 0 OID 24773)
-- Dependencies: 245
-- Data for Name: publication_parts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.publication_parts (id, publication_id, title, content, order_id, created_at) FROM stdin;
10	119	KIRISH	<p>Boshqa tillarda boʻlgani singari oʻzbek tilida ham hodisa va predmetlarning muayyan guruh va sinf belgilarini yaratgan yoki umumiy qoʻllanishga kiritgan xalq tilidan dunyoning aksariyat tillari tomonidan oʻzlashtirilgan leksik birliklar mavjud.</p><p>&nbsp;</p><p>Tilshunoslarning ta’kidlashlaricha, “sotsiolingvistik o‘zgarishlar tufayli va til aloqalari natijasida o‘zbek tili nafaqat lug‘at boyligi, balki sintaktik va stilistik tuzilishini ham boyitadi” [Abduazizov, 2010]. So‘z biror narsa, bu soʻzni olgan odamlarning voqeligiga xos bo‘lgan hodisani nomlaganda leksik jihatdan o‘zlashtirilgan hisoblanadi va uning ma’nosida chet tilining kelib chiqishini koʻrsatadigan hech narsa qolmaydi. Masalan, rus tilidan oʻzlashtirilgan muzey, universitet, kollej, litsey, sirk, forpost, samolyot, skuter va boshqa ko‘plab soʻzlar hamma uchun tushunarli va ularning ba’zilari xalqaro xarakterga ega va o‘zbek tilining lug‘at tarkibiga kiradi. So‘nggi yillarda milliy madaniy an’analarning tiklanish tendensiyalari munosabati bilan bir qator xorijiy so‘zlardan xalos bo‘lish, oldingi o‘zlashuvlar o‘rniga umumiy turkiy so‘zlar va arab so‘zlaridan foydalanish istagi kuchaymoqda. Lekin ogʻzaki nutqda ularning parallel qoʻllanilishi kuzatiladi.</p><p>&nbsp;</p><p>Butun lingvistik mexanizmda markaziy o‘rinni egallagan leksik birliklar boshqa til birliklariga nisbatan eng koʻp funksiyalarga ega. Muayyan funksiyaga ega boʻlish, biror narsani amalga oshirish uchun moʻljallangan bo‘lishni anglatadi. Leksik birliklarning vazifalari, birinchidan, mazmuni, ikkinchidan, leksik birliklarga xoslik darajasi bilan bir-biridan farq qiladi. Mazmun nuqtayi nazaridan ayrim funksiyalar leksik birliklarning tevarak-atrofdagi olam predmetlariga munosabatini aks ettiradi va shuning uchun ularni tashqi deb atash mumkin, boshqalari esa leksik birliklarning bir-biriga va til tizimiga munosabatini – ichki funksiyalarini aks ettiradi. Birinchisiga nominativ, umumlashtiruvchi – kognitiv, axborot – akkumulyator, deistik, hissiy, ramziy, kommunikativ, kontakt, estetik kiradi. Ikkinchisi – sintezlovchi, stilistik, metalingvistik, konstruktiv va farqlovchi. Turli funksiyalarning leksik birliklarga xosligi darajasiga qarab, ularni toʻgʻri va notoʻgʻriga boʻlish mumkin. Leksik birliklarning toʻgʻri ishlashi, ular asosiy tashuvchisi bo‘lgan vazifasi deyiladi. Boshqacha qilib aytadigan boʻlsak, toʻgʻri funksiyalarga, birinchi navbatda, leksik birliklarga xos bo‘lgan funksiyalar kiradi va shundan keyingina boshqa ba’zi bir til birliklariga xosdir. Leksik birliklarning tegishli vazifalari nominativ, umumlashtiruvchi – idrok, axborot – akkumulyator, deyktik, emotiv, ramziy, sintezlovchi, stilistik va metalingvistikdir. Notoʻgʻri – bu leksik birliklarning shunday funksiyasi boʻlib, ularning asosiy tashuvchisi leksiklardan tashqari boshqa har qanday til birliklari hisoblanadi. Boshqacha qilib aytganda, notoʻgʻri funksiyalarga, birinchi navbatda, ba’zi boshqa lingvistik birliklarga xos bo‘lgan funksiyalar kiradi. Leksik birliklarning birinchi va asosiy vazifasi obyektlar va xususiyatlarni nomlash funksiyasidir, ya’ni, nominativ (vakillik) funksiyasi. Leksik birliklar, birinchi navbatda, insonning atrofdagi voqelikni bilish natijalarini qayd etish uchun xizmat qiladi. Bu dunyoda harakat qilib, uni va oʻzini oʻylash, inson atrofdagi voqelikning tobora koʻproq yangi qismlarini aniqlaydi va ularning har biriga oʻziga xos nom beradi. Bu shuni anglatadiki, leksik birlik o‘zining tashqi ko‘rinishi bilan shaxs tomonidan aniqlangan va u tomonidan alohida deb tan olingan narsani nomlash zarurati bilan bogʻliq. Bu yerda soʻzlarda taqdim etilgan haqiqat nafaqat haqiqatda mavjud boʻlganlardan iboratligiga e’tibor berish kerak, balki tashqi sezgilarimiz tomonidan idrok etiladigan narsalarga ham e’tibor qaratishimiz lozim. Ular bilan bir qatorda, u butunlay virtual tabiatning juda koʻp alohida qismlarini ham o‘z ichiga oladi. Bunday obyektlar aqliy artefaktlardir. Ular, birinchidan, haqiqatda mavjud boʻlgan subyektlarning aloqalari va bogʻliqliklarini, ularning mavjudlik, iste’molchi va boshqa xususiyatlarini, ikkinchidan, inson ma’naviy hayotining obyektiv xilma-xilligini aks ettiradi. Shu tarzda tushunilgan aqliy artefaktlar odamga qarama-qarshi bo‘lgan voqelikni tushunarli qiladi va unga nisbatan ancha do‘stona munosabatda boʻladi. 1. Nominativ funksiya ot, sifat, son, fe’l va ergash gaplarga aloqador leksik birliklarga xosdir. Atrofdagi voqelikni nomlash bilan bogʻliq muammolar onomasiologiya tomonidan ishlab chiqilgan. Onomasiologiya (yun. oposha – “nom” va logos – “fan”) – leksikologiyaning leksik birliklar yordamida voqelik obyektlarini belgilash vositalari, usullari, qoliplari va xususiyatlarini oʻrganadigan boʻlim.</p><p>&nbsp;</p><p>Lingvistik adabiyotlarda onomasiologiyaning asoslari XX asr boshlarida qoʻyilganligi haqidagi fikrlarni uchratish mumkin. XX asrning oʻrtalarida “soʻzlar va narsalar” [Asatrian, 2009] ilmiy yoʻnalishiga mansub nemis olimlarining asarlarida mavjud. XX asr davomida onomasiologiyada yondashuv ruhida boʻlishiga qaramay, haqiqatdan ham bir qancha yutuqlarga erishildi. Leksik birliklarning ikkinchi muhim vazifasi – umumlashtiruvchi – idrok (ishoriy, tasniflovchi) vazifasidir. Leksik birlik odatda bitta aniq obyektni (xususiyatni) emas, balki obyektlarning (xususiyatlarning) butun sinfini nomlaydi. Masalan, kitob soʻzi oʻlchamidan, rangidan, matn qaysi tilda yozilganidan qat’i nazar, “ba’zi bir matn bilan bogʻlangan qogʻoz varaqlari koʻrinishidagi bosma ish” boʻlgan har qanday narsaning nomi sifatida xizmat qiladi. Leksik birlik obyektlarning (xususiyatlarning) butun sinfini nomlay olishi uchun u ushbu sinfni tashkil etuvchi barcha obyektlarda istisnosiz mavjud bo‘lgan kichik doiradagi atributlar bilan korrelyatsiya qilish xususiyatiga ega boʻlishi kerak. Miqdoriy nuqtayi nazardan, odatda muayyan sinfning obyektlarini (xususiyatlarini) boshqa barcha sinflar obyektlaridan (xususiyatlarini) ajrata olish uchun zarur boʻlgan koʻplab xususiyatlar mavjud. Binobarin, voqelikning har qanday faktini nomlash orqali leksik birlik bir vaqtning oʻzida uni tasniflaydi, ya’ni muayyan sinfga kiradi.&nbsp;<br><br>Nemis faylasufi E.Kassirer o‘z vaqtida nomlash va tasniflash o‘rtasidagi bog‘liqlikka e’tibor qaratgan edi: “Tasniflash inson tilining asosiy xususiyatlaridan biridir. Nomlash faktining oʻzi tasniflash jarayoniga asoslanadi. Buyum yoki harakatga nom berish, uni ma’lum bir tushunchalar sinfiga kiritish demakdir” [Kassirer, 1988]. Shunday qilib, leksik birliklarning kognitiv-umumlashtiruvchi funksiyasi ular tegishli tilda soʻzlashuvchi odamlarning bilish faoliyatini umumlashtirish va mustahkamlashga asoslanadi. Natijada inson ongida har bir leksik birlik oʻzi bildirgan narsa yoki xususiyat haqida ma’lum bir fikr bilan bogʻlanadi. Insonga ma’lum bo‘lgan barcha leksik birliklar bilan bogʻliq boʻlgan bunday gʻoyalar yigʻindisi uning atrofidagi real va virtual haqiqat haqidagi bilimini yoki ba’zan dunyoning lingvistik rasmini shakllantiradi. Agar nominativ funksiyaga muvofiq, leksik birlik atrofdagi voqelikning obyektlari va xususiyatlari bilan bogʻliq boʻlsa, umumlashtiruvchi-kognitiv funksiya ularning ushbu obyektlar va xususiyatlar haqidagi gʻoyalar bilan aloqasini ta’kidlaydi. Mashhur rus psixologi A.R. Luriya shunday deb yozadi: “Soʻz nafaqat predmetni bildiradi, balki obyektni tahlil qilish, avlodlarning tarixiy taraqqiyoti jarayonida shakllangan tajribani yetkazish kabi eng muhim vazifani ham bajaradi” [Luria, 1975]. Yuqoridagi fikr umumlashtiruvchi-kognitiv funksiyani ta’kidlab, leksik birliklarning yana bir chambarchas bogʻliq va juda muhim vazifasini, ya’ni axborot saqlashni ham ta’kidlaydi.</p><p>&nbsp;</p><p>Axborot-toʻplovchi yoki kümülatif – (“koʻpaytirish, toʻplash”dan) funksiya leksik birliklarning nomdagi obyekt bilan bogʻliq boʻlgan har xil turdagi ma’lumotlarni yozib olish, birlashtirish va ularning mazmunida toʻplash uchun ajoyib xususiyatini aks ettiradi. Boshqacha qilib aytadigan boʻlsak, leksik birlik xotiraga ega: u xuddi shimgich kabi, soʻzlovchilarning tegishli obyektga (xususiyatga) an’anaviy, ijtimoiy munosabati, ushbu obyektning (xususiyat) joylashuvi haqidagi barcha yakuniy, hissiy va boshqa ma’lumotlarni oʻzlashtiradi va saqlaydi. Natijada eng oddiy obyektlarni va juda muhim axloqiy, ijtimoiy va mafkuraviy koʻrsatmalarni bildiruvchi koʻplab leksik birliklarning madaniy va tarixiy “ifloslanishi” sodir boʻladi. Misol uchun, ruslar uchun poyezd soʻzi shunchaki “teplovoz tomonidan boshqariladigan birlashtirilgan temir yoʻl vagonlari poyezdi” emas. Umumlashtiruvchi – kognitiv (muhim, tasniflovchi) funksiyani aks ettiruvchi xususiyatlarning ushbu minimal roʻyxatiga qoʻshimcha ravishda, bu soʻz ruslar orasida tezyurar poyezd, yoʻlovchi poyezdi, uzoq masofali poyezd, elektr poyezd va an’anaviy poyezd turlari bilan bog‘liq. Ushbu turdagi poyezd yoʻlovchi vagonlari bilan, masalan, yumshoq vagon, docked/kupe, ajratilgan oʻrindiqli vagon, umumiy vagon va rus poeyzdlarining boshqa xususiyatlari bilan bog‘liq. Aynan axborotni saqlash funksiyasi leksik birliklarga milliy o‘zlikni, milliy madaniy-tarixiy an’analarni saqlash va uzatish vositasi bo‘lib xizmat qilish imkoniyatini beradi. Rus leksik birliklarining axborotni saqlash funksiyasini oʻrganishga Y.M. Vereshagin va V.G. Kostomarov muhim hissa qoʻshdi [Vereshchagin &amp; Kostomarov, 1990].</p><p>&nbsp;</p><p>Deyktik funksiya yoki oddiygina deyksis (yun. 1e1x1z – “ko‘rsatma”) soʻzlovchi yoki nutq momenti bilan u yoki bu tarzda bogʻliq boʻlgan narsa yoki belgilar bilan koʻrsatish, bogʻlash funksiyasidir. Deyksis quyidagilarni oʻz ichiga oladi: a) soʻzlovchi va tinglovchining koʻrsatkichi (men, sen, meniki, sizniki); b) nutq obyektining koʻrsatkichi (u, ular, uning va h.k.z.); d) nutq obyektining masofaviylik darajasining koʻrsatkichi (bu, bu yerda, u yerda); e) nutq obyektining vaqtinchalik va fazoviy lokalizatsiyasining koʻrsatkichi (bu yerda, hozir, u yerda, keyin). Deyktik vazifa, asosan, olmosh va ergash gaplarga xosdir. Ma’lumki, olmoshlar, boshqa muhim leksik birliklardan farqli oʻlaroq, obyektlarni, ularning xususiyatlarini, miqdorini yoki tartibini bildirmaydi. Emotiv (lot. eshowege – “hayajonlantirish”) – soʻzlovchining histuyg‘ularini ifodalash funksiyasi. Emotiv funksiya tufayli so‘zlovchi leksik birliklar yordamida kimga yoki nima haqida gapirayotganiga munosabat bildira oladi. Koʻp jihatdan, hissiy funksiya an’anaviy ravishda tushunilgan interensiyalarga xos boʻlib, ular ma’lumki, hech narsani nomlamaydi, faqat ba’zi his-tuyg‘ularni ifodalaydi. Kesimlardan tashqari, emotsional funksiya hissiy ekspressiv rang berish bilan ajralib turadigan har qanday leksik birliklarga xosdir, masalan, bema’nilik (oʻynoqi), bema’nilik (norozi), yolgʻon (nafrat), dahshatli (juda charchagan), (kuchlanish) va boshq.</p><p>&nbsp;</p><p>Belgi funksiyasi leksik birlikni belgi, tilni esa belgilar tizimi sifatida ko‘rib chiqish imkoniyatini nazarda tutadi. Bunday koʻrib chiqish zarurati turli xil til modellarini yaratish bilan bogʻliq holda yoki til va uning birliklari fikrlar, niyatlar, his-tuyg‘ular va boshqalarni oʻz ichiga olgan kengroq konseptual kontekstda tahlil qilingan hollarda paydo boʻladi (musiqa, rasm, yoʻl belgilari va boshq.). Leksik birlikni belgi sifatida ko‘rib chiqish imkoniyati faqat shartli va soʻzning tabiatiga bevosita aloqasi yoʻq. “Imo-ishora” tushunchasi bilan “so‘z” tushunchasi o‘rtasida ma’lum bir bog‘liqlik borligi haqidagi fikr juda qadimiy fikrdir. Buni tilda “soʻz” tushunchasi bilan bevosita bogʻliq boʻlgan belgi soʻzidan kelib chiqqan maʼno, ishora, belgilovchi, maʼno kabi lugʻaviy birliklarning azaldan mavjud boʻlganligi dalolat beradi. “Belgi” tushunchasining oʻzi hali ham fanda boshqacha talqin qilinadi. Ba’zilar ushbu konsepsiyaga faqat sun’iy axborot tizimlarining belgilarini, masalan, yoʻl belgilari, harbiy belgilar, Morze alifbosi va boshqalarni oʻz ichiga oladi. Boshqalar esa unda ogʻzaki belgilar deb ataladigan va sun’iy axborot tizimlarining belgilarini va simptom belgilarini birlashtiradi, ya’ni biror narsaga ishora qiluvchi turli belgilar (masalan, tutun – olov belgisi). Nihoyat, boshqalar sun’iy axborot tizimlarining faqat ogʻzaki belgilarini belgi sifatida tan oladilar. Tilning belgilar nazariyasining birinchi izchil va aniq taqdimoti F. de Sossyurga tegishli boʻlib, u “lingvistik belgi &lt;...&gt; tushuncha va akustik tasvirni bogʻlaydi, deb hisoblaydi. Bunda ikkinchisi moddiy tovush &lt;...&gt; emas, balki tovushning ruhiy izi, u haqida sezgilarimiz orqali qabul qiladigan fikrdir” [de Sossyur, 2000]. F. de Sossyurning belgi sof aqliy mohiyat sifatidagi tezisi bir necha bor tanqid qilingan. Fanda til belgisi haqidagi yuqoridagi tushuncha bilan bir qatorda yana ikkitasi ancha keng tarqalgan.</p><p>&nbsp;</p><p>Birinchisiga koʻra, lisoniy (ogʻzaki) belgi ikki tomonlama (moddiy-ideal) birlik boʻlib, unda belgilovchi moddiy shakl va uning akustik obrazi, belgilovchi esa tegishli tushuncha bilan ifodalanadi.</p><p>&nbsp;</p><p>Ikkinchi talqin lingvistik belgini faqat moddiy qobiqqa tushiradi.</p><p>&nbsp;</p><p>Bundan tashqari, erkin foydalanishda “belgi”, “lingvistik belgi”, “ogʻzaki belgi” va shunga oʻxshash atamalar yuqorida qayd etilgan noaniqlikni oldindan bartaraf qilmasdan, odatda “soʻz” leksik birligining sinonimi sifatida ishlatiladi. “Belgi” atamasi va uning hosilalarini talqin qilishdagi bunday noaniqlik ularni lingvistik tavsiflarda qoʻllash maqsadga muvofiqligi haqida ma’lum shubhalarni keltirib chiqaradi.</p><p>&nbsp;</p><p>Leksik birliklarning sintezlovchi vazifasi ularning fonetik, morfologik, semantik, sintaktik va stilistik xususiyatlarning manbai va tashuvchisi bo‘lib, ular birgalikda til tizimining tegishli bo‘g‘inlari mazmunini tashkil etishiga asoslanadi. Tushunchalarning o‘zi, masalan, fonema, morfema, hol, ma’no, semema va boshqalar leksik birliklarni tahlil qilishda va ulardan foydalanishni kuzatish natijasida va haqiqatda paydo boʻlishi mumkin edi. Leksik birliklarga xos bo‘lgan sintez funksiyasi ularni turli amaliy maqsadlarda qo‘llash imkonini beradi. Masalan, ma’lum darajadagi morfologik minimumni yaratmoqchi boʻlsak, buni quyidagicha amalga oshirish mumkin: a) ushbu darajaga mos keladigan leksik minimumni olish; b) har bir leksik birlikka tayinlash (nufuzli lugʻatlar va grammatikalar asosida) bu minimal uning barcha grammatik belgilari; d) bu xususiyatlarni umumlashtirish, toʻgʻri tartibga solish va ularni tizimlashtirilgan shaklda taqdim etish. Stilistik funksiyasi, bir tomondan, nutqning ma’lum sohalariga tayinlangan leksik birliklar, ikkinchidan, nutqning har qanday sohasida erkin qoʻllaniladigan leksik birliklar mavjudligiga asoslanadi. Birinchisi stilistik jihatdan bogʻliq (uslubiy jihatdan belgilangan, stilistik jihatdan belgilangan), ikkinchisi esa stilistik jihatdan neytral deb ataladi. Masalan, so‘z – so‘zi uslubiy jihatdan betaraf bo‘lib, uning shafoat sinonimi stilistik jihatdan bog‘langan (u rasmiy ish nutqiga berilgan), sarf so‘zi stilistik jihatdan neytral, isrof so‘zi stilistik jihatdan bog‘langan (so‘zlashuv nutqiga berilgan) vaboshq.. Stilistik jihatdan qaramaqarshi boʻlgan bunday leksik birliklarning mavjudligi so‘zlovchiga nutq registrini turli xil lingvistik boʻlmagan omillarga (vaziyatning tabiati, niyat mazmuni va boshqalar) qarab oʻzgartirishga imkon beradi.</p><p>&nbsp;</p><p>Metalingvistik funksiya leksik birliklarga boshqa leksik birliklarni tushuntirish imkonini beradigan funksiyadir. Turli leksik birliklar metalingvistik funksiyada foydalanish uchun turli xil qobiliyatlarga ega. Koʻp jihatdan metalingvistik funksiya leksik birliklarga xosdir, ular katta konseptual sinflar yoki tematik guruhlarning nomlari, masalan, obyekt, xususiyat, harakat, xona, mexanizm, mashina, qism va boshq. Bu va shunga oʻxshash soʻzlar koʻpincha izohli lugʻatlardagi ta’riflarda uchraydi. Ideografik (shu jumladan, tematik) lugʻatlarda bunday leksik birliklar odatda ma’lum bir umumiy xususiyat bilan birlashtirilgan soʻz turkumlarini boshqaradi. Metalingvistik funksiya umumlashtiruvchi – kognitiv (ma’noli, tasniflovchi) bilan chambarchas bogʻliq: soʻzning metalingvistik qoʻllanilishida aynan ma’nosi aktuallashtiriladi. Leksik birliklarning notoʻgʻri funksiyalari orasida asosiysi kommunikativdir.</p><p>&nbsp;</p><p>Leksik birliklarning kommunikativ vazifasi ularning aloqa, aloqa va taʼsir vositasi boʻlib xizmat qilish maqsadidir. Bu funksiya leksik birliklar uchun notoʻgʻri, chunki uning asosiy tashuvchisi gapdir. Leksik birlik nutqning yakuniy tarkibiy qismidir. Leksik birliklarning kommunikativ xususiyatlari, birinchi navbatda, ularning asosiy maqsadi bilan belgilanadi: atrofdagi olamning obyektlari va belgilarini nomlash, ular soʻzlovchilar, birinchidan, oʻzlarining axborot holatini boshqalarga yetkazishlari uchun moʻjallangan bo‘lsa, ikkinchidan, boshqalarning nutqi orqali taqdim etilganlarni idrok etishi uchun mo‘ljallangan. Agar til nuqtayi nazaridan (“til-nutq” dixotomiyasi) leksik birliklar, birinchi navbatda, nominativ birliklar boʻlsa, nutq nuqtayi nazaridan ular kommunikativ birliklar va kommunikativga ma’lumot aniqligini beradiganlardir. Kommunikativ funksiyaga muvofiq, muayyan nutqiy asarlarda leksik birliklar oʻzlarining nominativ ma’nosining faqat ma’lum bir kommunikativ vaziyatga mos keladigan qismini amalga oshiradilar. Masalan, choynakni kitobga qo‘yish iborasida kitob so‘zining nominativ ma’nosining eng umumiy qismi, ya’ni “tekis sirtga ega bo‘lgan narsa” aktuallashtirilsa, nominativ ma’noning barcha elementlari aktuallashtirilmaydi.</p><p>&nbsp;</p><p>“So‘z ma’lumot beradi, so‘z ma’lumot berishga xizmat qiladi, so‘z so‘zlovchining fikr va his-tuyg‘ularini bildiradi” va boshqacha aytganda, metafora bunday gaplarda yashiringanligini va uni tom ma’noda qabul qilib bo‘lmasligini aniq tushunishimiz kerak. Soʻzlar soʻzlovchi va tinglovchi oʻrtasida tumshugʻida oʻy bilan uchib yuradigan qushlar ham emas, ma’lumot tashuvchi samolyotlar ham emas. Soʻzning muloqotdagi roli (u bu rolni, birinchi navbatda, oʻzining moddiy qobigʻi yordamida bajaradi) tinglovchi (oʻquvchi) ongida nutqni joʻnatuvchi xohlagan bir yoki taxminan ma’lumot holatini uygʻotishdir. A.A. Potebnya shunday deb yozgan: “Siz oʻz fikringizni soʻz bilan boshqasiga yetkaza olmaysiz, lekin siz faqat unda oʻzingizni uygʻotishingiz mumkin” [Potebnya, 1926]. Leksik birliklarning estetik (vizual, poetik) vazifasi ularning badiiy ifoda vositasi sifatida harakat qilish maqsadidir. Estetik funksiya leksik birliklar uchun notoʻgʻri, chunki matn uning asosiy tashuvchisi sifatida ishlaydi. Shu bilan birga, matnning badiiy ekspressivligini yaratishda leksik birliklar boshqa barcha birliklardan koʻra koʻproq asosiy rol oʻynaydi. Estetik funksiya, birinchidan, jonli tasvir-timsollarni uygʻotuvchi oʻziga xos ma’noli lugʻaviy birliklarga, masalan, koʻz, ogʻiz, peshona va hokazolarga, ikkinchidan, yorqin ichki shaklga ega boʻlgan lugʻaviy birliklarga, masalan, kelishish, ibodat qilish uchun xarakterlidir, uchinchidan, har qanday leksik birliklar gʻayrioddiy kontekstda mohirlik bilan qoʻllangan. Leksik birliklarning estetik vazifasi yaxshi yozuvchilar tomonidan yaratilgan nutqiy asarlarda, umuman olganda, til tuyg‘usi o‘tkir bo‘lgan odamlar tomonidan namoyon bo‘ladi. Ularning ikkalasi ham oʻrtacha ona tilida soʻzlashuvchilardan farq qiladi, birinchi navbatda, ular soʻzni nafaqat uning qayerdadir roʻyobga chiqqan xususiyatlari, balki hali amalga oshirilmagan imkoniyatlari bilan ham idrok etadilar va his qiladilar. Leksik birliklarda estetik funksiyaning mavjudligi ma’ruzachilarga nafaqat voqea ma’lumotlarini bir-biriga yetkazish imkoniyatini beradi, balki intellektga ta’sir qiladi, shuningdek, voqealarni ham tasvirlaydi, shu orqali ruh va tasavvurga ta’sir qiladi, ya’ni nafaqat bilimni shakllantirish, balki tajribani uygʻotishda ham o‘z ta’sirini o‘tkazadi.</p><p>&nbsp;</p><p>Konstruktiv funksiya soʻzlarning, bir tomondan, iboralar va gaplar qurilishida ishtirok etishi, ikkinchidan esa, tahlili quyi darajadagi birliklarni, xususan, morfemalarni aniqlash imkonini beradigan mavjudotlar ekanligiga asoslanadi. Bundan tashqari, soʻzlar orasida konstruktiv vazifasi asosiy boʻlgan leksik birliklarning alohida guruhi aniq ajralib turadi. Gap, ma’lumki, muhim leksik birliklarni, jumlalarni yoki jumla qismlarini bogʻlash uchun ishlatiladigan predloglar va bogʻlovchilar kabi xizmat qiluvchi soʻzlar haqida ketmoqda. Konstruktiv funksiyaning birlamchi tashuvchisi morfemadir.</p><p>&nbsp;</p><p>Iqtisodiy soha maxsus semiotik tarkibiy qism – maxsus maqsadlar uchun til ishlatiladigan maxsus sohalarni anglatadi. Z.I. Guriyeva ishbilarmonlik tilini oʻrganib chiqib, barcha tillarning maxsus maqsadlar uchun maksimal umumiy xususiyati ularning lugʻatida odam maxsus sohalarda shugʻullanadigan obyektlarning nomlari (nominativ birliklari) mavjudligi ekanligini ta’kidlaydi [Gur’yeva, 2003]. Boshqacha qilib aytganda, maxsus maqsadlar uchun tillarning nominativ birliklari maxsus tushunchalarni bildiradi. Muayyan matnlarning mavjudligi, shuningdek, ma’lum bir tilni maxsus maqsadlar uchun ajratishning ajralmas shartidir. Iqtisodiyot dasturiy ta’minotining asosiy tushunchalari – bu turli darajadagi koʻplab til birliklari tomonidan iqtisodiy nutqda ogʻzaki bayon qilingan tadbirkorlik, pul, moliya, kredit, biznes, foyda haqidagi tushunchalar.</p><p>&nbsp;</p><p>Majoziy til biznes nutqiga kirib, iqtisodiy jurnalistika, yangiliklar, intervyular va yetakchi iqtisodiy ekspertlarning tahliliy muhokamalari, teledasturlar va iqtisodiyot boʻyicha darsliklar orqali [Kazakova, 2012] oʻz yoʻlini ochib beradi. Majoziy tildan ochiq foydalanish har doim iqtisodiy nutq uchun xarakterli boʻlib kelgan. Biroq iqtisodiy nutqda iqtisodiy jurnalistika qoidalarni buzadigan zamonaviy faoliyat yoʻliga kirgandan shu davrgacha ekspressiv til ishlatilmadi [Handford &amp; Koester, 2010; Gleicher, 2011]. Bizning fikrimizcha, professional iqtisodiy aloqaning turli sohalariga idiomalar va metaforalarning kirib kelishi ingliz biznesi nutqi sohasidagi hozirgi frazalar natijasidir [Kunin, 2005]. Metafora asosida shakllangan iboralar nafaqat hozirgi iqtisodiy voqelikni tasvirlash uchun [O’Halloran, 1999], balki kasbiy sohada oʻzini namoyon qilish uchun ham qoʻllaniladi [Erll &amp; Rigney, 2006].</p><p>&nbsp;</p><p>Metaforik qayta talqin qilish yoki metaforizatsiya natijasida paydo boʻladigan yangi mavhum tushunchalar sonini hisobga olmaganda, frazeologik lugʻatni rivojlantirishning asosiy vositasidir [Hadian &amp; Arefi, 2016]. Ushbu haqiqatni hisobga olgan holda, ingliz iqtisodiy nutqida ishlatiladigan frazeologik birliklarni tahlil qilish nafaqat ushbu leksemalarni aniqlashga, balki ingliz mentalitetining xususiyatlarini, ingliz ijtimoiy-iqtisodiy va ijtimoiy-siyosiy munosabatlarining, shuningdek, ingliz turmush tarzining xususiyatlarini ham aniqlashga imkon beradi [Skandera, 2007]. Tadqiqotchilar nuqtayi nazaridan, iqtisodiy nutq juda keng tarqalgan hodisa [Sommer, 2004]. Bundan tashqari, iqtisodiy nutqning funksional holati, tarkibiy qismlari va lingvistik chegaralari yetarli darajada oʻrganilmagan. Iqtisodiy nutq iqtisodiy sohadagi aloqa natijasida turli omillar ta’sirida paydo boʻldi: ekstralingvistik, pragmatik, ijtimoiy-madaniy va boshq. Boshqa nutq turlarida boʻlgani kabi, iqtisodiy nutq nafaqat situatsion kontekst va ishtirokchilarning kommunikativ va pragmatik munosabatlari, balki ekstralingvistik (ijtimoiy-psixologik va madaniy-tarixiy) omillar ham ta’sir qiladi [Shchekina, 2001].</p><p>&nbsp;</p><p>Frazeologik sohada iqtisodiy nutq bir qator oʻziga xos xususiyatlarga ega, jumladan, mantiqiy taqdimot, aniqlik, argumentativlik va informativlik [Anderson, 2006]. Ushbu belgilar har qanday tilning terminologik tizimiga xosdir. Shuningdek, frazeologik birliklar ingliz iqtisodiy nutqida faol ishlatiladi, chunki ular moslashuvchan [Bondi, 2010].</p><p>&nbsp;</p><p>Umuman olganda, inglizcha frazeologik ma’nolar tizimi asrlar davomida insoniyat jamiyati bilan birgalikda shakllangan va shu kungacha shakllanib kelayotgan murakkab tarmoqlangan quyi tizimdir [Apalat, 1999]. Shunday qilib, ushbu tizimda iqtisodiy matnlarda topilishi mumkin boʻlgan va muhim etnomadaniy ma’lumotlar manbai sifatida ishlaydigan koʻplab birliklar mavjud [Adolphs &amp; Carter, 2007]. Shuning uchun frazeologik ma’nolarni turli xil xususiyatlar, birlashmalar, munosabatlarga asoslangan millatning jamoaviy rasmini bildiruvchi noyob, madaniy jihatdan bogʻliq lingvistik birliklar sifatida tahlil qilish maqsadga muvofiqdir [Brody, 2003]. Darhaqiqat, har qanday tilda stereotipik ma’nolarni bildiruvchi tushunchalar mavjud [Dirven &amp; Verspoor, 2004]. Ushbu tushunchalar frazeologik birliklar tizimida paydo boʻlishi mumkin [Taylor, 2002]. Ushbu bosqichda frazeologik birliklar tilshunoslik va madaniyatshunoslikning haqiqiy maqsadiga aylanishi mumkin. Boshqa tomondan, frazeologik birliklarning stereotipik tabiati qoʻshimcha e’tiborga loyiq xususiyatdir. Xuddi shu narsa frazeologik ma’nolarning aksiologik tomoniga ham tegishli [Sinelnikov et al., 2015].</p><p>&nbsp;</p><p>Ishbilarmonlik muhitida keng qoʻllanilishiga qaramay, terminologik ma’noga ega bo‘lgan terminologik iboralar yoki frazeologik birliklar uzoq vaqt davomida maxsus tadqiqotlar doirasidan tashqarida boʻlgan. Ular milliy kontekstda lingvistik ifoda vositasi sifatida qaralmagan. Biroq hozirda bu sohada sezilarli yutuqlarga erishildi. Fokusning bunday oʻzgarishi tahlil qilish uchun turli tillarning frazeologik sohasini kengaytirishga imkon beradi [Sasina, 2007]. Ingliz iqtisodiy nutqida koʻplab frazeologik birliklar qoʻllaniladi [Nerubenko, 2013]. Shunga qaramay, ularning semantik va tarkibiy xususiyatlari, tasnifi va foydalanish maqsadi yetarli darajada oʻrganilmagan. Shunday qilib, yangi vazifa iqtisodiy ingliz frazeologik birliklarini oʻrganishdir [Safina, 2002].&nbsp;<br><br><br><br><br><br><br>&nbsp;</p>	1	1753979529
11	119	TADQIQOT METODLARI	<p>Ushbu tadqiqotning maqsadi ingliz tilidagi iqtisodiy matnlarda mavjud bo‘lgan frazeologik birliklarning tuzilishi va ma’nosini tahlil qilishdir. Tadqiqot soha terminologik iboralarning leksik-semantik, kognitiv, pragmatik va madaniy-lingvistik xususiyatlarini tahlil qilishni oʻz ichiga oladi. Tadqiqot vazifalari ingliz frazeologik birliklarini aniqlagan va shakllantirgan ichki va tashqi omillarni tahlil qilish; iqtisodiy nutqda frazeologik birliklar oʻrtasidagi leksik-semantik munosabatlarga asoslanib, dominant leksemalarni aniqlash; iqtisodiy nutqdagi frazeologik birliklarning fonini tavsiflash; frazeologik birliklarni tahlil qilish va ingliz tilining iqtisodiy sohasidagi etnik, psixologik, ijtimoiy-siyosiy va madaniy konstantalarni aniqlashdan iborat.</p><p>&nbsp;</p><p>Mazkur tadqiqot ingliz iqtisodiy tilida ishlatiladigan frazeologik birliklar boʻyicha oʻtkazildi. Tadqiqot obyektlari (frazeologik birliklar) soʻnggi besh yil ichida ingliz tilidagi iqtisodiy matnlardan (hujjatlar, onlayn materiallar, “Economist” kabi jurnal va boshqa gazetalar)dan olingan. Ingliz frazeologik birliklarining tavsifi qoʻshimcha ravishda leksikografik manbalar, jumladan, frazeologik, terminologik va etimologik lugʻatlar, shuningdek, oʻziga xos ingliz lugʻatiga ega lugʻatlar ma’lumotlari bilan toʻldirildi. Oxirgi toifaga inglizcha-ruscha iqtisodiy lugʻat, “Longman” lugʻati va “Slovar-vocab.com” kiradi.</p><p>&nbsp;</p><p>Shu bilan birga, tadqiqot uchun tilshunoslikka oid maqolalar, media materiallar, biznes va iqtisodiyotga oid professional adabiyotlardan ellita frazeologik atamalar ajratib olindi. Ular toʻrtta frazeologik va semantik sohalarga bo‘lindi: “pul munosabatlari”, “sotib olish va sotish”, “biznes va menejment” va “iqtisodiy va ishlab chiqarish munosabatlari”.&nbsp;<br>Tadqiqotda lingvistik tahlilning quyidagi usullari qoʻllanilgan:</p><ul><li>komponentlarni tahlil qilish usuli – semantemani tavsiflaydi, etnik guruhni bildiruvchi frazeologik birlikning ma’nosini tushunishga yordam beradi va soʻzlarning frazeologik makroguruhlarining leksik va semantik tuzilishini oʻrganadi;</li><li>lingvokulturologik va etnolingvistik tahlil usuli – terminologik birliklarning frazeologik tarkibining madaniy va aksiologik tomonini aniqlashga imkon beradi;</li><li>tarkibiy va semantik modellashtirish usuli – ingliz tilida frazeologik birliklarning shakllanishining qonuniyatlari va oʻziga xos mexanizmlarini belgilaydi;</li><li>funksional tahlil usuli – iqtisodiy aloqa sharoitida sobit terminologik birliklarning tegishli ma’nosini aniqlash uchun ishlatiladi;</li><li>uzluksiz namuna olish usuli – iqtisodiy nutqda mavjud boʻlgan faktik frazeologik materialni olishga qaratilgan;</li><li>talqin usuli – frazeologik birliklarning ma’nosini va ularning nutq kontekstida bir-biri bilan qanday bogʻliqligini tushunish uchun ishlatiladi.&nbsp;<br>&nbsp;</li></ul><p>&nbsp;</p>	2	1753979584
12	119	NATIJALAR VA MUNOZARA	<p>Iqtisodiy matnda frazeologiyadan foydalanish tashqi va ichki omillarga bogʻliq. Bir tomondan, tilning rivojlanishi yangi paydo bo‘lishiga olib keldi. Iqtisodiy sohadagi frazeologik birikmalar, masalan: to play economics – iqtisodiy faoliyatda insofsiz usullarga murojaat qilish; insofsiz iqtisodiy oʻyin oʻtkazish.</p><p>&nbsp;</p><p>Boshqa tomondan, iqtisodiyot tarixdan, madaniy an’analardan kelib chiqqan frazeologik birliklardan faol foydalanadi.&nbsp;<br>Ba’zi frazeologik birliklar to‘liq o‘rnatilmagan, shuning uchun ular kalit soʻzlar bilan farq qilishi mumkin. Soʻzlarning bunday guruhlanishi semantik yaxlitlikni yoʻqotmasdan bitta komponentni oʻzgartirishga imkon beradi, masalan: to enter into a contract – shartnoma tuzish. Frazeologik birliklar barqaror tuzilishga va ma’noga ega bo‘lgan tayyor lingvistik birliklar sifatida ishlatiladi, masalan: to catch the wind – shamolni ushlash toʻlqinni ushlash, ma’lum bir vaqtda muvaffaqiyat qozonish demakdir.</p><p>&nbsp;</p><p>Iqtisodiy nutqda ishlatiladigan frazeologik birliklar mavhum boʻlmagan narsalar bilan bogʻliq va odamlarning kundalik hayotiga yaqin. Bu, oʻz navbatida, terminologik sohada frazeologik birliklar orasida juda koʻp sonli majoziy nominatsiyalar mavjudligini tushuntiradi. Bu frazeologik birliklarga iqtisodiy voqelikni bildiruvchi metaforik ma’nolar kiradi, masalan, cats and dogs – spekulyativ aksiyalar; lame duck – moliyaviy qiyinchiliklarni boshdan kechirayotgan kompaniya yoki tadbirkor.</p><p>&nbsp;</p><p>Iqtisodiy matnlarda pulni iqtisodiy birlik sifatida belgilaydigan frazeologik birliklar mavjud: purse full of money, the root of all evil (money), money burns a hole in my pocket, nor for love or money, to be stony-broke – pul yoʻq, fry the fat out of (fry out fat) – bosim yoki tovlamachilik orqali pul olish.</p><p>&nbsp;</p><p>Frazeologik birikmalardagi money – pul atamasi noqonuniy iqtisodiy harakatlar sharoitida tez-tez ishlatiladi, masalan: trade-based money laundering – chegaralar orqali pul olish uchun tijoratni suiiste’mol qilish; ba’zan maqsad soliqlar, yig‘imlar yoki kapital nazoratidan qochishdir; koʻpincha bank tizimiga nopok pul kiritishdir; money laundering – jinoiy faoliyat natijasida olingan pullarni yuvish jarayonini anglatadi.</p><p>&nbsp;</p><ul><li>Jinoiy faoliyat natijasida olingan pulni bildiruvchi frazeologik birliklar quyidagilar:&nbsp;<br>black money:<br>But big rich countries still like to portray themselves as leaders in the fight against black money [“Rich smell”, 2013].<br><i>Katta boy davlatlar hali ham oʻzlarini qora pullarga qarshi kurashda yetakchi sifatida koʻrsatishni yaxshi koʻradilar.</i></li><li>dodgy money:<br>Big rich countries often accuse small offshore financial centres, such as Jersey and the Cayman Islands, of acting as willing conduits for dodgy money [“Rich smell”, 2013].<br><i>Katta boy mamlakatlar koʻpincha Jersi va Kayman orollari kabi kichik offshor moliyaviy markazlarni shubhali pullarning tayyor oʻtkazgichlari sifatida ayblashadi.</i></li></ul><p>&nbsp;</p><p>Quyida pulga ijobiy nur sochadigan frazeologik birliklar keltirilgan:</p><ul><li>white money:<br>This was to be part of a national “white-money strategy”, still in the making, to shed Switzerland’s image as a tax haven once and for all. Critics suspect it is a smokescreen [“Rise of the midshores”, 2013].<br>Bu Shveytsariyaning soliq panohi sifatidagi obroʻsini bir marta va butunlay yoʻq qilish uchun hali ishlab chiqilayotgan milliy “oq pul” strategiyasining bir qismi boʻlishi kerak edi. Tanqidchilar bu tutun ekrani deb gumon qilmoqdalar.&nbsp;</li><li>honest money&nbsp;<br>What the opponents of the primacy of the electronic money do not realize is that the economic yardstick of electronic money making is the key to the eliminated inflation and an honest fund [Kimball, 2019].<br>Elektron pullarning ustuvorligi muxoliflari tushunmaydigan narsa shundaki, elektron pullarni yaratishning iqtisodiy mezoni inflyatsiyani yoʻq qilish va halol moliyalashtirishning kalitidir (Maylz Kimball elektron valyuta haqiqiy narx barqarorligini qanday ta’minlashi haqida).&nbsp;</li></ul><p>Pul birliklarini bildiruvchi koʻplab yangi frazeologik birliklar mavjud, masalan web money, Internet money, electronic money – yaqinda iqtisodiy nutqda paydo boʻlgan, shuningdek:&nbsp;</p><ul><li>electronic money&nbsp;<br>Electronic money would fix that, however, by making it impossible to move money out of a form subject to negative rates – except by spending it or investing it in a high-yield asset, which is precisely the stimulative outcome the central bank is hoping to generate [Agarwal &amp; Kimball, 2022].<br>Buni salbiy stavkalarga ega boʻlgan shakldan pul oʻtkazishni imkonsiz qilish orqali tuzatadi – uni sarflash yoki yuqori mahsuldor aktivga sarmoya kiritish bundan mustasno, bu aynan Markaziy bank umid qiladigan ragʻbatlantiruvchi natijadir. Bu elektron dollarni qisqartiring.&nbsp;</li></ul><p>Tegishli nomlarga ega frazeologik birliklar iqtisodiy nutqda ham uchraydi, shu jumladan:</p><p>&nbsp;</p><p>Joy nomlari: the Trojan horse (Troyan oti), to carry coals to Newcastle (Nyukaslga koʻmir olib borish), between Scylla and Charybdis (Ssilla va Chariybdis oʻrtasida). Masalan: Economists have been carrying coal to Newcastle since Adam</p><p>&nbsp;</p><p>Smith provided English merchants with a rationalization of what they had always wanted to do – treat their fellow human beings as beasts of burden. Economists continue to perform the same function [Kozy, 1974].</p><p>&nbsp;</p><p>Iqtisodchilar Adam Smitning davridan beri Nyukaslga koʻmir tashishmoqda. Smit ingliz savdogarlariga har doim qilishni xohlagan narsalarini ratsionalizasiya qildi – oʻz hamkasblariga yuk tashuvchi hayvon kabi munosabatda boʻldi. Iqtisodchilar xuddi shu funksiyani bajarishda davom etmoqdalar.</p><p>&nbsp;</p><p>“To carry coals to Newcastle” (Nyukaslga koʻmir olib borish) iborasi – foydasiz va behuda ishlarni bajarishni anglatadi.</p><p>&nbsp;</p><p>“Trojan horse” (Troyan oti)ning strategiyasi – jasur harakat boʻlishi mumkin, ammo ikkala tomon ham pozitsion urushga yopishib olishlari va qonun siyosati qanday oʻynashini kutishlari ehtimoli koʻproq.</p><p>&nbsp;</p><p>Troyan otining ma’nosi – ularni qabul qilganlarga oʻlim keltiradigan noinsof, qalbaki sovgʻalarni anglatadi.</p><p>&nbsp;</p><p>Antroponimlar: Gordian knot (Gordian tuguni), Peeping Tom (Qiziquvchan Tom), Doubting Thomas (Shubhali Tomas). Masalan: – The solution of the Gordian knot of the European Monetary.&nbsp;<br>System is very similar, except there is a little extra secret. It would not work unless the sword was made of gold.</p><p>&nbsp;</p><p>Yevropa valyuta tizimi Gordian tugunining yechimi sir-sanoatsiz juda oʻxshash. Agar qilich oltindan yasalmagan boʻlsa, u ishlamas edi.</p><p>&nbsp;</p><p>Frazeologiya Frigiya qiroli Gordius nomidan kelib chiqqan boʻlib, muammo, juda qiyin savol va “muammoni tez va qat’iy hal qilish qobiliyatini anglatadi”.</p><p>&nbsp;</p><p>Iqtisodiy frazeologiyaning maqsadiga mavhum tushunchalar ham ta’sir qiladi. Misol uchun, frazeologiya “goldilocks economy”:</p><p>&nbsp;</p><p>The blame lies with central bankers, who in the late 1990s put too much faith in the so-called goldilocks economy: not too hot, not too cold [“You beasts”, 2002].</p><p>&nbsp;</p><p>Ayb 1990-yillarning oxirida goldilocks deb ataladigan iqtisodiyotga juda koʻp ishongan Markaziy banklarda yotadi: juda issiq ham emas, juda sovuq ham emas.</p><p>&nbsp;</p><p>Ushbu frazeologiya “oltin oʻrtacha iqtisodiyot”, barqaror rivojlangan mamlakatlar iqtisodiyoti va inflyatsiyaning tabiiy darajasi degan ma’noni anglatadi. Soʻzma-soʻz, “Goldilocks va uch ayiqlar ertakka asoslangan, unda asosiy belgi kichik ayiq boʻtqani tatib koʻradi va u “juda issiq ham emas va juda sovuq ham emas” boʻlib chiqadi.</p><p>&nbsp;</p><p>Ushbu ibora, aurea mediocritas (aurea mediosritas), birinchi marta lotin tilida Rim shoiri va faylasufi Goratsiy tomonidan ishlatilgan.</p><p>&nbsp;</p><p>Iqtisodiyotda ba’zi frazeologik birliklar mifologiya, tarixiy voqealar, adabiy asarlar va Injil hikoyalaridan olingan. Iqtisodiy nutqning ayrim frazeologik birliklari ma’nosining kelib chiqishi mifologiyadan kelib chiqadi: Midas touch Achilles heel, Grim Reaper, Pandora’s box. Masalan:</p><p>&nbsp;</p><p>But some EU governments have similar instincts. Most retain “golden shares ” in big privatized companies. It is a Midas touch [“The Midas touch”, 2000].</p><p>&nbsp;</p><p>Ammo ba’zi Yevropa Ittifoqi mamlakatlari hukumatlari oʻxshash instinktlarga ega. Ularning aksariyati yirik xususiylashtirilgan kompaniyalarda “eski aksiyalarni” saqlaydi. Bu Midas teginishini anglatadi.</p><p>&nbsp;</p><p>“Midas touch” frazeologiyasi qirol haqidagi yunon afsonalaridan kelib chiqqan boʻlib, u tekkan hamma narsa oltinga aylanishini xohlagan. Zamonaviy talqinda ibora biznesda juda muvaffaqiyatli odamni anglatadi:</p><p>&nbsp;</p><p>President Reagan won plaudits for appointing the first femal Supreme Court ju stice. Mr Bush will need the wisdom of Solomon to please even half the country in no minating her successor [“A hard seat to fill”, 2005].</p><p>&nbsp;</p><p>Prezident Reygan oliy sudning birinchi ayolini adolatli tayinlagani uchun olqishlandi. Janob Bush oʻz vorisini tayinlashda mamlakatning kamida yarmini mamnun qilish uchun Sulaymonning donoligiga muhtoj boʻladi.</p><p>&nbsp;</p><p>“Wisdom of Solomon” (Sulaymonning donoligi) iborasi donoligi va adolati bilan mashhur boʻlgan Shoh Solomon nomi bilan bogʻliq.</p><p>&nbsp;</p><p>Adabiy asarlar: Amerika orzusi, Don Kixot, Jeyms Bond va boshq., masalan:</p><p>&nbsp;</p><p>Americans have come to tolerate extreme inequality, more so than the people living in any of the other rich countries around the globe. And the American dream may be to blame [“Inequality and the American Dream”, 2006].&nbsp;<br>Amerikaliklar dunyoning boshqa boy mamlakatlarida yashovchi odamlarga qaraganda haddan tashqari tengsizlikka koʻproq chidashga odatlangan. Va, ehtimol, Amerika orzusi bunga aybdor.</p><p>&nbsp;</p><p>Bu AQSh fuqarolarining qadriyatlari toʻplamini, ularning “Amerika gʻoyasini” anglatadi.</p><p>&nbsp;</p><p>Zoonimlar (hayvonlar nomi)ga ega frazeologik birliklar ham iqtisodiy nutqda odatiy topilma hisoblanadi. Bunday lingvistik birliklar iqtisodiy agentlarning xattiharakatlari va hayvonlar bilan iqtisodiy munosabatlar bilan bogʻliq. Masalan, bulls and bears:</p><p>&nbsp;</p><p>Even though the bulls and bears are constantly at odds, they can both make money with the changing cycles in the market [“Even stockmarket bulls”, 2018].</p><p>&nbsp;</p><p>Buqalar va ayiqlar doimo qarama-qarshilikda boʻlishiga qaramay, ikkalasi ham bozorda oʻzgaruvchan sikllardan pul ishlashlari mumkin.</p><p>&nbsp;</p><p>Ushbu frazeologik birlikda ikkita hayvonning nomlari mavjud: bull (buqa) – shoxdorlar oilasiga mansub, xuddi fil va kit kabi yirik hayvon; bear (ayiq – qalin moʻynali, meva va hasharotlar bilan oziqlanadigan katta kuchli hayvon. Shunga asoslanib, zoonimlar bilan bogʻliq frazeologik birliklar quyidagicha ma’no beradi:</p><p>&nbsp;</p><p>bull market (buqa bozori) – stavkalarni (aksiyalarni) oshirish tendensiyasiga ega bozor:</p><p>&nbsp;</p><p>A bull market is when everything in the economy is great, people are finding jobs, gross domestic product is growing, and stocks are rising [“What is ‘Bull Market’”, n.d.].</p><p>&nbsp;</p><p>Buqa bozori – bu iqtisodiyotda katta ish olib borayotgan, unda odamlar ish topayotgan, yalpi ichki mahsulot o‘sib borayotgan va zaxiralar oʻsib borayotgan payt hisoblanadi.</p><p>&nbsp;</p><p>bear market (ayiq bozori) – stavkalarni pasaytirish tendensiyasiga ega bozor (aksiyalar):</p><p>&nbsp;</p><p>Bear markets make it tough for investors to pick profitable stocks. One solution to this is to make money when stocks are falling using a technique called short selling. Ayiq bozori investorlarga foydali aksiyalarni tanlashni qiyinlashtiradi.</p><p>&nbsp;</p><p>Ushbu muammoning yechimlaridan biri bu qisqa sotish deb nomlangan texnikadan foydalangan holda aksiyalar tushgan paytda pul ishlashdir.</p><p>&nbsp;</p><p>Ingliz frazeologik birliklarida “bull and bear” (buqa va ayiq) tasvirlari buqa va ayiqni kuchli hayvonlar sifatida qabul qilish bilan bogʻliq: “bear with strong legs” (“kuchli oyoqli ayiq”) ko‘rsatkichlarni pasaytiradi, “bull with horns” (“shoxli buqa”) esa koʻrsatkichlarni oshiradi. Iqtisodiy nutqda buqa va ayiq tasvirlari salbiy ma’nolarda, masalan, raqibni obroʻsizlantirishga urinish sifatida ham ishlatilishi mumkin:</p><p>&nbsp;</p><p>This is the worst bear market of all times is embarrassing to us. Your cheap headlines, such as “the bears show their teeth” or “grin and bear it” are insulting</p><p>&nbsp;</p><p>[“You beasts”, 2002].</p><p>&nbsp;</p><p>Bu barcha davrlar ichida eng yomon ayiq bozori va bu bizni hijolatga qoʻyadi. Sizning arzon-garov: “ayiqlar tishlarini koʻrsatayapti” yoki “jilmaying va bunga sabr qiling” kabi sarlavhalaringiz ayanchli.</p><p>&nbsp;</p><p>“The bears show their teeth” (Ayiqlar tishlarini koʻrsatayapti) iborasi “show teeth – to bare one’s teeth” (tishlarni koʻrsatish – bu jilmayish) iborasidan kelib chiqadi. “Grin and bear” (jilmayish va ayiq) frazeologiyasi kimgadir yoki biror narsaga jilmayish bilan haqiqiy munosabatni yashirishni anglatadi. Shu nuqtayi nazardan, frazeologik birliklar The Economist jurnalidagi maqolalarida kamsitish va obroʻsizlantirishda ishlatiladi.</p><p>&nbsp;</p><p>Yuqoridagi misol keltirilgan hayvonlardan tashqari frazeologik birliklar orasida quyidagi zoonimlarni topish mumkin: kalamush, mushuk, ajdaho, choʻchqa va boshqalar. Masalan, dead cat bounce:</p><p>&nbsp;</p><p>In other words, we might be seeing what economist Nouriel Roubini in the context of the US economy earlier called “dead cat bounce”. An enduring revival would have been backed by a turnaround in investment.</p><p>&nbsp;</p><p>Boshqa soʻz bilan aytganda, biz iqtisodchi Nuryel Rubinini, AQSh iqtisodiyoti doirasida, dead cat bounce (“oʻlik mushuk sakrayapti”) iborasini ilgari surganligini guvohi boʻlishimiz mumkin. Barqaror tiklanish investisiyalarning koʻpayishi bilan qoʻllab-quvvatlanadi.</p><p>&nbsp;</p><p>Frazeologiya “bouncing off a dead cat” (“oʻlik mushuk sakrayapti”) pasayish davridan keyin moliyaviy aktiv narxining keskin oshishi degan ma’noni anglatadi. Bu odatda yoʻqotishlarning kamayishi bilan bogʻliq; bu qisqa muddatda aksiyalarning pasayish tendensiyasining oʻzgarishini anglatmaydi. Bu ibora hatto oʻlik mushuk ham katta balandlikdan yiqilsa, sakrab tushadi degan fikrdan kelib chiqadi.</p><p>&nbsp;</p><p>to smell a rat – biror narsa notoʻgʻri ekanligini his qilish (sizga xiyonat qilgan yoki sizni aldagan kishi):</p><p>&nbsp;</p><p>On the face of it, this move seems sensible. But critics smell a rat. They point out that even the biggest democracies, including America, have not always felt a need to increase the numbers of representatives in line with the population [“What’s Malay”, 2014].</p><p>&nbsp;</p><p>Bir qarashda, bu qadam oqilona koʻrinadi. Ammo tanqidchilar nimadir notoʻgʻri ekanligini his qilishadi. Ularning ta’kidlashicha, hatto eng yirik demokratik davlatlar, shu jumladan, Amerika ham har doim ham aholi soniga qarab vakillar sonini koʻpaytirish zarurligini sezmagan.&nbsp;<br>&nbsp;<br>&nbsp;</p>	3	1753979754
13	119	XULOSA	<p>Har bir til frazeologik tomondan tadqiqot uchun boy boʻlgan lingvistik materialni taqdim etadi, chunki u nafaqat dunyoning ona qiyofasi va shaxsning uning qismlariga boʻlgan munosabati haqidagi bilimlarni aks ettiradi, balki milliy madaniyatning oltin standartlari va stereotiplarini yetkazish uchun dasturlashtirilgan hisoblanadi. Shunday ekan, frazeologik terminologiya “dunyoning aksiologik suratini” aks ettiradi. Uning etnik tajriba bilan aloqalarini oʻrganish va etnik dunyoda atrof-muhit, madaniyat, urfodatlar va milliy urf-odatlarning oʻziga xos aks etishi insonning qadimiy arxetipik tasvirlari tilda qanday kodlanganligini aniqlashga imkon beradi. Frazeologik leksik birliklari ikki turdagi ma’umotlarni uzatishga qodir: umuman insoniyat tomonidan olingan ma’lumotlar va ma’lum millatlar tomonidan olingan ma’lumotlar. Bizning fikrimizcha, oʻrganilayotgan terminologik frazeologik birliklarda qayd etilgan ma’lumotlar til va madaniyat ma’lumotlarini dunyoning yaxlit suratini tashkil etuvchi semiotik tarkibiy qismlar sifatida toʻplaydi.</p><p>&nbsp;</p><p>Ona tilida soʻzlashuvchilar frazeologik birliklarni uzoq oʻtmishda paydo boʻlgan va faqat ma’lum bir kontekstda ishlatilishi mumkin boʻlgan ma’nolar sifatida qabul qilishadi. Shunga qaramay, ular ijtimoiy hodisa boʻlib qolmoqda va ijtimoiy maqsadlarda foydalanilmoqda. Frazeologik birliklarning leksik-semantik tarkibi quyidagi sohalarda amalga oshiriladigan konseptual mikropollarni aks ettiradi: shaxs, makon va vaqt, hayvonlar, obyektlar va ularning holati, biologiya, tibbiyot, baholash ta’riflari va boshqalar. Iqtisodiy nutqdagi frazeologik terminologiya pul birliklarini, bozor va birja munosabatlari ishtirokchilarini, iqtisodiy munosabatlar obyektlari va subyektlarini, baholovchi iqtisodiy xususiyatlarni (masalan, muvaffaqiyat darajasi) va boshqalarni anglatadi.</p><p>&nbsp;</p><p>Iqtisodiy matnlarda frazeologik birliklarning ahamiyati mifologiya, Injil va diniy matnlar, tarix, etnik guruhning milliy-madaniy xususiyatlari, uning odatlari va urf-odatlari kabi turli manbalardan kelib chiqadi. Iqtisodiy matnlardagi frazeologik birliklarning asosiy maqsadi oʻquvchilar ongiga ta’sir qilishdir. Chunki, frazeologik birliklar hissiy va ifodali rangga ega. Iqtisodiy frazeologik birliklar quyidagi leksiksemantik mikropolni qamrab oladi: bank va moliya sohasi, sanoat va ishlab chiqarish sohasi, iqtisodiy siyosat va h.k.z. Tadqiqot natijalari shuni koʻrsatdiki, ushbu semantik mikro guruhlarni ajratish oʻzboshimchalik bilan amalga oshiriladi, chunki terminologik ma’noga ega boʻlgan bitta frazeologik birlik turli sohalarga tegishli boʻlishi mumkin.</p><p>&nbsp;</p><p>Iqtisodiy nutqda dominant “pul” soʻzi salbiy va ijobiy belgilar bilan ifodali konseptual ma’noni anglatadi. Salbiy ma’noga ega boʻlgan leksik-semantik maydon “qora pul”, “shubhali pul”, “qonli pul” va shu kabi frazeologik birikmalarni oʻz ichiga oladi. Ijobiy ma’no odatda “oq pul”, “halol pul” va shu kabi tuzilmalar bilan belgilanadi. Ingliz iqtisodiy frazeologizmlari orasida koʻpincha toponimlar, antroponimlar va zoonimlar ham uchraydi. Frazeologik birliklar ma’lum bir kontekstda shakllanadigan mavhum tushunchalarni anglatadi. Iqtisodiy frazeologik birliklarning asosiy manbalari mifologiya, tarixiy voqealar, personajlar va shaxslar, adabiy asarlar va din, shu jumladan, Injil mavzularidir. Frazeologik birliklarning tavsifi ingliz tili iqtisodiy sohasining psixologik, ijtimoiy-siyosiy va madaniy xususiyatlarini aniqlaydi&nbsp;<br>&nbsp;</p>	4	1753979776
\.


--
-- TOC entry 5162 (class 0 OID 24973)
-- Dependencies: 263
-- Data for Name: publication_refs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.publication_refs (id, publication_id, source_type, authors, organization_name, publication_year, publication_date, title, chapter_title, thesis_type, source_title, publisher_name, publication_place, volume, issue, page_start, page_end, edition, conference_country, conference_city, word_term, defense_place, university_name, doi, url, web_of_science_url, google_scholar_url, access_date, created_at) FROM stdin;
\.


--
-- TOC entry 5160 (class 0 OID 24967)
-- Dependencies: 261
-- Data for Name: publication_refs_backup; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.publication_refs_backup (id, publication_id, title, authors, doi, doi_link, wos_link, scopus_link, gscholar_link, created_at, resource, web_link) FROM stdin;
6	119	A hard seat to fill. (2005, July 7)							1753979902	The Economist	https://www.economist.com/united-states/2005/07/07/a-hard-seat-to-fill
8	119	Beyond the word: New challenges in analysing corpora of spoken English. 2	Adolphs, S., & Carter, R.	10.1080/13825570701452698	https://doi.org/10.1080/13825570701452698	https://doi.org/10.1080/13825570701452698	https://doi.org/10.1080/13825570701452698	https://doi.org/10.1080/13825570701452698	1753980122	European Journal of English Studies, 11(2), 133–146, 2007	
7	119	Tilshunoslik nazariyasiga kirish (2010)	Abduazizov, A. 						1753979930	Toshkent: “Sharq” nashriyotmatbaa aksiyadorlik kompaniyasi	
\.


--
-- TOC entry 5146 (class 0 OID 24785)
-- Dependencies: 247
-- Data for Name: publications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.publications (id, title, title_uz, title_ru, main_author_id, subauthor_ids, issue_id, abstract, abstract_uz, abstract_ru, doi, doi_link, keywords, additional, stat_views, stat_alt, stat_crossref, stat_wos, stat_scopus, date_sent, date_accept, date_publish, stage, comments, file_ids, is_paid, price, price_uz, price_ru, subscription_enable, created_at, keywords_uz, keywords_ru, current_views) FROM stdin;
119	Lexical Units and Their Use as Phraseological Units in Economic Discourse (on the Example of the Field of Entrepreneurship)	LEKSIK BIRLIKLAR VA ULARNING IQTISODIY NUTQDA FRAZEOLOGIK BIRLIK SIFATIDA QOʻLLANILISHI (TADBIRKORLIK SOHASI MISOLIDA)	ЛЕКСИЧЕСКИЕ ЕДИНИЦЫ И ИХ ИСПОЛЬЗОВАНИЕ КАК ФРАЗЕОЛОГИЧЕСКИХ ЕДИНИЦ В ЭКОНОМИЧЕСКОМ ДИСКУРСЕ (НА ПРИМЕРЕ СФЕРЫ ПРЕДПРИНИМАТЕЛЬСТВА)	8	{9}	13	This article examines the utilization of lexical\r\nunits as phraseological expressions within\r\neconomic discourse, with a particular focus on\r\nentrepreneurship. It investigates phraseological\r\nexpressions commonly encountered in texts\r\npertaining to entrepreneurial activities, analyzing\r\ntheir lexical-semantic structure, stylistic features,\r\nand communicative functions. Additionally, the\r\narticle elucidates the role of these phraseologisms\r\nin conveying economic concepts and articulating\r\nideas in a vivid and persuasive manner.\r\nThe research article aims to identify translation\r\nmethods based on the linguistic characteristics of\r\nlexical units associated with entrepreneurship in\r\nboth English and Uzbek. The study’s objectives\r\ninclude highlighting the extent to which lexical\r\nunits in the field of entrepreneurship have been\r\ntheoretically examined in linguistics; identifying\r\ntheir linguistic features from both diachronic\r\nand synchronic perspectives; and uncovering\r\nthe derivational aspects of terms in this field,\r\nincluding their formation through affixal,\r\nmorphemic-morphological, lexical-semantic,\r\nfunctional-semantic, and syntactic methods.\r\nThe research employs descriptive, comparativetypological (contrastive), diachronic and synchronic, componential analysis, semantic field\r\nanalysis, and linguo-statistical methods.\r\nThe scientific novelty of this article lies in\r\nsubstantiating the figurative use of entrepreneurial\r\nlexical units in spoken language, their role in\r\nindividuals’ lives, their use in the economy, and the\r\npresence of phraseological units in this domain.\r\nAccording to research findings, phraseological\r\nunits in economic discourse convey more\r\nemotional, expressive, and figurative meaning\r\nthan ordinary lexical items. They enrich economic\r\ntexts stylistically and facilitate clear expression\r\nof various situations in economic activity. Their\r\nusage is particularly effective in communicative\r\nspeech, mass media, and advertising texts.\r\nIn conclusion, phraseological units are\r\nan integral component of the language of\r\nentrepreneurship. They not only enhance the\r\naesthetic capacity of language in expressing\r\neconomic thought but also render communication\r\nmore straightforward, comprehensible, and\r\nimpactful. This, in turn, contributes to the\r\ndistinctiveness and development of economic\r\nlanguage and underscores the relevance of\r\nstudying them in applied linguistics.	Mazkur maqolada leksik birliklarning iqtisodiy nutq, xususan, tadbirkorlik sohasi doirasida\r\nfrazeologik birlik sifatida qoʻllanilishi tahlil qilinadi. Tadbirkorlik faoliyati bilan bogʻliq matnlarda uchraydigan frazeologik ifodalar, ularning\r\nleksik-semantik tuzilishi, uslubiy xususiyatlari\r\nva kommunikativ vazifalari oʻrganiladi. Shuningdek, ushbu frazeologizmlarning iqtisodiy tushunchalarni ifodalashda, obrazli va ta’sirchan fikr\r\nbildirishda tutgan oʻrni ochib beriladi.\r\nTadqiqot-maqolaning maqsadi ingliz va oʻzbek tillaridagi tadbirkorlik sohasiga oid leksik\r\nbirliklarning lingvistik xususiyatlarini ochib berish asosida tarjima qilish usullarini aniqlashdan\r\niborat.\r\nTadqiqotning vazifalari tilshunoslikda tadbirkorlik sohasi leksik birliklarining nazariy jihatdan\r\noʻrganilganlik darajasini yoritish, ularni diaxron\r\nva sinxron aspektda lingvistik xususiyatlarini\r\naniqlash; mazkur soha terminlarining derivatsion\r\njihatlarini, affiksal, morfemik-morfologik, leksik-semantik, funksional-semantik va sintaktik\r\nusulda yasalishini ochib berishdan iborat. Maqolada tavsifiy, qiyosiy-tipologik (chogʻishtirma),\r\ndiaxron va sinxron, komponent tahlil, semantik\r\nmaydon tahlili, lingvostatistik metodlar qoʻllanilgan.\r\nUshbu maqolaning ilmiy yangiligi – tadqiqotda yoritilgan tadbirkorlik sohasi leksik birliklarini\r\nxalq ogʻzaki nutqida koʻchma ma’noda qoʻllanilishi, bu nomlarning odamlar hayotida katta ahamiyat kasb etishi, iqtisodiyotda keng qoʻllanilgan\r\nnomlar, bu sohadagi frazeologik birliklar asoslab\r\nberildi.\r\nTadqiqot natijalariga koʻra, iqtisodiy nutqda\r\nishlatiladigan frazeologik birliklar odatiy leksik\r\nbirliklarga nisbatan ko‘proq emotsional, ekspressiv va obrazli ma’no yuklaydi. Ular nafaqat iqtisodiy mazmundagi matnlarni stilistik jihatdan\r\nboyitadi, balki iqtisodiy faoliyat jarayonidagi turli\r\nholatlarni aniq va qisqa ifodalashga xizmat qiladi.\r\nAyniqsa, muomala nutqida, ommaviy axborot vositalarida va reklama matnlarida bu birliklarning\r\nqoʻllanilishi sezilarli darajada samaradorlikni\r\noshiradi.\r\nXulosa qilib aytganda, frazeologik birliklar\r\ntadbirkorlik tilining ajralmas qismi boʻlib, ular\r\niqtisodiy fikrni ifodalashda nafaqat tilning estetik\r\nimkoniyatlarini kengaytiradi, balki muomala jarayonini sodda, tushunarli va ta’sirchan qiladi. Bu\r\nesa iqtisodiy tilning o‘ziga xosligi va rivojlanishiga xizmat qiladi hamda ularni oʻrganish amaliy tilshunoslik uchun dolzarb masala ekanligini\r\nko‘rsatadi.\r\n	В данной статье рассматривается использование лексических\r\nединиц в качестве фразеологических выражений в экономическом дискурсе, с особым акцентом на предпринимательство. В статье исследуются фразеологические\r\nвыражения, часто встречающиеся в текстах,\r\nотносящихся к предпринимательской деятельности, анализируются\r\nих лексико-семантическая структура, стилистические особенности\r\nи коммуникативные функции. Кроме того, в\r\nстатье освещается роль этих фразеологизмов\r\nв передаче экономических концепций и артикуляции\r\nидей ярким и убедительным образом.\r\nЦелью исследования является выявление\r\nметодов перевода, основанных на лингвистических характеристиках\r\nлексических единиц, связанных с предпринимательством,\r\nкак в английском, так и в узбекском языках. Цели исследования\r\nвключают в себя: выявление степени теоретической изученности лексических\r\nединиц в области предпринимательства в лингвистике; выявление\r\nих языковых особенностей как с диахронической, так и с синхронической точки зрения; и раскрытие\r\nдеривационных аспектов терминов в данной области,\r\nвключая их образование аффиксальным,\r\nморфемно-морфологическим, лексико-семантическим,\r\nфункционально-семантическим и синтаксическим методами.\r\nВ исследовании используются описательный, сравнительно-типологический (контрастивный), диахронический и синхронический, компонентный анализ, анализ семантического поля и лингвостатистические методы.\r\nНаучная новизна данной статьи заключается в\r\nобосновании образного использования предпринимательской\r\nлексики в разговорной речи, ее роли в\r\nжизни\r\nлюдей, ее использовании в экономике и\r\nналичии фразеологических единиц в этой области.\r\nСогласно результатам исследования, фразеологические\r\nединицы в экономическом дискурсе передают более\r\nэмоциональное, экспрессивное и образное значение,\r\nчем обычные лексические единицы. Они стилистически обогащают экономические\r\nтексты и способствуют четкому выражению\r\nразличных ситуаций экономической деятельности. Их\r\nиспользование особенно эффективно в коммуникативной речи, средствах массовой информации и рекламных текстах.\r\nВ заключение следует отметить, что фразеологические единицы являются\r\nнеотъемлемой частью языка\r\nпредпринимательства. Они не только усиливают\r\nэстетические возможности языка в выражении\r\nэкономической мысли, но и делают коммуникацию\r\nболее простой, понятной и\r\nэффективной. Это, в свою очередь, способствует\r\nсвоеобразию и развитию экономического\r\nязыка и подчёркивает актуальность\r\nих изучения в прикладной лингвистике.	10.36078/987655220	https://doi.org/10.36078/987655220	{"linguoculturological analysis","phraseological unit","functional analysis","ethnolinguistic analysis","cultural constant","electronic money","lexical unit",business,management,"economic discourse"}		318	\N	\N	\N	\N	1736112240	1742592300	1742851500	\N		{1}	f	0	0	0	f	1753921620	{"lingvokulturologik tahlil","frazeologik birlik","funksional tahlil","etnolingvistik tahlil","madaniy konstanta","elektron pul","leksik birlik",biznes,menejment,"iqtisodiy nutq"}	{"лингвокультурологический анализ","фразеологическая единица","функциональный анализ","этнолингвистический анализ","культурная константа","электронные деньги","лексическая единица",бизнес,менеджмент,"экономический дискурс"}	0
\.


--
-- TOC entry 5148 (class 0 OID 24796)
-- Dependencies: 249
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.settings (id, k, v, created_at) FROM stdin;
\.


--
-- TOC entry 5150 (class 0 OID 24802)
-- Dependencies: 251
-- Data for Name: submissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.submissions (id, user_id, status, title, abstract, is_special, is_dataset, check_copyright, keywords, classifications, check_ethical, check_consent, check_acknowledgements, is_used_previous, word_count, is_corresponding_author, main_author_id, sub_author_ids, is_competing_interests, notes, file_authors, file_anonymized, created_date, updated_at, editor_review_status) FROM stdin;
17	1	in_process	333	333 333 3 33 333 333 3 33333 333 3 33333 333 3 33333 333 3 33333 333 3 33	t	t	t	{$data,1,2,3,4,5,6,7,78}	{1,2,3}	t	t	t	t	3333	\N	8	{}	t	\N	authors_new_1757738963.docx	anonymized_new_1757738965.docx	1757738987	1757738987	assigned
16	1	rejected	123	qwqweeqweqweq qweqw eqw eqwe qwe qweqw eqwe qweqw eqw qwe qw eqw	t	t	t	{$data,1,2,3,4,5,6,7}	{1,2,3}	t	t	t	t	3333	\N	9	{}	t	Sabab	authors_16_1757738839.docx	anonymized_16_1757738843.docx	1757738830	1757739133	\N
18	5	rejected	IMPORTANCE OF IMPROVING STUDENTS’ WRITING COMPETENCE WHILE TEACHING FOREIGN LANGUAGES	Students’ writing competence while teaching them English as a foreign language (EFL) is considered to be one of the key goals of training future personnel at pedagogical higher educational institutions. This article deals with the theoretical and practical basis of teaching writing in order to achieve their writing competence is very important for future EFL personnel’s progress in learning writing based on its current status and tasks in a globalized context of the world. Also, it is known that writing has been viewed as a means of consolidating speaking, listening and reading skills of language learners in studying foreign languages which has an impact on the whole current process of teaching foreign languages (TFL). However, the implementation of modern innovative technologies and means in almost every aspect of a human’s life has resulted in improving not only spoken but also written communication among people around the world. \nThe participants of this research are the first-year students of the faculty of Foreign language and literature (English) who attended classes within the experimental and control groups (N=36) in the scope of writing lessons at Uzbekistan State World Languages University (UzSWLU).\nA mixed-method design was applied into the study: self-monitoring checklists (1), course-evaluation questionnaires (2), achievement tests (3), and semi-structured interviews (4) conducted at both of the groups. All the three methods (1, 2, & 3) were utilized with the help of platforms of Google Forms and Telegram Messenger while the last method (4) was held face-to-face by recording audios via a smartphone. \nFindings revealed that a writing skill as an educational goal has its own topics and language areas to be learned and acquired in practice. Furthermore, it was also perceived that in terms of improvements of quality and content factors of the writing course, principles of teaching writing, and typology of writing exercises, those features correlated significantly in training future personnel of this sphere. \nBased on the research findings, it is recommended that offline and online platforms of pedagogical higher education should be united to improve students’ writing skills, for instance, in the blended foreign language learning environment. Moreover, approaching writing as an educational goal instead of an educational means optimizes and updates the whole process of TFL writing in practice.	f	f	t	{$data,writing,"pedagogical higher education","written communication","teaching writing","writing skill","student’s written discourse","status of writing","educational goal","writing genre","written discourse"}	{5,39,43}	t	t	t	f	8000	\N	10	{}	f		authors_18_1757763709.docx	anonymized_18_1757763627.docx	1757763581	1757764282	\N
19	8	in_process	How Adults See Children vs. How Children See the World	This paper examines the historical transformation of adult perspectives on children and investigates how children’s own worldviews are articulated through literary and artistic works. In medieval societies, children were often regarded as “miniature adults,” with no clear recognition of a distinct childhood. From the modern era onward, they came to be viewed as incomplete beings in need of education and protection; the 20th century was even labeled “The Century of the Child.” While children were idealized as central agents of social progress, they were simultaneously enclosed within institutional structures such as schools.\nThe study addresses not only adult-driven narratives but also representations of the child’s perspective, as found in the works of creators such as Kazuo Umezu and Hayao Miyazaki. In these works, children are portrayed as possessing unique sensibilities and autonomy, often embodying a complex duality of innocence and cruelty. Such depictions challenge adult-centric ideals and question conventional images of children shaped by societal expectations.\nThe 1994 ratification of the Convention on the Rights of the Child by both Japan and Uzbekistan reflects global efforts to recognize children as rights-bearing individuals. Nevertheless, in education and broader social systems, insufficient understanding of children persists, and approaches rooted in children’s own voices and agency remain limited.\nThis paper argues that children should be recognized as fundamentally distinct from adults. Although the concept of childhood is historically and culturally variable, it is inadequate to interpret children solely through shifting social norms. A stance of respect—acknowledging children as complete human beings rather than immature adults—is essential. Education and governance should treat children as equals, actively honoring their perspectives. Artistic expressions offer valuable insight into the lived experiences of the world from a child’s point of view.	f	f	t	{$data,"Children’s perception","Innocence and cruelty",Childhood,"Children’s literature",Poetry,Adults,"Children’s rights."}	{9,22,47}	t	t	t	f	6000	\N	11	{}	f	\N	authors_19_1762627573.docx	anonymized_19_1762627580.docx	1762626461	1762627586	\N
\.


--
-- TOC entry 5152 (class 0 OID 24810)
-- Dependencies: 253
-- Data for Name: tariffs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tariffs (id, name, name_uz, name_ru, description, description_uz, description_ru, price_rub, price_uzs, price_usd, user_limit, is_default, created_at, updated_at, is_verified) FROM stdin;
1	Базовый	Asosiy	Базовый	Базовый бесплатный тариф	Bepul asosiy tarif	Базовый бесплатный тариф	0	0	0	100	f	1746481880	\N	f
2	Премиум	Premium	Премиум	Премиум тариф для расширенных возможностей	Kengaytirilgan imkoniyatlar uchun premium tarif	Премиум тариф для расширенных возможностей	500	75000	5.5	50	f	1746481880	\N	t
\.


--
-- TOC entry 5154 (class 0 OID 24822)
-- Dependencies: 255
-- Data for Name: translations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.translations (id, alias, content, content_uz, content_ru, created_at) FROM stdin;
1421	footer_rights	Published by Elsevier B.V. All rights are reserved, including those for text and data mining, AI training, and similar technologies.			\N
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
1420	footer_copyright	Copyright © 2024 Shandong University.			\N
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
1412	menu_for_uzgumya	For UzGUMya Researchers			\N
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
1465	altmetric	Altmetric			\N
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
1094	remember_me	Remember me	Meni eslab qol	Запомнить меня	\N
1097	login_with_orcid	Login with ORCID	ORCID orqali kirish	Войти через ORCID	\N
1103	my_purchases	My Purchases	Mening xaridlarim	Мои покупки	\N
1108	welcome	Welcome	Xush kelibsiz	Добро пожаловать	\N
1109	control_info	Here you can manage your information or submit new articles	Bu yerda siz ma'lumotlaringizni boshqarishingiz yoki yangi maqolalar yuborishingiz mumkin	Здесь вы можете управлять своей информацией или подавать новые статьи	\N
1116	edit_article	Edit Article	Maqolani tahrirlash	Редактировать статью	\N
1122	in_process	Under Review	Ko'rib chiqilmoqda	На рассмотрении	\N
1123	accepted	Accepted	Qabul qilingan	Принято	\N
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
1561	all_years	all_years			1752612108
1562	category	category			1752612108
1563	all_categories	all_categories			1752612108
1564	access_type	access_type			1752612108
1565	all_access_types	all_access_types			1752612108
1566	free_access	free_access			1752612108
1567	paid_access	paid_access			1752612108
1568	subscription_access	subscription_access			1752612108
1569	apply_filters	apply_filters			1752612108
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
1580	access_free	access_free			1752612118
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
1631	stat_1_value	5 Days	5 Kun	5 Дней	1769042596
1632	stat_1_text	Time to First Decision	Birinchi qarorgacha vaqt	Время до первого решения	1769042596
1633	stat_2_value	5 Days	5 Kun	5 Дней	1769042596
1634	stat_2_text	Time to First Decision	Birinchi qarorgacha vaqt	Время до первого решения	1769042596
1635	stat_3_value	5 Days	5 Kun	5 Дней	1769042596
1636	stat_3_text	Time to First Decision	Birinchi qarorgacha vaqt	Время до первого решения	1769042596
1638	stat_4_text	Time to First Decision	Birinchi qarorgacha vaqt	Время до первого решения	1769042596
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
1637	stat_4_value	5 Days	5 Kun	5 Дней	1769042596
1741	admin_users_patronymic	Patronymic	Otasining ismi	Отчество	1769048050
1688	admin_login_page_title	Login - FM-Admin	Kirish - FM-Admin	Вход в систему - FM-Admin	1769047871
1694	admin_login_forgot_password	Forgot password?	Parolni unutdingizmi?	Забыли пароль?	1769047871
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
2099	admin_label_user_limit	User Limit	Foydalanuvchilar limiti	Лимит пользователей	1769056098
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
1810	admin_status_published	Published	Nashr qilingan	Опубликовано	1769048438
1813	admin_placeholder_user_id	User ID	Foydalanuvchi ID	ID пользователя	1769048438
1814	admin_btn_apply	Apply	Qo'llash	Применить	1769048438
2072	admin_label_short_info	Short Description	Qisqa tavsif	Краткое описание	1769055922
1816	admin_submissions_col_user	User	Foydalanuvchi	Пользователь	1769048438
1817	admin_submissions_col_title	Title	Nomi	Название	1769048438
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
\.


--
-- TOC entry 5156 (class 0 OID 24828)
-- Dependencies: 257
-- Data for Name: user_doc_uploads; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_doc_uploads (id, user_id, work_title, file_path, verification_status, created_at, updated_at) FROM stdin;
3	8	teacher		pending	1762627518	1762627518
\.


--
-- TOC entry 5158 (class 0 OID 24834)
-- Dependencies: 259
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, name, second_name, father_name, email, password, country_id, region, rolename, is_blocked, is_notify, accept_rules_time, last_online, created_at, register_time, token, avatar, subscription_end_date, tariff_id, editor_specialization) FROM stdin;
3	ImmutableMultiDict([])	2	\N	test@exam2ple.com	2	1	\N	user	f	f	1738731380	1738731380	\N	\N	\N	\N	\N	\N	\N
4	Mark	Markov	\N	23@yandex.ru	23@yandex.ru	1	\N	user	f	f	1738731487	1738731487	\N	\N	\N	\N	\N	\N	\N
2	test	test	test	test@example.com	qwe3241	84	test	user	f	f	\N	\N	\N	\N	\N	\N	1752260400	2	\N
6	Иван	Петров	\N	editor1@journal.com	123	\N	\N	editor	f	f	\N	\N	1750616472	1750616472	\N	\N	\N	\N	Математика
7	Мария	Сидорова	\N	editor2@journal.com	123	\N	\N	editor	f	f	\N	\N	1750616472	1750616472	\N	\N	\N	\N	Физика
1	Abu	Samijonov	-	croownguuard@gmail.com	2	267	Tashkent	admin	f	f	1	1750641300	\N	1	UTgMcelqSDIyO9e1WN1s91i7Jz5hzZH5kxR5GLMYErg	/static/uploads/avatars/avatar_1_1739574824.jpg	1767207599	\N	\N
5	Solijon	Azizov		solijonazizov1@gmail.com	Qwe3241	267		admin	f	t	1740047709	1740047709	\N	\N	\N	\N	1777748400	\N	\N
8	Kuniyuki	Noto	None	notokuniyuki@gmail.com	1212noto	164	\N	user	f	t	1762623575	1762623575	\N	\N	\N	\N	\N	\N	\N
9	Iroda	Rahmanova	\N	irodarahmanova11@gmail.com	iroda2006	267	\N	user	f	t	1762937465	1762937465	\N	\N	\N	\N	\N	\N	\N
\.


--
-- TOC entry 5197 (class 0 OID 0)
-- Dependencies: 218
-- Name: author_profile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.author_profile_id_seq', 11, true);


--
-- TOC entry 5198 (class 0 OID 0)
-- Dependencies: 220
-- Name: editor_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.editor_assignments_id_seq', 4, true);


--
-- TOC entry 5199 (class 0 OID 0)
-- Dependencies: 222
-- Name: editor_notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.editor_notifications_id_seq', 1, false);


--
-- TOC entry 5200 (class 0 OID 0)
-- Dependencies: 224
-- Name: editorial_board_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.editorial_board_id_seq', 1, false);


--
-- TOC entry 5201 (class 0 OID 0)
-- Dependencies: 226
-- Name: files_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.files_id_seq', 1, true);


--
-- TOC entry 5202 (class 0 OID 0)
-- Dependencies: 228
-- Name: fix_classifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fix_classifications_id_seq', 52, true);


--
-- TOC entry 5203 (class 0 OID 0)
-- Dependencies: 230
-- Name: fix_country_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fix_country_id_seq', 274, true);


--
-- TOC entry 5204 (class 0 OID 0)
-- Dependencies: 232
-- Name: fix_issue_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fix_issue_categories_id_seq', 3, true);


--
-- TOC entry 5205 (class 0 OID 0)
-- Dependencies: 234
-- Name: issues_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.issues_id_seq', 13, true);


--
-- TOC entry 5206 (class 0 OID 0)
-- Dependencies: 236
-- Name: news_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.news_id_seq', 8, true);


--
-- TOC entry 5207 (class 0 OID 0)
-- Dependencies: 238
-- Name: pages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pages_id_seq', 19, true);


--
-- TOC entry 5208 (class 0 OID 0)
-- Dependencies: 240
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payments_id_seq', 19, true);


--
-- TOC entry 5209 (class 0 OID 0)
-- Dependencies: 242
-- Name: publication_citations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.publication_citations_id_seq', 1, false);


--
-- TOC entry 5210 (class 0 OID 0)
-- Dependencies: 244
-- Name: publication_figures_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.publication_figures_id_seq', 1, true);


--
-- TOC entry 5211 (class 0 OID 0)
-- Dependencies: 246
-- Name: publication_parts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.publication_parts_id_seq', 14, true);


--
-- TOC entry 5212 (class 0 OID 0)
-- Dependencies: 262
-- Name: publication_refs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.publication_refs_id_seq', 1, false);


--
-- TOC entry 5213 (class 0 OID 0)
-- Dependencies: 248
-- Name: publications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.publications_id_seq', 119, true);


--
-- TOC entry 5214 (class 0 OID 0)
-- Dependencies: 250
-- Name: settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.settings_id_seq', 1, false);


--
-- TOC entry 5215 (class 0 OID 0)
-- Dependencies: 252
-- Name: submissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.submissions_id_seq', 19, true);


--
-- TOC entry 5216 (class 0 OID 0)
-- Dependencies: 254
-- Name: tariffs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tariffs_id_seq', 4, true);


--
-- TOC entry 5217 (class 0 OID 0)
-- Dependencies: 256
-- Name: translations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.translations_id_seq', 2178, true);


--
-- TOC entry 5218 (class 0 OID 0)
-- Dependencies: 258
-- Name: user_doc_uploads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_doc_uploads_id_seq', 3, true);


--
-- TOC entry 5219 (class 0 OID 0)
-- Dependencies: 260
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 9, true);


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

