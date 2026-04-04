---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
# Must match a location `id` in data/locations.yaml
location: edinburgh
draft: false

# Add each photo as an item in this list.
# `src` is the Cloudinary path after /upload/ — just the filename path.
# `caption` is optional alt text / caption shown in the gallery.
photos:
  - src: "photos/edinburgh/photo-1.jpg"
    caption: "Arthur's Seat at sunrise"
  - src: "photos/edinburgh/photo-2.jpg"
    caption: "Old Town from Calton Hill"
---
