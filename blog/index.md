---
layout: default
title: Blog
---

# Two Cents Blog
<ul class="blog-list">
  {% for post in site.posts %}
    <li>
      <a class="blog-card" href="{{ post.url | relative_url }}">
        <h2 class="blog-title">{{ post.title }}</h2>
        <p class="blog-meta">
          {{ post.date | date: "%B %d, %Y" }}
        </p>
      </a>
    </li>
  {% endfor %}
</ul>

