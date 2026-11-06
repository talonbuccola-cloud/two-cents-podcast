---
layout: default
title: Blog
---
# Two Cents Blog

<div class="blog-search-wrap">
  <label class="blog-search-label" for="blog-search">Find a movie</label>
  <input class="blog-search" id="blog-search" type="search" placeholder="Try “corn”, “shark”, “1984”…" autocomplete="off">
  <p class="blog-count">{{ site.posts | size }} reviews and counting. Pick a theme to open its episodes.</p>
</div>

{% assign grouped_slugs = "" %}
{% for theme in site.data.post_themes %}
  {% assign theme_posts = "" | split: "" %}
  {% for slug in theme.movies %}
    {% for post in site.posts %}
      {% if post.slug == slug %}
        {% assign theme_posts = theme_posts | push: post %}
        {% assign grouped_slugs = grouped_slugs | append: slug | append: "," %}
      {% endif %}
    {% endfor %}
  {% endfor %}
  {% if theme_posts.size > 0 %}
  <section class="theme-card" data-theme="{{ theme.name | downcase }}">
    <button class="theme-head" type="button" aria-expanded="false">
      <span class="theme-posters">
        {% for post in theme_posts limit: 4 %}{% if post.featured_image %}<img src="{{ post.featured_image }}" alt="" class="theme-poster">{% endif %}{% endfor %}
      </span>
      <span class="theme-info">
        <span class="theme-name">{{ theme.name }}</span>
        <span class="theme-movies">{% for post in theme_posts %}{{ post.title }}{% unless forloop.last %} · {% endunless %}{% endfor %}</span>
        <span class="theme-count">{{ theme_posts.size }} episode{% if theme_posts.size != 1 %}s{% endif %} — tap to open</span>
      </span>
    </button>
    <div class="theme-body" hidden>
      <ul class="blog-list">
        {% for post in theme_posts %}
          <li class="blog-item" data-search="{{ post.title | downcase }} {{ post.date | date: '%Y' }}">
            <a class="blog-card" href="{{ post.url | relative_url }}">
              {% if post.featured_image %}
                <img src="{{ post.featured_image }}" alt="{{ post.title }}" class="post-thumbnail" style="object-position: {{ post.thumbnail_position | default: 'center top' }};">
              {% endif %}
              <h3 class="blog-title">{{ post.title }}</h3>
              <p class="blog-meta">
                {{ post.date | date: "%B %d, %Y" }}
              </p>
            </a>
          </li>
        {% endfor %}
      </ul>
    </div>
  </section>
  {% endif %}
{% endfor %}

{% assign rest = "" | split: "" %}
{% for post in site.posts %}
  {% assign probe = post.slug | append: "," %}
  {% unless grouped_slugs contains probe %}
    {% assign rest = rest | push: post %}
  {% endunless %}
{% endfor %}
{% if rest.size > 0 %}
<section class="theme-card" data-theme="more episodes">
  <button class="theme-head" type="button" aria-expanded="false">
    <span class="theme-posters">
      {% for post in rest limit: 4 %}{% if post.featured_image %}<img src="{{ post.featured_image }}" alt="" class="theme-poster">{% endif %}{% endfor %}
    </span>
    <span class="theme-info">
      <span class="theme-name">More Episodes</span>
      <span class="theme-movies">{% for post in rest %}{{ post.title }}{% unless forloop.last %} · {% endunless %}{% endfor %}</span>
      <span class="theme-count">{{ rest.size }} episode{% if rest.size != 1 %}s{% endif %} — tap to open</span>
    </span>
  </button>
  <div class="theme-body" hidden>
    <ul class="blog-list">
      {% for post in rest %}
        <li class="blog-item" data-search="{{ post.title | downcase }} {{ post.date | date: '%Y' }}">
          <a class="blog-card" href="{{ post.url | relative_url }}">
            {% if post.featured_image %}
              <img src="{{ post.featured_image }}" alt="{{ post.title }}" class="post-thumbnail" style="object-position: {{ post.thumbnail_position | default: 'center top' }};">
            {% endif %}
            <h3 class="blog-title">{{ post.title }}</h3>
            <p class="blog-meta">
              {{ post.date | date: "%B %d, %Y" }}
            </p>
          </a>
        </li>
      {% endfor %}
    </ul>
  </div>
</section>
{% endif %}

<p class="blog-empty" id="blog-empty" hidden>No movie matches that. Try a shorter piece of the title.</p>

<script>
(function () {
  var input = document.getElementById('blog-search');
  var empty = document.getElementById('blog-empty');

  function setOpen(section, open) {
    var body = section.querySelector('.theme-body');
    var head = section.querySelector('.theme-head');
    if (body) body.hidden = !open;
    if (head) head.setAttribute('aria-expanded', open ? 'true' : 'false');
    section.classList.toggle('open', open);
  }

  document.querySelectorAll('.theme-card').forEach(function (section) {
    var head = section.querySelector('.theme-head');
    head.addEventListener('click', function () {
      setOpen(section, section.querySelector('.theme-body').hidden);
    });
  });

  if (input) {
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var anyVisible = false;
      document.querySelectorAll('.theme-card').forEach(function (section) {
        var sectionVisible = false;
        section.querySelectorAll('.blog-item').forEach(function (item) {
          var show = !q || item.getAttribute('data-search').indexOf(q) !== -1;
          item.style.display = show ? '' : 'none';
          if (show) sectionVisible = true;
        });
        if (!q) {
          section.style.display = '';
          section.querySelectorAll('.blog-item').forEach(function (item) { item.style.display = ''; });
          anyVisible = true;
        } else {
          section.style.display = sectionVisible ? '' : 'none';
          if (sectionVisible) { setOpen(section, true); anyVisible = true; }
        }
      });
      empty.hidden = anyVisible;
    });
  }
})();
</script>
