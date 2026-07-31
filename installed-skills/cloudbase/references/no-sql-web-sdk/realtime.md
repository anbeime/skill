# Realtime Database with CloudBase

CloudBase document database supports **real-time push** functionality that allows applications to listen to all update events for documents in a specified collection that match query conditions. When monitored documents undergo any changes (such as addition, modification, deletion), the client receives notifications in real-time, enabling real-time data synchronization and updates.

## Core Features

### Real-time Data Change Monitoring
- Listen to all change events for documents in a collection that match query conditions
- Support for all types of changes: addition, modification, deletion
- Automatically push change snapshots to clients

### Use Cases
- Chat applications
- Real-time collaborative editing
- Live interactive features
- Real-time dashboards
- Multiplayer game state synchronization

## Basic Usage

### 1. Establish Monitoring

Use the `.watch()` method on the collection reference to establish monitoring:

```javascript
// db is the database instance from cloudbase js client sdk 
const watcher = db.collection("todos") // Specify collection
  .where({ // Specify query conditions
    status: 'active',
    priority: _.in(['high', 'medium'])
  })
  .watch({
    onChange: function(snapshot) { // Data change callback
      console.log("Received data snapshot", snapshot);
      // Update your UI or process data here
      handleDataChange(snapshot);
    },
    onError: function(err) { // Error handling callback
      console.error("Monitoring closed due to error", err);
      // Handle errors, such as attempting to re-establish connection
      handleWatchError(err);
    }
  });
```

### 2. Close Monitoring

When you no longer need to monitor data changes, call the `watcher.close()` method:

```javascript
// Close monitoring when page or component unmounts
watcher.close();
```

## API Details

### watch(options)

Create a real-time data listener that returns a `watcher` object.

**Parameters:**
- `options.onChange` (Function): Callback function when data changes
- `options.onError` (Function): Callback function when monitoring encounters an error

**onChange callback parameter snapshot:**
```javascript
{
  docChanges: [
    {
      id: 'document-id',
      dataType: 'init' | 'update' | 'delete' | 'add',
      queueType: 'init' | 'update' | 'delete' | 'enqueue' | 'dequeue',
      doc: { // Document content after change
        // Document fields
      }
    },
    // More changes...
  ],
  docs: [ // All documents in the query result set
    // Document content...
  ]
}
```

**Change types in onChange callback:**
- `init`: Initialization, sends all data when first establishing connection
- `update`: Document content update
- `add`: New document added
- `delete`: Document deleted

**Watcher object methods:**
- `watcher.close()`: Close monitoring and release resources

## Best Practices

### 1. Specific Query Conditions

Set as specific query conditions as possible in the `.where()` method to monitor only the data changes you truly need:

```javascript
// Recommended: Specific query conditions
db.collection("messages")
  .where({
    chatRoomId: currentChatRoomId,
    isDeleted: false
  })
  .watch({...});

// Not recommended: Monitoring entire collection
db.collection("messages").watch({...});
```

### 2. Close Monitoring in a Timely Manner

Be sure to close monitoring when pages or components unmount to prevent memory leaks:

**React Component Example:**
```javascript
import { useEffect } from 'react';

function ChatRoom({ roomId }) {
  useEffect(() => {
    const watcher = db.collection("messages")
      .where({ chatRoomId: roomId })
      .watch({
        onChange: handleNewMessages,
        onError: handleError
      });
    
    // Close monitoring when component unmounts
    return () => {
      watcher.close();
    };
  }, [roomId]);
}
```