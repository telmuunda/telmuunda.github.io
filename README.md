# telmuunda.github.io
My personal portfolio website.

## Write a blog post

From the repository folder, run:

```sh
python3 scripts/blog_editor.py
```

Open http://127.0.0.1:8765 in your browser. The editor writes a static HTML post into `posts/` and adds it to the blog list. Stop the local editor with Ctrl+C. Commit and push the new post and updated index to publish it on GitHub Pages.

The editor listens only on your own computer; it does not expose a GitHub token or write access to the public website.

## Monthly science feature

The featured physics and astronomy story is selected from ScienceDaily's public RSS feeds and stored in `assets/data/physics-news.json`. GitHub Actions refreshes it on the first day of each month. To refresh it manually, run:

```sh
python3 scripts/update_physics_news.py
```

The workflow needs Actions write permission to commit the updated news file to the repository.
