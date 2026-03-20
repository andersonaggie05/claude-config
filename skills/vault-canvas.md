---
name: vault-canvas
description: Generate or regenerate Obsidian Canvas mind maps for system visualization
---

# /vault-canvas

Generate .canvas files in Obsidian's JSON format. Output to ~/vault/maps/.

## Obsidian Canvas JSON Schema

```json
{
  "nodes": [
    {
      "id": "unique-id",
      "x": 0, "y": 0,
      "width": 250, "height": 60,
      "type": "text",
      "text": "Node content (supports markdown)"
    },
    {
      "id": "file-node",
      "x": 300, "y": 0,
      "width": 250, "height": 400,
      "type": "file",
      "file": "path/to/file.md"
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "fromNode": "unique-id",
      "toNode": "file-node",
      "fromSide": "right",
      "toSide": "left",
      "label": "optional edge label"
    }
  ]
}
```

## Commands

- `/vault-canvas system` — regenerate system-architecture.canvas (all hooks, modules, skills, memory)
- `/vault-canvas system-with-vault` — regenerate full architecture canvas including vault layer (qmd, Obsidian, orient hook, ~/vault/ structure)
- `/vault-canvas modules` — regenerate module-composition.canvas
- `/vault-canvas projects` — regenerate project-dependencies.canvas
- `/vault-canvas {topic}` — generate ad-hoc canvas in ~/vault/maps/ad-hoc/
