import { notFound } from "next/navigation";
import { getContent, CONTENT_SLUGS, faqEntities } from "../../../lib/content";
import { SITE_URL } from "../../../lib/site";
import "./content.css";

// Per-page structured data: an Article (so the guide is eligible as a cited
// source with authorship and freshness) plus a FAQPage built from the same
// question-shaped sections the page renders. Author/publisher reference the
// Organization @id defined once in the root layout, so the graph stays linked.
function buildJsonLd(c) {
  const path = `/content/${c.slug}`;
  const url = `${SITE_URL}${path}`;
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Article",
        "@id": `${url}#article`,
        headline: c.title,
        description: c.description,
        mainEntityOfPage: url,
        inLanguage: "en-US",
        ...(c.datePublished ? { datePublished: c.datePublished } : {}),
        ...(c.dateModified ? { dateModified: c.dateModified } : {}),
        author: { "@id": `${SITE_URL}/#organization` },
        publisher: { "@id": `${SITE_URL}/#organization` }
      },
      {
        "@type": "FAQPage",
        "@id": `${url}#faq`,
        mainEntity: faqEntities(c.slug)
      }
    ]
  };
}

// Pre-render every guide at build time.
export function generateStaticParams() {
  return CONTENT_SLUGS.map((slug) => ({ slug }));
}

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const c = getContent(slug);
  if (!c) return {};
  const path = `/content/${c.slug}`;
  return {
    title: c.title,
    description: c.description,
    alternates: {
      canonical: path,
      // Point AI clients at the clean Markdown mirror of this same page.
      types: { "text/markdown": `${SITE_URL}${path}.md` }
    },
    openGraph: { title: c.title, description: c.description, url: `${SITE_URL}${path}`, type: "article" }
  };
}

export default async function ContentPage({ params }) {
  const { slug } = await params;
  const c = getContent(slug);
  if (!c) notFound();

  return (
    <main className="publicShell">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(buildJsonLd(c)) }}
      />
      <article className="contentArticle">
        <p className="publicEyebrow">Guide for trades owners</p>
        <h1>{c.title}</h1>
        <p className="contentIntro">{c.intro}</p>

        {c.sections.map((section) => (
          <section key={section.heading} className="contentSection">
            <h2>{section.heading}</h2>
            {(section.body || []).map((para, i) => <p key={i}>{para}</p>)}
            {section.bullets?.length ? (
              <ul>{section.bullets.map((b, i) => <li key={i}>{b}</li>)}</ul>
            ) : null}
          </section>
        ))}

        {c.cta ? (
          <p className="contentCta">
            <a className="primaryCta" href={c.cta.href}>{c.cta.text}</a>
          </p>
        ) : null}
      </article>
    </main>
  );
}
