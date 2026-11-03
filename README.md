# telmuunda.github.io
My personal portfolio website.

## Write a blog post

From the repository folder, run:

```sh
python3 scripts/blog_editor.py
```

Open http://127.0.0.1:8765/blog-editor.html in your browser. The local server also serves the rest of the site at that address, so you can preview it at http://127.0.0.1:8765/blog.html. The editor writes a static HTML post into `posts/` and adds it to `assets/data/blog-posts.json`. Posts appear in the blog list on their publication date (UTC); until then, they remain hidden from the list. Stop the local editor with Ctrl+C, then commit and push the new post and updated index to publish them on GitHub Pages.

The editor listens only on your own computer; it does not expose a GitHub token or write access to the public website. The committed post files and index are still present in the repository before the publication date, so scheduling hides posts from the site’s list but is not a way to keep their contents secret.

Run the Python tests with:

```sh
python3 -m unittest discover -s tests -p '*_test.py'
```

## Monthly science feature

The featured physics and astronomy story is selected from ScienceDaily's public RSS feeds and stored in `assets/data/physics-news.json`. GitHub Actions refreshes it on the first day of each month. To refresh it manually, run:

```sh
python3 scripts/update_physics_news.py
```

The workflow needs Actions write permission to commit the updated news file to the repository.
