# Knowledge Graph Tools - Usage Guide

## Overview

The Knowledge Graph incarnation provides tools for managing entities, relationships, and observations in a Neo4j-based knowledge graph.

## Common Issues and Solutions

### Issue: "Error: All observations must have a 'contents' array"

**Problem**: The `add_observations` tool expects a specific data structure that wasn't clear from the original documentation.

**Solution**: Use the correct format with `contents` as an array:

```json
[
    {
        "entityName": "Deep Learning Models",
        "contents": ["First observation", "Second observation", "Third observation"]
    }
]
```

### Issue: "Property values can only be of primitive types"

**Problem**: Neo4j doesn't accept complex nested objects as property values.

**Solution**:
1. Create entities with empty observations: `"observations": []`
2. Then use `add_observations` to add detailed content separately

## Tool Usage Examples

### 1. Creating Entities

```json
{
    "entities": [
        {
            "name": "Deep Learning Models",
            "entityType": "Technology",
            "observations": []
        }
    ]
}
```

### 2. Adding Observations (Multiple)

```json
{
    "observations": [
        {
            "entityName": "Deep Learning Models",
            "contents": [
                "Machine learning models that use neural networks",
                "Often trained with SGD",
                "Can suffer from catastrophic forgetting"
            ]
        }
    ]
}
```

### 3. Adding Single Observation (Convenience)

```json
{
    "entityName": "Deep Learning Models",
    "content": "A single observation about deep learning models"
}
```

### 4. Creating Relations

```json
{
    "relations": [
        {
            "from": "Deep Learning Models",
            "to": "Stochastic Gradient Descent",
            "relationType": "TRAINED_WITH"
        }
    ]
}
```

## Available Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `create_entities` | Create new entities | `entities`: list with name, entityType, observations |
| `add_observations` | Add multiple observations | `observations`: list with entityName, contents array |
| `add_single_observation` | Add one observation | `entityName`: string, `content`: string |
| `create_relations` | Link entities | `relations`: list with from, to, relationType |
| `read_graph` | View entire graph | None |
| `search_nodes` | Find entities | `query`: search string |
| `open_nodes` | Get entity details | `names`: list of entity names |
| `delete_entities` | Remove entities | `entityNames`: list of names |
| `delete_observations` | Remove observations | `deletions`: list with entityName, observations |
| `delete_relations` | Remove relations | `relations`: list with from, to, relationType |

## Best Practices

1. **Always use empty observations when creating entities**: `"observations": []`
2. **Add detailed content separately**: Use `add_observations` after entity creation
3. **Use descriptive entity types**: "Technology", "Concept", "Algorithm", etc.
4. **Use active voice for relations**: "TRAINED_WITH", "DEPENDS_ON", "IMPLEMENTS"
5. **Check entity existence**: Use `search_nodes` to verify entities exist before creating relations

## Error Troubleshooting

- **"No entity found"**: Ensure entity names match exactly (case-sensitive)
- **"Contents array required"**: Use `contents` (plural) with array of strings
- **"Property type error"**: Don't nest objects in observations during entity creation
- **"Transaction scope"**: Tools handle this internally - no action needed

## Migration from Old Format

If you were using:
```json
// OLD - Don't use
{"entityName": "MyEntity", "content": "single string"}
```

Change to:
```json
// NEW - Correct format
{"entityName": "MyEntity", "contents": ["single string"]}
```
