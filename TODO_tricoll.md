# Tricoll

## `mp_angel_city` stats
```
  9K TricollHeader (Models)
770K TricollTriangle
```

## Plan
 - [ ] Merge Tricoll meshes for each solid entity
   - [ ] Group by GridCell
     - [ ] split worldspawn grid & global cell?
   - [ ] Reset origin to align with entity origin
 - [ ] save each tricoll blob to a mesh
       `.obj`; group geosets & object meshes


## Prototype
```python
solid_entity_geo_sets: Dict[int, Set[GeoSet]] = ...
for solid_entity, geo_sets in segs.items():
  for geo_set in geo_sets:
    for primitive in geo_set:
      if primitive.type == TRICOLL:
        ...
```

### Notes
 * GeoSet groups don't make sense
   - primitives can appear in multiple groups
   - not bothering with the BVH heirarchy (grid>cell>geoset>prim>tricoll>node>tri)
