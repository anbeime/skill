# Aggregation Queries with CloudBase

This document explains how to perform aggregation operations for data analysis and statistics in CloudBase document database.

## Overview

Aggregation queries allow you to:
- Group data by specific fields
- Calculate statistics (count, sum, average, etc.)
- Transform and reshape data
- Perform complex data analysis

## Basic Aggregation Syntax

```javascript
const result = await db.collection('collectionName')
    .aggregate()
    .group({ /* grouping configuration */ })
    .end();

console.log('Results:', result.list);
```

**Note:** Aggregation queries use `.end()` instead of `.get()`

## Grouping Data

### Simple Grouping with Count

Count documents by a specific field:

```javascript
// Count todos by priority
const result = await db.collection('todos')
    .aggregate()
    .group({
        _id: '$priority',  // Group by priority field
        count: {
            $sum: 1        // Count documents in each group
        }
    })
    .end();

console.log('By priority:', result.list);
// Output: [
//   { _id: 'high', count: 15 },
//   { _id: 'medium', count: 23 },
//   { _id: 'low', count: 8 }
// ]
```

### Field Reference Syntax

Use `$` prefix to reference document fields:
- `$priority` - References the `priority` field
- `$status` - References the `status` field
- `$user.name` - References nested fields

## Aggregation Operators

### Accumulator Operators

| Operator | Description | Usage |
|----------|-------------|-------|
| `$sum` | Sum values | `{ total: { $sum: '$amount' } }` |
| `$avg` | Average values | `{ avgScore: { $avg: '$score' } }` |
| `$min` | Minimum value | `{ minPrice: { $min: '$price' } }` |
| `$max` | Maximum value | `{ maxPrice: { $max: '$price' } }` |
| `$first` | First value | `{ first: { $first: '$date' } }` |
| `$last` | Last value | `{ last: { $last: '$date' } }` |
| `$push` | Array of all values | `{ items: { $push: '$name' } }` |

## Common Aggregation Patterns

### Count by Category

```javascript
// Count users by role
const result = await db.collection('users')
    .aggregate()
    .group({
        _id: '$role',
        count: { $sum: 1 }
    })
    .end();
```

### Sum and Average

```javascript
// Calculate total and average order amount by customer
const result = await db.collection('orders')
    .aggregate()
    .group({
        _id: '$customerId',
        totalAmount: { $sum: '$amount' },
        averageAmount: { $avg: '$amount' },
        orderCount: { $sum: 1 }
    })
    .end();
```

### Find Min and Max

```javascript
// Find price range by product category
const result = await db.collection('products')
    .aggregate()
    .group({
        _id: '$category',
        minPrice: { $min: '$price' },
        maxPrice: { $max: '$price' },
        avgPrice: { $avg: '$price' }
    })
    .end();
```

### Multiple Groups

```javascript
// Group by status and priority
const result = await db.collection('todos')
    .aggregate()
    .group({
        _id: {
            status: '$status',
            priority: '$priority'
        },
        count: { $sum: 1 }
    })
    .end();

// Output: [
//   { _id: { status: 'active', priority: 'high' }, count: 5 },
//   { _id: { status: 'active', priority: 'low' }, count: 3 },
//   { _id: { status: 'completed', priority: 'high' }, count: 10 }
// ]
```

## Pipeline Stages

Aggregation supports multiple stages in a pipeline:

### Match Stage (Filter)

Filter documents before grouping:

```javascript
const result = await db.collection('orders')
    .aggregate()
    .match({
        status: 'completed',
        createdAt: db.command.gte(new Date('2025-01-01'))
    })
    .group({
        _id: '$customerId',
        totalRevenue: { $sum: '$amount' }
    })
    .end();
```

### Sort Stage

Sort the aggregation results:

```javascript
const result = await db.collection('todos')
    .aggregate()
    .group({
        _id: '$assignee',
        taskCount: { $sum: 1 }
    })
    .sort({
        taskCount: -1  // -1 for descending, 1 for ascending
    })
    .end();
```

### Limit Stage

Limit the number of results:

```javascript
// Top 10 customers by order count
const result = await db.collection('orders')
    .aggregate()
    .group({
        _id: '$customerId',
        orderCount: { $sum: 1 }
    })
    .sort({ orderCount: -1 })
    .limit(10)
    .end();
```

