# API Design Plan

This document outlines the API endpoints required to support the frontend UI functionalities.

## 1. Records API

### GET /api/records

- **Description**: Fetches a list of sleep records for a specific date.
- **Query Parameters**:
  - `date` (string, YYYY-MM-DD): The date to retrieve records for.
- **Response Body**:
  ```json
  [
    {
      "id": "string",
      "timestamp": "string (ISO 8601)",
      "duration": "float",
      "audioUrl": "string",
      "transcription": "string",
      "confidence": "float",
      "isFavorite": "boolean",
      "tags": ["string"]
    }
  ]
  ```

### PATCH /api/records/{record_id}

- **Description**: Updates a specific record. Currently used for marking as favorite.
- **Path Parameters**:
  - `record_id` (string): The ID of the record to update.
- **Request Body**:
  ```json
  {
    "isFavorite": "boolean"
  }
  ```
- **Response Body**: The updated record object.

## 2. Statistics API

### GET /api/stats/monthly-activity

- **Description**: Fetches the count of records for each day in a given month.
- **Query Parameters**:
  - `year` (integer): The year.
  - `month` (integer): The month (1-12).
- **Response Body**:
  ```json
  {
    "YYYY-MM-DD": "integer",
    "YYYY-MM-DD": "integer"
  }
  ```

### GET /api/stats

- **Description**: Fetches aggregated statistics over a date range.
- **Query Parameters**:
  - `startDate` (string, YYYY-MM-DD)
  - `endDate` (string, YYYY-MM-DD)
- **Response Body**:
  ```json
  {
    "dailyStats": [
      { "date": "YYYY-MM-DD", "count": "integer", "avgDuration": "float" }
    ],
    "hourlyStats": [
      { "hour": "HH:00", "count": "integer" }
    ],
    "tagStats": [
      { "name": "string", "value": "integer" }
    ],
    "keywordData": [
      { "text": "string", "value": "integer", "category": "string" }
    ]
  }
  ```

## 3. Static Files

### GET /audio/{filename}

- **Description**: Serves the audio files. The `audio_url` in the record object will point to this endpoint.
- **Path Parameters**:
  - `filename` (string): The name of the audio file.