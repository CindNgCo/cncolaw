# Editing Articles

The article section is separated from the homepage.

To add or change articles, edit:

```text
articles/articles.js
```

Each article has:

```js
{
  slug: "short-url-name",
  title: "Article title",
  date: "2026-07-05",
  category: "Property",
  summary: "Short summary shown on the articles page.",
  body: [
    {
      heading: "Section heading",
      paragraphs: [
        "First paragraph.",
        "Second paragraph."
      ]
    }
  ]
}
```

The public article link will be:

```text
/articles/short-url-name.html
```

The homepage is not affected except for the Articles link in the navigation and footer.
