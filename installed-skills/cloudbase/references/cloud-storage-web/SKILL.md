---
name: cloud-storage-web
description: Complete guide for CloudBase cloud storage using Web SDK (@cloudbase/js-sdk) - upload, download, temporary URLs, file management, and best practices.
alwaysApply: false
---

# Cloud Storage Web SDK

Use this skill when building web applications that need to upload, download, or manage files using CloudBase cloud storage via the `@cloudbase/js-sdk` (Web SDK).

## When to use this skill

Use this skill for **file storage operations** in web applications when you need to:

- Upload files from web browsers to CloudBase cloud storage
- Generate temporary download URLs for stored files
- Delete files from cloud storage
- Download files from cloud storage to local browser

**Do NOT use for:**
- Mini-program file operations (use mini-program specific skills)
- Backend file operations (use Node SDK skills)
- Database operations (use database skills)

## How to use this skill (for a coding agent)

1. **Initialize CloudBase SDK**
   - Ask the user for their CloudBase environment ID
   - Always use the standard initialization pattern shown below

2. **Choose the right storage method**
   - `uploadFile` - For uploading files from browser to cloud storage
   - `getTempFileURL` - For generating temporary download links
   - `deleteFile` - For deleting files from storage
   - `downloadFile` - For downloading files to browser

3. **Handle CORS requirements**
   - Remind users to add their domain to CloudBase console security domains
   - This prevents CORS errors during file operations

4. **Follow file path rules**
   - Use valid characters: `[0-9a-zA-Z]`, `/`, `!`, `-`, `_`, `.`, ` `, `*`, Chinese characters
   - Use `/` for folder structure (e.g., `folder/file.jpg`)

---

## SDK Initialization

```javascript
import cloudbase from "@cloudbase/js-sdk";

const app = cloudbase.init({
  env: "your-env-id", // Replace with your CloudBase environment ID
});
```

**Initialization rules:**
- Always use synchronous initialization with the pattern above
- Do not lazy-load the SDK with dynamic imports
- Keep a single shared `app` instance across your application

## File Upload (uploadFile)

### Basic Usage

```javascript
const result = await app.uploadFile({
  cloudPath: "folder/filename.jpg", // File path in cloud storage
  filePath: fileInput.files[0],     // HTML file input element
});

// Result contains:
{
  fileID: "cloud://env-id/folder/filename.jpg", // Unique file identifier
  // ... other metadata
}
```

### Advanced Upload with Progress

```javascript
const result = await app.uploadFile({
  cloudPath: "uploads/avatar.jpg",
  filePath: selectedFile,
  method: "put", // "post" or "put" (default: "put")
  onUploadProgress: (progressEvent) => {
    const percent = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    );
    console.log(`Upload progress: ${percent}%`);
    // Update UI progress bar here
  }
});
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudPath` | string | Yes | Absolute path with filename (e.g., "folder/file.jpg") |
| `filePath` | File | Yes | HTML file input object |
| `method` | "post" \| "put" | No | Upload method (default: "put") |
| `onUploadProgress` | function | No | Progress callback function |

### Cloud Path Rules

- **Valid characters**: `[0-9a-zA-Z]`, `/`, `!`, `-`, `_`, `.`, ` `, `*`, Chinese characters
- **Invalid characters**: Other special characters
- **Structure**: Use `/` to create folder hierarchy
- **Examples**:
  - `"avatar.jpg"`
  - `"uploads/avatar.jpg"`
  - `"user/123/avatar.jpg"`

### CORS Configuration

**⚠️ IMPORTANT:** To prevent CORS errors, add your domain to CloudBase console:

1. Go to CloudBase Console → Environment → Security Sources → Security Domains
2. Add your frontend domain (e.g., `https://your-app.com`, `http://localhost:3000`)
3. If CORS errors occur, remove and re-add the domain

## Temporary Download URLs (getTempFileURL)

### Basic Usage

```javascript
const result = await app.getTempFileURL({
  fileList: [
    {
      fileID: "cloud://env-id/folder/filename.jpg",
      maxAge: 3600 // URL valid for 1 hour (seconds)
    }
  ]
});

// Access the download URL
result.fileList.forEach(file => {
  if (file.code === "SUCCESS") {
    console.log("Download URL:", file.tempFileURL);
    // Use this URL to download or display the file
  }
});
```

### Multiple Files

