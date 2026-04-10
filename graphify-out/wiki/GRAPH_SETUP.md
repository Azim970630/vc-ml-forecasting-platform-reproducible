# 3D Graph Color Setup Guide

Your graph is ready, but the 3D Graph plugin colors need to be manually configured in Obsidian. Here's how:

## Quick Setup (30 seconds)

1. **Open Obsidian** → **Settings** → **3D Graph** (in left sidebar)
2. Look for **"Color Groups"** or **"Color by Community"** option
3. Enable **"Color by Community"**
4. Paste your color configuration (see below)

## Manual Color Configuration

If the plugin has a settings interface, enter these community-to-color mappings:

| Community | Color | Category |
|-----------|-------|----------|
| 0 | #00BCD4 | Feature Engineering |
| 1 | #9C27B0 | Models & Forecasting |
| 2 | #FF9800 | Reproducibility |
| 3 | #4CAF50 | Pipelines |
| 4 | #8D6E63 | Data Sources |
| 5 | #E53935 | Data Versioning |
| 6 | #9E9E9E | Base Classes |
| 7 | #FBC02D | Unit Tests |
| 8 | #BDBDBD | Utilities |
| 9 | #FFE082 | Test Fixtures |
| 10-11 | #7B1FA2 | Tests |
| 12 | #66BB6A | Pipeline Builders |
| 13 | #AED581 | Integration Tests |
| 15-29 | #80DEEA | Architecture Concepts |
| 30-31 | #CE93D8 | Forecaster Models |
| 32-34 | #B3E5FC | Feature Transformers |
| 35 | #D7CCC8 | CSV Data Source |
| 36-37 | #FFCC80 | Deployment |
| 38, 47 | #C8E6C9 | Ops & Governance |
| 39-41 | #E1BEE7 | Custom Patterns |
| 42-43 | #FFF9C4 | Testing |
| 44 | #FFE0B2 | Verification |
| 45, 50 | #FFCCBC | Audit & Lineage |
| 46 | #BBDEFB | MLflow Registry |
| 48-49, 51 | #D7CCC8 | Storage & Config |
| 52-55 | #F5F5F5 | Design Rationale |
| 56-58 | #E8EAF6 | Design Patterns |
| 59-60 | #CFD8DC | Dependencies |

## Alternative: Built-in Graph View

If the 3D Graph plugin is difficult to configure, use Obsidian's **built-in Graph View**:

1. Press `Ctrl+G` (or `Cmd+G` on Mac)
2. The colors are now configured in `.obsidian/graph.json` 
3. You should see color groups for: pipelines, data sources, reproducibility, etc.

## Troubleshooting

**Colors still not showing?**
- Make sure the 3D Graph plugin is **enabled** in Community Plugins
- Reload Obsidian (Ctrl+Shift+R)
- Check that `graph.json` has `"community": X` fields (it should)

**Want to change a color?**
- Edit this file: `graphify-out/wiki/.obsidian/plugins/3d-graph/data.json`
- Find the community number
- Change the hex color code
- Reload Obsidian

## File Locations

Configuration files are here:
```
graphify-out/wiki/.obsidian/
├── plugins/3d-graph/
│   ├── data.json          (color mappings)
│   ├── manifest.json      (plugin metadata)
│   └── styles.css         (visual styling)
└── graph.json             (built-in graph settings)
```

The actual graph data (with community assignments) is in:
```
graphify-out/graph.json    (225 nodes, 226 edges, 61 communities)
```
