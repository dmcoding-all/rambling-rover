---
title: "{{ replace .Name "-" " " | title }}"
# Must match the `id` in data/locations.yaml
location_id: {{ .Name }}

# Travel recommendations for this location
# Types: Stay, Eat, Do, Hike, Transport, Tip
recommendations:
  - type: Do
    name: ""
    note: ""
    url: ""
  - type: Eat
    name: ""
    note: ""
    url: ""
  - type: Stay
    name: ""
    note: ""
    url: ""
  - type: Hike
    name: ""
    note: ""
    url: ""
---

Write a short intro about this location here. This appears at the top of the location page above the tabs.
