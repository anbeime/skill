# Geolocation Queries with CloudBase

This document explains how to work with geographic data and perform location-based queries in CloudBase.

## Prerequisites

**⚠️ CRITICAL**: Before performing any geolocation queries, you **MUST** create a geolocation index on the field you're querying. Queries will fail without proper indexing.

## Geographic Data Types

CloudBase supports several geographic data types through `db.Geo`:

```javascript
const db = app.database();
```

### Point (Single Location)

Represents a single geographic coordinate:

```javascript
// Create a Point: longitude, latitude
const point = new db.Geo.Point(116.404, 39.915);  // Tiananmen Square coordinates
```

**Note:** Coordinates are in `[longitude, latitude]` format (NOT latitude, longitude).

### LineString (Path/Route)

Represents a path or route:

```javascript
// Create a LineString (array of Points)
const line = new db.Geo.LineString([
    new db.Geo.Point(116.404, 39.915),  // Start
    new db.Geo.Point(116.405, 39.916),  // Waypoint
    new db.Geo.Point(116.406, 39.917)   // End
]);
```

### Polygon (Area)

Represents an enclosed area:

```javascript
// Create a Polygon (array of LineStrings, first is outer boundary)
const polygon = new db.Geo.Polygon([
    new db.Geo.LineString([
        new db.Geo.Point(116.404, 39.915),
        new db.Geo.Point(116.404, 39.916),
        new db.Geo.Point(116.405, 39.916),
        new db.Geo.Point(116.405, 39.915),
        new db.Geo.Point(116.404, 39.915)   // Must close the polygon
    ])
]);
```

**Note:** The first and last points must be identical to close the polygon.

## Storing Geographic Data

Store location data in documents:

```javascript
// Add a user with location
await db.collection('users').add({
    name: 'John',
    location: new db.Geo.Point(116.404, 39.915),
    address: 'Beijing, China'
});

// Add a delivery route
await db.collection('routes').add({
    name: 'Route A',
    path: new db.Geo.LineString([
        new db.Geo.Point(116.404, 39.915),
        new db.Geo.Point(116.405, 39.916),
        new db.Geo.Point(116.406, 39.917)
    ])
});

// Add a service area
await db.collection('serviceAreas').add({
    name: 'Downtown',
    area: new db.Geo.Polygon([
        new db.Geo.LineString([
            new db.Geo.Point(116.404, 39.915),
            new db.Geo.Point(116.404, 39.916),
            new db.Geo.Point(116.405, 39.916),
            new db.Geo.Point(116.405, 39.915),
            new db.Geo.Point(116.404, 39.915)
        ])
    ])
});
```

## Geolocation Query Operators

CloudBase provides three main geolocation query operators:

### 1. geoNear (Proximity Search)

Find documents near a specific location, ordered by distance:

```javascript
const _ = db.command;

// Find users within 1000 meters of a location
const result = await db.collection('users').where({
    location: _.geoNear({
        geometry: new db.Geo.Point(116.404, 39.915),  // Center point
        maxDistance: 1000,   // Maximum distance in meters
        minDistance: 0       // Minimum distance in meters
    })
}).get();

console.log('Nearby users:', result.data);
```

**Parameters:**
- `geometry` - Center point (Point object)
- `maxDistance` - Maximum distance in meters (optional)
- `minDistance` - Minimum distance in meters (optional, default: 0)

**Important:** Results are automatically sorted by distance (closest first).

### 2. geoWithin (Area Search)

Find documents within a specific geographic area:

```javascript
const _ = db.command;

// Define search area
const searchArea = new db.Geo.Polygon([
    new db.Geo.LineString([
        new db.Geo.Point(116.404, 39.915),
        new db.Geo.Point(116.404, 39.920),
        new db.Geo.Point(116.410, 39.920),
        new db.Geo.Point(116.410, 39.915),
        new db.Geo.Point(116.404, 39.915)
    ])
]);

// Find users in the area
const result = await db.collection('users').where({
    location: _.geoWithin({
        geometry: searchArea
    })
}).get();
```

**Use Cases:**
- Find all stores in a neighborhood
- Users within a city boundary
- Deliveries in a service area

### 3. geoIntersects (Intersection Search)

Find documents that intersect with a specific geometry:

```javascript
const _ = db.command;

// Define a path/route
const deliveryRoute = new db.Geo.LineString([
    new db.Geo.Point(116.404, 39.915),
    new db.Geo.Point(116.410, 39.920)
]);

// Find service areas that intersect with the route
const result = await db.collection('serviceAreas').where({
    area: _.geoIntersects({
        geometry: deliveryRoute
    })
}).get();
```

**Use Cases:**
- Routes crossing service areas
- Overlapping geographic regions
- Path planning

## Complete Examples

### Nearby Search App

```javascript
async function findNearbyPlaces(userLat, userLon, radius = 5000, category = null) {
    const _ = db.command;
    const userLocation = new db.Geo.Point(userLon, userLat);
    
    let whereCondition = {
        location: _.geoNear({
            geometry: userLocation,
            maxDistance: radius
        })
    };
    
    // Add category filter if specified
    if (category) {
        whereCondition.category = category;
    }
    
    try {
        const result = await db.collection('places')
            .where(whereCondition)
            .limit(20)
            .get();
        
        return result.data;
    } catch (error) {
        console.error('Nearby search failed:', error);
        throw error;
    }
}

// Usage
const nearbyRestaurants = await findNearbyPlaces(39.915, 116.404, 2000, 'restaurant');
console.log('Found', nearbyRestaurants.length, 'restaurants nearby');
```

