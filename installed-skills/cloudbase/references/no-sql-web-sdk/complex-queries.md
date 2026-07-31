# Complex Queries with CloudBase

This document provides detailed guidance on constructing complex queries using CloudBase document database.

## Query Operators

Access operators through `db.command`:

```javascript
const _ = db.command;
```

### Comparison Operators

| Operator | Usage | Description |
|----------|-------|-------------|
| `gt` | `_.gt(value)` | Greater than |
| `gte` | `_.gte(value)` | Greater than or equal |
| `lt` | `_.lt(value)` | Less than |
| `lte` | `_.lte(value)` | Less than or equal |
| `eq` | `_.eq(value)` | Equal to |
| `neq` | `_.neq(value)` | Not equal to |

### Array Operators

| Operator | Usage | Description |
|----------|-------|-------------|
| `in` | `_.in([values])` | Value exists in array |
| `nin` | `_.nin([values])` | Value not in array |

## Building Complex Queries

### Multiple Conditions

Combine multiple conditions in the `where()` object:

```javascript
const result = await db.collection('todos')
    .where({
        // Age greater than 18
        age: _.gt(18),
        // Tags include 'tech' or 'study'
        tags: _.in(['tech', 'study']),
        // Created within last week
        createdAt: _.gte(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000))
    })
    .get();
```

### Sorting Results

Use `orderBy()` to sort results:

```javascript
// Single field sorting
db.collection('posts')
    .orderBy('createdAt', 'desc')
    .get()

// Multiple field sorting (chain multiple orderBy calls)
db.collection('products')
    .orderBy('category', 'asc')
    .orderBy('price', 'desc')
    .get()
```

**Sort directions:**
- `'asc'` - Ascending order
- `'desc'` - Descending order

### Limiting Results

Control the number of results returned:

```javascript
// Limit to 10 results
db.collection('posts')
    .limit(10)
    .get()
```

**Limits:**
- Default: 100 records
- Maximum: 1000 records per query

### Field Selection

Optimize queries by selecting only needed fields:

```javascript
const result = await db.collection('users')
    .field({
        title: true,        // Include title
        completed: true,    // Include completed
        createdAt: true,    // Include createdAt
        _id: false          // Exclude _id
    })
    .get();
```

**Field selection rules:**
- `true` - Include field in results
- `false` - Exclude field from results
- If not specified, all fields are included by default

## Complete Complex Query Example

Here's a comprehensive example combining all query features:

```javascript
const _ = db.command;

const result = await db.collection('todos')
    .where({
        // Status must be 'active' or 'pending'
        status: _.in(['active', 'pending']),
        // Priority is high
        priority: 'high',
        // Age greater than 18
        age: _.gt(18),
        // Created in the last 30 days
        createdAt: _.gte(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000))
    })
    .field({
        title: true,
        status: true,
        priority: true,
        assignee: true,
        createdAt: true
    })
    .orderBy('createdAt', 'desc')
    .orderBy('priority', 'asc')
    .limit(50)
    .skip(0)
    .get();

console.log('Found', result.data.length, 'todos');
console.log('Results:', result.data);
```

## Query Performance Tips

1. **Use Indexes**: Create indexes on frequently queried fields
2. **Limit Fields**: Only select fields you need with `.field()`
3. **Apply Filters Early**: Use specific `where()` conditions to reduce data scanned
4. **Reasonable Limits**: Don't query more data than necessary
5. **Optimize Sort Fields**: Sort on indexed fields when possible

## Common Query Patterns

### Date Range Queries

```javascript
const startDate = new Date('2025-01-01');
const endDate = new Date('2025-12-31');

db.collection('events')
    .where({
        eventDate: _.gte(startDate).and(_.lte(endDate))
    })
    .get()
```

### Text Search (Exact Match)

```javascript
// Exact title match
db.collection('articles')
    .where({
        title: 'Specific Title'
    })
    .get()
```

### Multiple Value Matching

```javascript
// Find users with specific roles
db.collection('users')
    .where({
        role: _.in(['admin', 'moderator', 'editor'])
    })
    .get()
```

### Excluding Values

```javascript
// Find posts not in draft or archived status
db.collection('posts')
    .where({
        status: _.nin(['draft', 'archived'])
    })
    .get()
```

### Combining with Logical Operators

```javascript
// Users over 18 OR with verified status
db.collection('users')
    .where({
        _or: [
            { age: _.gt(18) },
            { verified: true }
        ]
    })
    .get()
```

## Error Handling

Always handle potential errors:

```javascript
try {
    const result = await db.collection('todos')
        .where({ status: _.in(['active']) })
        .orderBy('priority', 'desc')
        .limit(10)
        .get();
    
    if (result.data.length === 0) {
        console.log('No matching documents found');
    } else {
        console.log('Found documents:', result.data);
    }
} catch (error) {
    console.error('Query failed:', error);
    // Handle error appropriately
}
```
