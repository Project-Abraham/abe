# ABE
**A**bstract **B**rushes & **E**ntities

Python module for processing Brushes & Entities

Designed for level editor files used in Quake-based game engines


## Features

> TODO: `bite` texture & material parsers

> TODO: `bish` shader parsers

### Atomic Foundation
 * `base`
   - `Brush` & `BrushSide`
   - `Entity`
   - `MapFile`
 * `texture` (Texture Projection)
   - `ProjectionAxis`
   - `TextureVector`

### Physics & Geometry Tools
From [`ass`](https://github.com/snake-biscuits/ass)
 * `geometry`
   - `Model`, `Mesh`, `Polygon` & `Vertex`
   - abstract `Material` (for assignment)
 * `physics`
   - `Brush`
   - `AABB`
   - `Plane`
 * `scenes`
   for interchanging w/ common 3D file formats

### Parsers

| extension | name | editor(s) |
| :--- | :--- | :--- |
| `*.map` | `id_software.QuakeMap` | TrenchBroom & MRVN-Radiant |
| `*.map` | `infinity_ward.CoD4Map` | CoD4Radiant |
| `*.map` | `valve.Valve220Map` | TrenchBroom |
| `*.vmf` | `valve.Vmf` | Hammer & Hammer++ |


## Installation

```sh
$ pip install "abe @ git+ssh://git@github.com:Project-Abraham/abe.git"
```


## Usage

> TODO
