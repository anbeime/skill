# CRUD Operations with CloudBase

This document covers Create, Update, and Delete operations for CloudBase document database.

## Create Operations

### Adding a Single Document

Add a new document to a collection:

```javascript
// Add a single document
// Note: _openid is automatically added by SDK, do not include it in the data
const result = await db.collection('todos').add({
    title: 'Learn CloudBase',
    description: 'Study the database API',
    completed: false,
    priority: 'high',
    createdAt: new Date()
    // _openid is automatically populated from authenticated user session
});

console.log('Added document with ID:', result.id);
```

**Return Value:**
```javascript
{
    id: "generated-doc-id",  // Auto-generated document ID
    // ... other metadata
}
```

### Adding with Custom ID

Specify your own document ID:

```javascript
// Add with custom ID
const result = await db.collection('todos')
    .doc('custom-todo-id')
    .set({
        title: 'Custom ID Todo',
        completed: false,
        createdAt: new Date()
    });
```

**Note:** Use `.set()` with `.doc()` to specify a custom ID. If document exists, it will be overwritten.

### Adding Multiple Documents

Add multiple documents at once:

```javascript
// Batch add documents
const todos = [
    { title: 'Task 1', completed: false },
    { title: 'Task 2', completed: false },
    { title: 'Task 3', completed: true }
];

// Add one by one
for (const todo of todos) {
    await db.collection('todos').add(todo);
}

// Or use Promise.all for parallel insertion
const results = await Promise.all(
    todos.map(todo => db.collection('todos').add(todo))
);

console.log('Added', results.length, 'documents');
```

### Data Validation

Validate data before insertion:

```javascript
function validateTodo(todo) {
    if (!todo.title || todo.title.trim() === '') {
        throw new Error('Title is required');
    }
    if (typeof todo.completed !== 'boolean') {
        throw new Error('Completed must be a boolean');
    }
    return true;
}

async function addTodo(todoData) {
    try {
        validateTodo(todoData);
        
        const result = await db.collection('todos').add({
            ...todoData,
            createdAt: new Date(),
            updatedAt: new Date()
        });
        
        return result;
    } catch (error) {
        console.error('Failed to add todo:', error);
        throw error;
    }
}
```

## Update Operations

### Update by Document ID

Update a specific document by its ID:

```javascript
// Update by ID
// Note: Do not include _openid in update data - it cannot be modified
const result = await db.collection('todos')
    .doc('todo-id-123')
    .update({
        completed: true,
        updatedAt: new Date()
        // _openid cannot be updated and should not be included
    });

console.log('Updated:', result.updated, 'document(s)');
```

**Return Value:**
```javascript
{
    updated: 1,  // Number of documents updated
    // ... other metadata
}
```

### Update with Conditions

Update documents matching specific conditions:

```javascript
// Update all incomplete high-priority todos
const result = await db.collection('todos')
    .where({
        completed: false,
        priority: 'high'
    })
    .update({
        priority: 'urgent',
        updatedAt: new Date()
    });

console.log('Updated', result.updated, 'documents');
```

### Partial Updates

Only update specific fields (other fields remain unchanged):

```javascript
// Only update the title, leave other fields unchanged
// Note: _openid cannot be updated and should not be included
await db.collection('todos')
    .doc('todo-id-123')
    .update({
        title: 'Updated Title'
        // _openid remains unchanged and cannot be modified
    });
```

### Update with Operators

Use update operators for complex updates:

```javascript
const _ = db.command;

// Increment a counter
await db.collection('posts')
    .doc('post-123')
    .update({
        views: _.inc(1)  // Increment views by 1
    });

// Add item to array
await db.collection('todos')
    .doc('todo-123')
    .update({
        tags: _.push(['urgent'])  // Add 'urgent' to tags array
    });

// Remove item from array
await db.collection('todos')
    .doc('todo-123')
    .update({
        tags: _.pull('completed')  // Remove 'completed' from tags
    });

// Multiply a number
await db.collection('products')
    .doc('product-123')
    .update({
        price: _.mul(1.1)  // Increase price by 10%
    });
```

