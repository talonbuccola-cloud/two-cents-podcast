import datetime
import re
import shutil
import unicodedata
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class BlogComposerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Two Cents Blog Composer")
        self.root.geometry("1280x780")

        self.repo_root = Path(__file__).resolve().parents[2]
        self.posts_dir = self.repo_root / "_posts"
        self.uploads_dir = self.repo_root / "assets" / "uploads"

        self.featured_local_path = None
        self.featured_dest_name = None

        self.images = []
        self.image_sources = set()
        self.preview_after_id = None

        self.reserved_upload_names = {p.name.lower() for p in self.uploads_dir.glob("*") if p.is_file()}

        self._build_ui()
        self.date_var.set(datetime.date.today().isoformat())
        self.on_title_changed()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        top = ttk.LabelFrame(main, text="Post Details", padding=10)
        top.pack(fill="x")

        self.title_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.permalink_var = tk.StringVar()
        self.auto_permalink_var = tk.BooleanVar(value=True)
        self.featured_var = tk.StringVar()
        self.placement_var = tk.StringVar(value="right")

        ttk.Label(top, text="Title").grid(row=0, column=0, sticky="w")
        title_entry = ttk.Entry(top, textvariable=self.title_var, width=62)
        title_entry.grid(row=0, column=1, columnspan=4, sticky="ew", padx=(8, 10))

        ttk.Label(top, text="Publish Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(top, textvariable=self.date_var, width=18).grid(row=1, column=1, sticky="w", padx=(8, 10), pady=(8, 0))

        ttk.Label(top, text="Permalink").grid(row=1, column=2, sticky="w", pady=(8, 0))
        self.permalink_entry = ttk.Entry(top, textvariable=self.permalink_var, width=34)
        self.permalink_entry.grid(row=1, column=3, sticky="ew", padx=(8, 4), pady=(8, 0))
        ttk.Checkbutton(top, text="Auto", variable=self.auto_permalink_var).grid(row=1, column=4, sticky="w", pady=(8, 0))

        ttk.Label(top, text="Featured Image").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(top, textvariable=self.featured_var, width=62).grid(row=2, column=1, columnspan=2, sticky="ew", padx=(8, 10), pady=(8, 0))
        ttk.Button(top, text="Choose Featured Image...", command=self.choose_featured_image).grid(
            row=2, column=3, columnspan=2, sticky="e", pady=(8, 0)
        )

        for i in range(5):
            top.columnconfigure(i, weight=1 if i in (1, 3) else 0)

        self.title_var.trace_add("write", self.on_title_changed)
        self.permalink_entry.bind("<KeyPress>", self.on_permalink_manual_edit)
        self.permalink_entry.bind("<<Paste>>", self.on_permalink_manual_edit)

        mid = ttk.Panedwindow(main, orient="horizontal")
        mid.pack(fill="both", expand=True, pady=(12, 0))

        left = ttk.LabelFrame(mid, text="Post Body", padding=10)
        preview = ttk.LabelFrame(mid, text="Live Preview", padding=10)
        right = ttk.LabelFrame(mid, text="Image Inserter", padding=10)
        mid.add(left, weight=3)
        mid.add(preview, weight=2)
        mid.add(right, weight=2)

        self.body_text = tk.Text(left, wrap="word", undo=True)
        body_scroll = ttk.Scrollbar(left, orient="vertical", command=self.body_text.yview)
        self.body_text.configure(yscrollcommand=body_scroll.set)
        self.body_text.pack(side="left", fill="both", expand=True)
        body_scroll.pack(side="right", fill="y")

        self.body_text.bind("<KeyRelease>", self.schedule_preview_update)
        self.body_text.bind("<<Paste>>", self.schedule_preview_update)
        self.body_text.bind("<ButtonRelease-1>", self.schedule_preview_update)

        self.preview_text = tk.Text(preview, wrap="word", state="disabled", background="#f7f7f7")
        preview_scroll = ttk.Scrollbar(preview, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")

        ttk.Button(right, text="Add Images...", command=self.add_images).pack(fill="x")

        self.image_list = tk.Listbox(right, height=16)
        self.image_list.pack(fill="both", expand=True, pady=(8, 8))

        placement_row = ttk.Frame(right)
        placement_row.pack(fill="x")

        ttk.Label(placement_row, text="Placement").pack(side="left")
        placement_combo = ttk.Combobox(
            placement_row,
            textvariable=self.placement_var,
            values=["left", "right", "full width"],
            state="readonly",
            width=14,
        )
        placement_combo.pack(side="left", padx=(8, 0))

        btn_row = ttk.Frame(right)
        btn_row.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_row, text="Insert At Cursor", command=self.insert_selected_image).pack(side="left")
        ttk.Button(btn_row, text="Remove Selected", command=self.remove_selected_image).pack(side="left", padx=(8, 0))

        bottom = ttk.Frame(main)
        bottom.pack(fill="x", pady=(12, 0))

        ttk.Button(bottom, text="Generate Post", command=self.generate_post).pack(side="right")
        ttk.Button(bottom, text="Clear Form", command=self.clear_form).pack(side="right", padx=(0, 8))

        note = (
            "This local tool writes only to _posts and assets/uploads inside this repo. "
            "Public site files remain unchanged."
        )
        ttk.Label(main, text=note).pack(anchor="w", pady=(8, 0))

        self.update_preview()

    def slugify(self, value: str) -> str:
        # Keep one canonical slug implementation for post filenames and permalinks.
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
        slug = re.sub(r"[^a-z0-9]+", "-", normalized)
        slug = re.sub(r"-{2,}", "-", slug)
        slug = slug.strip("-")
        return slug or "post"

    def ensure_permalink(self, raw: str, title: str) -> str:
        value = (raw or "").strip()
        if not value:
            value = f"/blog/{self.slugify(title)}/"
        if not value.startswith("/"):
            value = "/" + value
        if not value.endswith("/"):
            value = value + "/"
        return value

    def normalize_pasted_text(self, text: str) -> str:
        if not text:
            return text

        replacements = {
            "â€™": "'",
            "â€œ": '"',
            "â€": '"',
            "â€”": "--",
            "â€“": "--",
            "Â": "",
            "�": "",
            "’": "'",
            "“": '"',
            "”": '"',
            "—": "--",
            "–": "--",
        }

        normalized = text
        for bad, good in replacements.items():
            normalized = normalized.replace(bad, good)
        return normalized

    def on_title_changed(self, *_args):
        if self.auto_permalink_var.get():
            slug = self.slugify(self.title_var.get())
            self.permalink_var.set(f"/blog/{slug}/")

    def on_permalink_manual_edit(self, _event=None):
        self.auto_permalink_var.set(False)

    def schedule_preview_update(self, _event=None):
        if self.preview_after_id is not None:
            self.root.after_cancel(self.preview_after_id)
        self.preview_after_id = self.root.after(120, self.update_preview)

    def update_preview(self):
        self.preview_after_id = None
        body = self.body_text.get("1.0", "end-1c")
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", body)
        self.preview_text.configure(state="disabled")

    def reserve_unique_name(self, base_name: str) -> str:
        base = Path(base_name)
        stem = self.slugify(base.stem)
        ext = base.suffix.lower() or ".img"

        candidate = f"{stem}{ext}"
        idx = 2
        while candidate.lower() in self.reserved_upload_names:
            candidate = f"{stem}-{idx}{ext}"
            idx += 1

        self.reserved_upload_names.add(candidate.lower())
        return candidate

    def planned_upload_name(self, source_path: str) -> str:
        source = Path(source_path)
        ext = source.suffix.lower() or ".img"
        base = f"{self.slugify(source.stem)}{ext}"
        return self.reserve_unique_name(base)

    def choose_featured_image(self):
        path = filedialog.askopenfilename(
            title="Select Featured Image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.gif;*.avif;*.bmp"), ("All files", "*.*")],
        )
        if not path:
            return

        self.featured_local_path = path
        self.featured_dest_name = self.planned_upload_name(path)
        self.featured_var.set(f"/assets/uploads/{self.featured_dest_name}")

    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Select Images To Insert",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.gif;*.avif;*.bmp"), ("All files", "*.*")],
        )
        if not files:
            return

        for path in files:
            normalized = str(Path(path).resolve())
            if normalized in self.image_sources:
                continue

            dest_name = self.planned_upload_name(normalized)
            rec = {"src": normalized, "dest": dest_name}
            self.images.append(rec)
            self.image_sources.add(normalized)
            self.image_list.insert("end", f"{dest_name}  <=  {Path(normalized).name}")

    def remove_selected_image(self):
        selected = list(self.image_list.curselection())
        if not selected:
            return

        for idx in reversed(selected):
            rec = self.images.pop(idx)
            self.image_sources.discard(rec["src"])
            self.image_list.delete(idx)
        self.schedule_preview_update()

    def snippet_for(self, web_path: str, placement: str) -> str:
        if placement == "left":
            style = 'float: left; max-width: 46%; height: auto; margin: 0.25em 1.1em 0.9em 0;'
            return f"![]({web_path}){{: style=\"{style}\"}}\n\n"

        if placement == "right":
            style = 'float: right; max-width: 46%; height: auto; margin: 0.25em 0 0.9em 1.1em;'
            return f"![]({web_path}){{: style=\"{style}\"}}\n\n"

        style = 'display: block; width: 100%; max-width: 100%; height: auto; margin: 1.25em 0;'
        return (
            "<div style=\"clear: both;\"></div>\n"
            f"![]({web_path}){{: style=\"{style}\"}}\n"
            "<div style=\"clear: both;\"></div>\n\n"
        )

    def insert_selected_image(self):
        selection = self.image_list.curselection()
        if not selection:
            messagebox.showwarning("No Image Selected", "Select an image from the list first.")
            return

        rec = self.images[selection[0]]
        web_path = f"/assets/uploads/{rec['dest']}"
        snippet = self.snippet_for(web_path, self.placement_var.get())
        self.body_text.insert("insert", snippet)
        self.body_text.focus_set()
        self.schedule_preview_update()

    def safe_copy(self, src_path: str, preferred_name: str) -> str:
        src = Path(src_path)
        target = self.uploads_dir / preferred_name

        if target.exists():
            if src.resolve() == target.resolve():
                return target.name
            stem = self.slugify(target.stem)
            ext = target.suffix.lower()
            idx = 2
            while True:
                alt = self.uploads_dir / f"{stem}-{idx}{ext}"
                if not alt.exists():
                    target = alt
                    break
                idx += 1

        shutil.copy2(src, target)
        return target.name

    def generate_post(self):
        title = self.title_var.get().strip()
        date_str = self.date_var.get().strip()
        permalink = self.ensure_permalink(self.permalink_var.get(), title)
        featured_image = self.featured_var.get().strip()
        body = self.body_text.get("1.0", "end").strip()

        title = self.normalize_pasted_text(title)
        body = self.normalize_pasted_text(body)

        if not title:
            messagebox.showerror("Missing Title", "Please enter a title.")
            return

        if not date_str:
            messagebox.showerror("Missing Date", "Please enter a publish date in YYYY-MM-DD format.")
            return

        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Date must be in YYYY-MM-DD format.")
            return

        if not featured_image:
            messagebox.showerror("Missing Featured Image", "Please enter or choose a featured image.")
            return

        if not body:
            messagebox.showerror("Missing Body", "Please paste the blog post body.")
            return

        slug = self.slugify(title)
        post_name = f"{date_str}-{slug}.md"

        self.posts_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

        post_path = self.posts_dir / post_name
        if post_path.exists():
            ok = messagebox.askyesno("Post Exists", f"{post_name} already exists. Overwrite it?")
            if not ok:
                return

        replace_map = {}

        for rec in self.images:
            original_web = f"/assets/uploads/{rec['dest']}"
            final_name = self.safe_copy(rec["src"], rec["dest"])
            rec["dest"] = final_name
            final_web = f"/assets/uploads/{final_name}"
            if original_web != final_web:
                replace_map[original_web] = final_web

        if self.featured_local_path and self.featured_dest_name:
            original_featured = f"/assets/uploads/{self.featured_dest_name}"
            final_featured_name = self.safe_copy(self.featured_local_path, self.featured_dest_name)
            final_featured = f"/assets/uploads/{final_featured_name}"
            if featured_image == original_featured:
                featured_image = final_featured
            self.featured_var.set(featured_image)

        for old, new in replace_map.items():
            body = body.replace(old, new)

        escaped_title = title.replace('"', '\\"')

        content = (
            "---\n"
            "layout: default\n"
            f"title: \"{escaped_title}\"\n"
            f"date: {date_str}\n"
            f"permalink: {permalink}\n"
            f"featured_image: \"{featured_image}\"\n"
            "---\n\n"
            f"{body}\n"
        )

        post_path.write_text(content, encoding="utf-8")

        messagebox.showinfo(
            "Post Generated",
            f"Saved post:\n{post_path}\n\nImages are in:\n{self.uploads_dir}\n\nNext: commit and push with GitHub Desktop.",
        )

    def clear_form(self):
        if not messagebox.askyesno("Clear Form", "Clear all fields for a new post?"):
            return

        self.title_var.set("")
        self.date_var.set(datetime.date.today().isoformat())
        self.auto_permalink_var.set(True)
        self.permalink_var.set("")
        self.featured_var.set("")
        self.featured_local_path = None
        self.featured_dest_name = None

        self.body_text.delete("1.0", "end")
        self.images.clear()
        self.image_sources.clear()
        self.image_list.delete(0, "end")
        self.update_preview()


def main():
    root = tk.Tk()
    app = BlogComposerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