### Project Stage

Reshape output documents:

```javascript
const result = await db.collection('users')
    .aggregate()
    .group({
        _id: '$department',
        employeeCount: { $sum: 1 },
        avgSalary: { $avg: '$salary' }
    })
    .project({
        department: '$_id',
        employees: '$employeeCount',
        averageSalary: '$avgSalary',
        _id: 0  // Exclude _id from output
    })
    .end();
```

## Complete Pipeline Example

```javascript
// Comprehensive sales analysis
const salesAnalysis = await db.collection('orders')
    .aggregate()
    // Stage 1: Filter to completed orders in 2025
    .match({
        status: 'completed',
        orderDate: db.command.gte(new Date('2025-01-01'))
    })
    // Stage 2: Group by product category
    .group({
        _id: '$category',
        totalRevenue: { $sum: '$amount' },
        orderCount: { $sum: 1 },
        avgOrderValue: { $avg: '$amount' },
        maxOrder: { $max: '$amount' },
        minOrder: { $min: '$amount' }
    })
    // Stage 3: Sort by revenue descending
    .sort({
        totalRevenue: -1
    })
    // Stage 4: Limit to top 5 categories
    .limit(5)
    // Stage 5: Reshape output
    .project({
        category: '$_id',
        revenue: '$totalRevenue',
        orders: '$orderCount',
        averageValue: '$avgOrderValue',
        range: {
            min: '$minOrder',
            max: '$maxOrder'
        },
        _id: 0
    })
    .end();

console.log('Top 5 categories:', salesAnalysis.list);
```

## Time-based Aggregations

### Group by Date

```javascript
// Count orders by date
const result = await db.collection('orders')
    .aggregate()
    .group({
        _id: {
            year: db.command.aggregate.dateToString({
                format: '%Y',
                date: '$createdAt'
            }),
            month: db.command.aggregate.dateToString({
                format: '%m',
                date: '$createdAt'
            })
        },
        orderCount: { $sum: 1 },
        revenue: { $sum: '$amount' }
    })
    .sort({
        '_id.year': 1,
        '_id.month': 1
    })
    .end();
```

## Array Aggregations

### Working with Array Fields

```javascript
// Unwind array fields for analysis
const result = await db.collection('orders')
    .aggregate()
    .unwind('$items')  // Flatten items array
    .group({
        _id: '$items.productId',
        totalQuantity: { $sum: '$items.quantity' },
        totalRevenue: { $sum: '$items.total' }
    })
    .sort({ totalRevenue: -1 })
    .limit(10)
    .end();
```

## Performance Tips

1. **Use match early**: Filter data before grouping to reduce processing
2. **Index match fields**: Ensure fields used in match stage are indexed
3. **Limit results**: Use limit to reduce data transfer
4. **Avoid large groups**: Very large groups can impact performance
5. **Project only needed fields**: Remove unnecessary fields early

## Common Use Cases

### Dashboard Statistics

```javascript
// Get overview statistics
const stats = await db.collection('todos')
    .aggregate()
    .group({
        _id: null,  // Single group for overall stats
        total: { $sum: 1 },
        completed: {
            $sum: {
                $cond: [{ $eq: ['$status', 'completed'] }, 1, 0]
            }
        },
        active: {
            $sum: {
                $cond: [{ $eq: ['$status', 'active'] }, 1, 0]
            }
        }
    })
    .end();
```

### User Activity Analysis

```javascript
// Analyze user activity
const userActivity = await db.collection('activities')
    .aggregate()
    .match({
        timestamp: db.command.gte(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000))
    })
    .group({
        _id: '$userId',
        actionCount: { $sum: 1 },
        lastAction: { $max: '$timestamp' },
        actions: { $push: '$actionType' }
    })
    .sort({ actionCount: -1 })
    .limit(20)
    .end();
```

## Error Handling

Always handle aggregation errors:

```javascript
try {
    const result = await db.collection('orders')
        .aggregate()
        .group({
            _id: '$category',
            total: { $sum: '$amount' }
        })
        .end();
    
    if (result.list.length === 0) {
        console.log('No data found');
    } else {
        console.log('Aggregation results:', result.list);
    }
} catch (error) {
    console.error('Aggregation failed:', error);
}
```

