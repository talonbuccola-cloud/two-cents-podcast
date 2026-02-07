---
layout: default
title: Blog
---

# Two Cents Blog

This is where our episode critiques will live.
<p><strong>Debug:</strong> site.posts count = {{ site.posts | size }}</p>

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      ({{ post.date | date: "%Y-%m-%d" }})
    </li>
  {% endfor %}
</ul>