### Common Update Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `_.inc(n)` | Increment by n | `views: _.inc(1)` |
| `_.mul(n)` | Multiply by n | `price: _.mul(1.5)` |
| `_.push(items)` | Add to array | `tags: _.push(['new'])` |
| `_.pull(item)` | Remove from array | `tags: _.pull('old')` |
| `_.set(value)` | Set to value | `status: _.set('active')` |
| `_.remove()` | Remove field | `tempField: _.remove()` |

### Set vs Update

**`.update()`** - Updates only specified fields:
```javascript
// Only updates 'title', other fields remain unchanged
await db.collection('todos')
    .doc('todo-123')
    .update({ title: 'New Title' });
```

**`.set()`** - Replaces entire document:
```javascript
// Replaces entire document, removes unspecified fields
await db.collection('todos')
    .doc('todo-123')
    .set({ title: 'New Title', completed: false });
```

### Batch Updates

Update multiple documents efficiently:

```javascript
// Update all incomplete todos assigned to a user
async function reassignTodos(oldUserId, newUserId) {
    const result = await db.collection('todos')
        .where({
            assigneeId: oldUserId,
            completed: false
        })
        .update({
            assigneeId: newUserId,
            updatedAt: new Date()
        });
    
    return result.updated;
}

const updatedCount = await reassignTodos('user-1', 'user-2');
console.log('Reassigned', updatedCount, 'todos');
```

## Delete Operations

### Delete by Document ID

Delete a specific document:

```javascript
// Delete by ID
const result = await db.collection('todos')
    .doc('todo-id-123')
    .remove();

console.log('Deleted:', result.deleted, 'document(s)');
```

**Return Value:**
```javascript
{
    deleted: 1,  // Number of documents deleted
    // ... other metadata
}
```

### Delete with Conditions

Delete documents matching conditions:

```javascript
// Delete all completed todos older than 30 days
const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);

const result = await db.collection('todos')
    .where({
        completed: true,
        completedAt: db.command.lt(thirtyDaysAgo)
    })
    .remove();

console.log('Deleted', result.deleted, 'old completed todos');
```

### Conditional Delete

Delete only if conditions are met:

```javascript
async function deleteTodoIfOwner(todoId, userId) {
    try {
        const result = await db.collection('todos')
            .where({
                _id: todoId,
                ownerId: userId  // Only delete if user is owner
            })
            .remove();
        
        if (result.deleted === 0) {
            throw new Error('Todo not found or user is not owner');
        }
        
        return true;
    } catch (error) {
        console.error('Delete failed:', error);
        return false;
    }
}
```

### Batch Delete

Delete multiple documents:

```javascript
// Delete all archived items
async function deleteArchived() {
    const result = await db.collection('todos')
        .where({
            status: 'archived'
        })
        .remove();
    
    return result.deleted;
}

const deletedCount = await deleteArchived();
console.log('Deleted', deletedCount, 'archived items');
```

### Soft Delete Pattern

Instead of permanently deleting, mark as deleted:

```javascript
// Soft delete - mark as deleted instead of removing
async function softDeleteTodo(todoId) {
    const result = await db.collection('todos')
        .doc(todoId)
        .update({
            deleted: true,
            deletedAt: new Date()
        });
    
    return result.updated > 0;
}

// Query only non-deleted items
async function getActiveTodos() {
    const result = await db.collection('todos')
        .where({
            deleted: db.command.neq(true)  // or: deleted: false
        })
        .get();
    
    return result.data;
}
```

## Complete CRUD Examples

### Todo Manager