```javascript
const result = await app.getTempFileURL({
  fileList: [
    {
      fileID: "cloud://env-id/image1.jpg",
      maxAge: 7200 // 2 hours
    },
    {
      fileID: "cloud://env-id/document.pdf",
      maxAge: 86400 // 24 hours
    }
  ]
});
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileList` | Array | Yes | Array of file objects |

#### fileList Item Structure

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileID` | string | Yes | Cloud storage file ID |
| `maxAge` | number | Yes | URL validity period in seconds |

### Response Structure

```javascript
{
  code: "SUCCESS",
  fileList: [
    {
      code: "SUCCESS",
      fileID: "cloud://env-id/folder/filename.jpg",
      tempFileURL: "https://temporary-download-url"
    }
  ]
}
```

### Best Practices

- Set appropriate `maxAge` based on use case (1 hour to 24 hours)
- Handle `SUCCESS`/`ERROR` codes in response
- Use temporary URLs for private file access
- Cache URLs if needed, but respect expiration time

## File Deletion (deleteFile)

### Basic Usage

```javascript
const result = await app.deleteFile({
  fileList: [
    "cloud://env-id/folder/filename.jpg"
  ]
});

// Check deletion results
result.fileList.forEach(file => {
  if (file.code === "SUCCESS") {
    console.log("File deleted:", file.fileID);
  } else {
    console.error("Failed to delete:", file.fileID);
  }
});
```

### Multiple Files

```javascript
const result = await app.deleteFile({
  fileList: [
    "cloud://env-id/old-avatar.jpg",
    "cloud://env-id/temp-upload.jpg",
    "cloud://env-id/cache-file.dat"
  ]
});
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileList` | Array<string> | Yes | Array of file IDs to delete |

### Response Structure

```javascript
{
  fileList: [
    {
      code: "SUCCESS",
      fileID: "cloud://env-id/folder/filename.jpg"
    }
  ]
}
```

### Best Practices

- Always check response codes before assuming deletion success
- Use this for cleanup operations (old avatars, temp files, etc.)
- Consider batching multiple deletions for efficiency

## File Download (downloadFile)

### Basic Usage

```javascript
const result = await app.downloadFile({
  fileID: "cloud://env-id/folder/filename.jpg"
});

// File is downloaded to browser default download location
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileID` | string | Yes | Cloud storage file ID |

### Response Structure

```javascript
{
  // Success response (no specific data returned)
  // File is downloaded to browser
}
```

### Best Practices

- Use for user-initiated downloads (save file dialogs)
- For programmatic file access, use `getTempFileURL` instead
- Handle download errors appropriately

## Error Handling

All storage operations should include proper error handling:

```javascript
try {
  const result = await app.uploadFile({
    cloudPath: "uploads/file.jpg",
    filePath: selectedFile
  });

  if (result.code) {
    // Handle error
    console.error("Upload failed:", result.message);
  } else {
    // Success
    console.log("File uploaded:", result.fileID);
  }
} catch (error) {
  console.error("Storage operation failed:", error);
}
```

### Common Error Codes

- `INVALID_PARAM` - Invalid parameters
- `PERMISSION_DENIED` - Insufficient permissions
- `RESOURCE_NOT_FOUND` - File not found
- `SYS_ERR` - System error


## Best Practices

1. **File Organization**: Use consistent folder structures (`uploads/`, `avatars/`, `documents/`)
2. **Naming Conventions**: Use descriptive filenames with timestamps if needed
3. **Progress Feedback**: Show upload progress for better UX
4. **Cleanup**: Delete temporary/unused files to save storage costs
5. **Security**: Validate file types and sizes before upload
6. **Caching**: Cache download URLs appropriately but respect expiration
7. **Batch Operations**: Use arrays for multiple file operations when possible

## Performance Considerations

1. **File Size Limits**: Be aware of CloudBase file size limits
2. **Concurrent Uploads**: Limit concurrent uploads to prevent browser overload
3. **Progress Monitoring**: Use progress callbacks for large file uploads
4. **Temporary URLs**: Generate URLs only when needed, with appropriate expiration

## Security Considerations

1. **Domain Whitelisting**: Always configure security domains to prevent CORS issues
2. **Access Control**: Use appropriate file permissions (public vs private)
3. **URL Expiration**: Set reasonable expiration times for temporary URLs
4. **User Permissions**: Ensure users can only access their own files when appropriate