### Delivery Zone Checker

```javascript
async function isInDeliveryZone(userLat, userLon, storeId) {
    const _ = db.command;
    const userLocation = new db.Geo.Point(userLon, userLat);
    
    try {
        // Get store's delivery zone
        const store = await db.collection('stores')
            .doc(storeId)
            .get();
        
        if (!store.data || !store.data.deliveryZone) {
            return false;
        }
        
        // Check if user location is within delivery zone
        const result = await db.collection('stores')
            .where({
                _id: storeId,
                deliveryZone: _.geoWithin({
                    geometry: new db.Geo.Point(userLon, userLat)
                })
            })
            .get();
        
        return result.data.length > 0;
    } catch (error) {
        console.error('Zone check failed:', error);
        return false;
    }
}

// Usage
const canDeliver = await isInDeliveryZone(39.915, 116.404, 'store-123');
console.log('Can deliver:', canDeliver);
```

### Distance-based Pricing

```javascript
async function calculateDeliveryFee(userLat, userLon, storeId) {
    const _ = db.command;
    
    try {
        // Get store location
        const store = await db.collection('stores')
            .doc(storeId)
            .get();
        
        if (!store.data || !store.data.location) {
            throw new Error('Store location not found');
        }
        
        const userLocation = new db.Geo.Point(userLon, userLat);
        
        // Find the store with distance
        const result = await db.collection('stores')
            .where({
                _id: storeId,
                location: _.geoNear({
                    geometry: userLocation,
                    maxDistance: 20000  // 20km max
                })
            })
            .get();
        
        if (result.data.length === 0) {
            throw new Error('Location outside delivery range');
        }
        
        // Calculate fee based on distance
        // Note: CloudBase returns distance in results
        const distance = result.data[0].distance || 0;
        const baseFee = 5;
        const perKmFee = 2;
        const deliveryFee = baseFee + (distance / 1000) * perKmFee;
        
        return {
            distance: Math.round(distance),
            fee: Math.round(deliveryFee * 100) / 100
        };
    } catch (error) {
        console.error('Fee calculation failed:', error);
        throw error;
    }
}

// Usage
const delivery = await calculateDeliveryFee(39.915, 116.404, 'store-123');
console.log(`Distance: ${delivery.distance}m, Fee: $${delivery.fee}`);
```

## Creating Geolocation Indexes

**This is required before querying!**

You need to create an index through the CloudBase console:

1. Go to your CloudBase console
2. Navigate to Database → Your Collection
3. Go to Indexes tab
4. Create a new index:
   - Field: `location` (or your geo field name)
   - Type: `geo` or `2dsphere`

Without this index, geolocation queries will fail with an error.

## Best Practices

1. **Always Create Indexes**: Geolocation queries require proper indexes
2. **Coordinate Order**: Use [longitude, latitude], not [latitude, longitude]
3. **Close Polygons**: First and last points in polygon must be identical
4. **Distance Units**: All distances are in meters
5. **Limit Results**: Use `.limit()` for large datasets
6. **Error Handling**: Always wrap geo queries in try-catch
7. **Validate Coordinates**: Ensure latitude is -90 to 90, longitude is -180 to 180
8. **Combine Filters**: Mix geo queries with other conditions when needed

## Common Pitfalls

### Wrong Coordinate Order
```javascript
// ❌ WRONG - latitude first
new db.Geo.Point(39.915, 116.404)

// ✅ CORRECT - longitude first
new db.Geo.Point(116.404, 39.915)
```

### Unclosed Polygon
```javascript
// ❌ WRONG - not closed
new db.Geo.LineString([
    new db.Geo.Point(116.404, 39.915),
    new db.Geo.Point(116.405, 39.916),
    new db.Geo.Point(116.405, 39.915)
])

// ✅ CORRECT - first equals last
new db.Geo.LineString([
    new db.Geo.Point(116.404, 39.915),
    new db.Geo.Point(116.405, 39.916),
    new db.Geo.Point(116.405, 39.915),
    new db.Geo.Point(116.404, 39.915)  // Closes polygon
])
```

### Missing Index
```javascript
// ❌ Will fail without geo index
await db.collection('users').where({
    location: _.geoNear({ geometry: point })
}).get()

// ✅ Create index first in console, then query
```

## Performance Considerations

1. **Index Size**: Geolocation indexes can be large; monitor storage
2. **Query Radius**: Smaller radius queries are faster
3. **Result Limits**: Always use `.limit()` to prevent large result sets
4. **Combine Conditions**: Filter by category/type first, then location
5. **Cache Results**: Cache frequently accessed location data

## React Example Component

```javascript
import { useState, useEffect } from 'react';

function NearbyPlaces({ userLat, userLon }) {
    const [places, setPlaces] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        loadNearbyPlaces();
    }, [userLat, userLon]);
    
    async function loadNearbyPlaces() {
        setLoading(true);
        try {
            const _ = db.command;
            const result = await db.collection('places')
                .where({
                    location: _.geoNear({
                        geometry: new db.Geo.Point(userLon, userLat),
                        maxDistance: 5000
                    })
                })
                .limit(10)
                .get();
            
            setPlaces(result.data);
        } catch (error) {
            console.error('Failed to load places:', error);
        } finally {
            setLoading(false);
        }
    }
    
    if (loading) return <div>Loading nearby places...</div>;
    
    return (
        <div>
            <h2>Nearby Places</h2>
            <ul>
                {places.map(place => (
                    <li key={place._id}>
                        {place.name} - {Math.round(place.distance)}m away
                    </li>
                ))}
            </ul>
        </div>
    );
}
```