```javascript
class TodoManager {
    constructor(db) {
        this.db = db;
        this.collection = db.collection('todos');
    }
    
    // Create
    async createTodo(title, description, priority = 'medium') {
        const result = await this.collection.add({
            title,
            description,
            priority,
            completed: false,
            createdAt: new Date(),
            updatedAt: new Date()
        });
        return result.id;
    }
    
    // Read (single)
    async getTodo(id) {
        const result = await this.collection.doc(id).get();
        return result.data[0];
    }
    
    // Read (multiple)
    async getTodos(filter = {}) {
        const result = await this.collection
            .where(filter)
            .orderBy('createdAt', 'desc')
            .get();
        return result.data;
    }
    
    // Update
    async updateTodo(id, updates) {
        const result = await this.collection
            .doc(id)
            .update({
                ...updates,
                updatedAt: new Date()
            });
        return result.updated > 0;
    }
    
    // Update status
    async toggleComplete(id) {
        const todo = await this.getTodo(id);
        return this.updateTodo(id, {
            completed: !todo.completed,
            completedAt: !todo.completed ? new Date() : null
        });
    }
    
    // Delete
    async deleteTodo(id) {
        const result = await this.collection.doc(id).remove();
        return result.deleted > 0;
    }
    
    // Batch operations
    async deleteCompleted() {
        const result = await this.collection
            .where({ completed: true })
            .remove();
        return result.deleted;
    }
}

// Usage
const todoManager = new TodoManager(db);

// Create
const todoId = await todoManager.createTodo(
    'Learn CloudBase', 
    'Study the database API', 
    'high'
);

// Read
const todo = await todoManager.getTodo(todoId);
const allTodos = await todoManager.getTodos({ completed: false });

// Update
await todoManager.updateTodo(todoId, { priority: 'urgent' });
await todoManager.toggleComplete(todoId);

// Delete
await todoManager.deleteTodo(todoId);
await todoManager.deleteCompleted();
```

## Error Handling Best Practices

```javascript
async function safeCRUD() {
    try {
        // Create
        const result = await db.collection('todos').add({
            title: 'New Todo'
        });
        
        console.log('Created:', result.id);
        
    } catch (error) {
        if (error.code === 'PERMISSION_DENIED') {
            console.error('No permission to create document');
        } else if (error.code === 'INVALID_PARAM') {
            console.error('Invalid data provided');
        } else {
            console.error('Unexpected error:', error);
        }
        
        throw error;  // Re-throw for caller to handle
    }
}
```

## Transaction Support

For operations requiring atomicity (all succeed or all fail):

```javascript
// Check CloudBase documentation for transaction API
// Transactions ensure data consistency
await db.runTransaction(async transaction => {
    // Read
    const todo = await transaction.collection('todos').doc('id').get();
    
    // Update based on read
    await transaction.collection('todos').doc('id').update({
        views: todo.data.views + 1
    });
});
```

## Best Practices

1. **Always handle errors**: Wrap operations in try-catch
2. **Validate input**: Check data before database operations
3. **Update timestamps**: Track createdAt and updatedAt
4. **Use transactions**: For related operations that must succeed together
5. **Batch operations**: Use batch updates/deletes when possible
6. **Soft deletes**: Consider soft delete for important data
7. **Index fields**: Index frequently queried/updated fields
8. **Limit updates**: Only update changed fields
9. **Configure security rules**: Use `writeSecurityRule` MCP tool to set database permissions before operations. See `./security-rules.md` for details. **Note:** Security rule changes take effect after a few minutes due to caching.
10. **Log operations**: Track important data changes

## Important: `_openid` Field Management

**CRITICAL: Never include `_openid` in write operations**

The `_openid` field is **automatically managed by the CloudBase SDK** and should **never** be included in any write operation data:

- **Automatic Assignment**: When you perform create, update, or set operations through the SDK, the system automatically writes the `_openid` field based on the current authenticated user's identity
- **Do Not Include**: The `_openid` field should **not** appear in any `data` parameter for write operations (`.add()`, `.update()`, `.set()`)
- **Error on Manual Setting**: If you manually include or modify `_openid` in write operations, the operation will **fail with an error**

**Correct Usage:**
```javascript
// Correct: Do not include _openid
await db.collection('todos').add({
    title: 'My Todo',
    completed: false
    // _openid is automatically added by SDK
});

// Wrong: Including _openid will cause an error
await db.collection('todos').add({
    title: 'My Todo',
    completed: false,
    _openid: 'some-id'  // ERROR: Cannot manually set _openid
});
```

**Note:** The `_openid` field is used internally by CloudBase for user identification and permission control. It is automatically populated from the authenticated user's session and cannot be manually overridden.

