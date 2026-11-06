"""Small, original curated IT taxonomy; not a repackaged ESCO/O*NET dataset."""

from functools import lru_cache

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
from spacy.util import filter_spans

TAXONOMY = {
    "Languages": {
        "Python": [],
        "JavaScript": ["JS"],
        "TypeScript": [],
        "Java": [],
        "C++": [],
        "C#": [],
        "Go": ["Golang"],
        "Rust": [],
        "SQL": [],
        "R": ["R language"],
        "Kotlin": [],
        "Swift": [],
    },
    "Web": {
        "React": ["ReactJS", "React.js", "React JS"],
        "Next.js": ["NextJS"],
        "Vue": ["Vue.js"],
        "HTML": ["HTML5"],
        "CSS": ["CSS3"],
        "Tailwind CSS": ["Tailwind"],
        "Angular": [],
    },
    "Backend": {
        "FastAPI": [],
        "Django": [],
        "Flask": [],
        "Node.js": ["NodeJS", "Node JS"],
        "Express": ["Express.js"],
        "REST APIs": ["REST API", "RESTful"],
        ".NET": ["ASP.NET"],
        "GraphQL": [],
    },
    "Databases": {
        "PostgreSQL": ["Postgres", "Postgre SQL"],
        "MySQL": [],
        "MongoDB": [],
        "Redis": [],
        "SQLite": [],
        "Elasticsearch": [],
    },
    "AI & ML": {
        "Machine Learning": ["ML"],
        "PyTorch": [],
        "TensorFlow": [],
        "scikit-learn": ["sklearn"],
        "NLP": ["Natural Language Processing"],
        "spaCy": [],
        "Transformers": [],
        "NumPy": [],
        "pandas": [],
    },
    "Cloud": {"AWS": ["Amazon Web Services"], "Azure": [], "Google Cloud": ["GCP"], "Terraform": []},
    "DevOps": {
        "Docker": [],
        "Kubernetes": ["K8s"],
        "CI/CD": [],
        "Git": [],
        "GitHub Actions": [],
        "Linux": [],
        "Jenkins": [],
    },
    "Security": {"OAuth": ["OAuth2"], "OWASP": [], "Penetration Testing": [], "Network Security": []},
    "Data": {
        "Apache Spark": ["Spark"],
        "Airflow": [],
        "Kafka": [],
        "ETL": [],
        "Power BI": [],
        "Tableau": [],
        "Excel": [],
    },
    "Mobile": {"React Native": [], "Flutter": [], "Android": [], "iOS": []},
    "Testing": {"pytest": [], "Playwright": [], "Jest": [], "Selenium": [], "Unit Testing": []},
    "Professional": {
        "Communication": [],
        "Leadership": [],
        "Project Management": [],
        "Agile": [],
        "Scrum": [],
    },
}
ALIASES = {
    alias.casefold(): name
    for group in TAXONOMY.values()
    for name, aliases in group.items()
    for alias in [name, *aliases]
}
CATEGORIES = {name: category for category, group in TAXONOMY.items() for name in group}
RESOURCES = {
    "Python": "https://docs.python.org/3/tutorial/",
    "FastAPI": "https://fastapi.tiangolo.com/tutorial/",
    "Docker": "https://docs.docker.com/get-started/",
    "PostgreSQL": "https://www.postgresql.org/docs/current/tutorial.html",
    "React": "https://react.dev/learn",
    "AWS": "https://aws.amazon.com/training/",
    "GitHub Actions": "https://docs.github.com/en/actions",
    "Kubernetes": "https://kubernetes.io/docs/tutorials/",
    "TypeScript": "https://www.typescriptlang.org/docs/",
    "PyTorch": "https://pytorch.org/tutorials/",
    "Git": "https://git-scm.com/doc",
    "Next.js": "https://nextjs.org/docs",
}


def canonical_name(value: str) -> str:
    return ALIASES.get(value.casefold(), value)


@lru_cache
def matcher():
    nlp = spacy.blank("en")
    phrases = PhraseMatcher(nlp.vocab, attr="LOWER")
    for group in TAXONOMY.values():
        for name, aliases in group.items():
            phrases.add(name, [nlp.make_doc(s) for s in [name, *aliases]])
    return nlp, phrases


def extract_skills(sections: dict[str, str]):
    nlp, phrases = matcher()
    found = {}
    for section, text in sections.items():
        doc = nlp.make_doc(text)
        # Prefer the full canonical phrase: "React JS" must not separately
        # assert JavaScript, nor "Postgre SQL" assert an extra SQL skill.
        spans = filter_spans([Span(doc, start, end, label=match_id) for match_id, start, end in phrases(doc)])
        for span in spans:
            name = span.label_
            if name in {"Go", "R"} and span.text.lower() in {"go", "r"}:
                if section != "skills" and not any(
                    w in text.lower() for w in ["programming", "golang", "language"]
                ):
                    continue
            evidence = text[max(0, span.start_char - 70) : min(len(text), span.end_char + 100)].strip()
            found.setdefault(
                name,
                {
                    "name": name,
                    "category": CATEGORIES[name],
                    "source_section": section,
                    "evidence": evidence,
                    "method": "phrase_match",
                    "user_verified": False,
                },
            )
    return sorted(found.values(), key=lambda item: item["name"])
