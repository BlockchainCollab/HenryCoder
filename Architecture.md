# HenryCoder Architecture

HenryCoder is a web application that translates smart contracts from EVM (Ethereum Virtual Machine) to Ralph (Alephium blockchain language). This document outlines the architecture and implementation plan for the application.

## System Overview

The application consists of two main components:
- A Nuxt.js frontend (single page application)
- A Python backend API

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │
│   Nuxt.js      │────▶│   Python       │────▶│   Translation  │
│   Frontend     │◀────│   Backend      │◀────│   Engine       │
│                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘
```

## Frontend (Nuxt.js)

### Components
- **Contract Upload/Input**: Interface for uploading or pasting EVM smart contracts
- **Translation Options**: Configuration settings for the translation process
- **Result Display**: Syntax-highlighted view of the translated Ralph code
- **Error Display**: Clear presentation of translation errors or warnings
- **Download Option**: Functionality to download the translated code

### Technologies
- Nuxt.js 3.x (Vue.js 3)
- TypeScript
- Tailwind CSS for styling
- Highlight.js or Prism for code syntax highlighting
- Axios for API communication

## Backend (Python)

### Components
- **API Server**: FastAPI-based REST API
- **Translation Engine**: Core logic for transforming EVM code to Ralph
- **Validation Service**: Validates input contracts and translated output
- **Error Handling**: Structured error reporting

### Technologies
- Python 3.12+
- FastAPI for API framework
- Custom Ralph code generator
- Docker for containerization

## Translation Process

1. **Parsing**: EVM contract (typically Solidity) is parsed by an LLM
2. **Analysis**: AST is analyzed to understand contract structure, functions, and state variables
3. **Mapping**: EVM constructs are mapped to Ralph equivalents
4. **Code Generation**: Ralph code is generated based on the mapping
5. **Validation**: Generated Ralph code is validated for syntax and semantic correctness

## API Endpoints

### POST /api/translate
Translates an EVM contract to Ralph

**Request Body**:
```json
{
  "source_code": "string",
  "options": {
    "optimize": boolean,
    "include_comments": boolean
    ...
  }
}
```

**Response**:
```json
{
  "translated_code": "string",
  "warnings": ["string"],
  "errors": ["string"]
}
```

### GET /api/health
Health check endpoint

**Response**:
```json
{
  "status": "ok",
  "version": "string"
}
```

**cURL Examples**:
```bash
# HTTP
curl http://127.0.0.1:8000/api/health

# HTTPS with SSL certificate check ignored (use -k flag for self-signed certificates)
curl -k https://127.0.0.1:8000/api/health
```

### Example Usage with cURL

**Testing the translation endpoint**:
```bash
# HTTP
curl -X POST http://127.0.0.1:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "pragma solidity ^0.8.0;\ncontract SimpleStorage {\n    uint256 public storedData;\n    function set(uint256 x) public {\n        storedData = x;\n    }\n}",
    "options": {
      "optimize": false,
      "include_comments": true
    }
  }'

# HTTPS with SSL certificate check ignored (use -k flag for self-signed certificates)
curl -k -X POST https://127.0.0.1:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "pragma solidity ^0.8.0;\ncontract SimpleStorage {\n    uint256 public storedData;\n    function set(uint256 x) public {\n        storedData = x;\n    }\n}",
    "options": {
      "optimize": false,
      "include_comments": true
    }
  }'
```

**Note**: The `-k` (or `--insecure`) flag tells cURL to ignore SSL certificate verification. This is useful for development/testing with self-signed certificates but should not be used in production environments.

## Data Flow

1. User uploads or inputs EVM contract on the frontend
2. Frontend sends contract to backend API via HTTP POST
3. Backend parses and translates the contract
4. Translation result is returned to frontend
5. Frontend displays the translated Ralph code
6. User can review, edit, and download the translated code

## Implementation Plan

### Phase 1: Project Setup
1. Setup frontend Nuxt.js project
   - Initialize project with TypeScript
   - Configure Tailwind CSS
   - Set up project structure

2. Setup backend Python project
   - Create FastAPI application
   - Configure Docker
   - Set up testing framework

### Phase 2: Core Components
1. Develop basic frontend UI
   - Create upload/input component
   - Implement basic result display

2. Develop basic backend API
   - Implement health check endpoint
   - Create basic translation endpoint stub

### Phase 3: Translation Engine
1. Develop Ralph code generator
   - Implement basic type mapping
   - Implement function translation
   - Implement state variable handling

### Phase 4: Integration and Refinement
1. Connect frontend and backend
2. Implement error handling and validation
3. Add advanced translation options
4. Improve UI/UX

### Phase 5: Testing and Deployment
1. Unit testing for frontend and backend components
2. Integration testing of the full system
3. Setup CI/CD pipeline
4. Deploy to production environment

## Deployment Architecture

```
                ┌─────────────┐
                │   NGINX     │
                │   Reverse   │
                │   Proxy     │
                └──────┬──────┘
                       │
       ┌───────────────┴───────────────┐
       │                               │
┌──────▼─────┐                ┌────────▼─────┐
│            │                │              │
│  Frontend  │                │  Backend     │
│  Container │                │  Container   │
│            │                │              │
└────────────┘                └──────────────┘
```

1. Frontend and backend will be containerized using Docker
2. NGINX will serve as a reverse proxy
3. Can be deployed on cloud providers (AWS, GCP, Azure) or VPS

## Development Requirements

### Frontend Development
- Node.js 16+
- npm or yarn
- VS Code with Vue/TypeScript extensions

### Backend Development
- Python 3.12+
- Docker
- Venv for virtual environment management
- FastAPI and required libraries installed via pip

## Future Enhancements
- User authentication for saving translations
- Support for batch processing of multiple contracts
- Integration with blockchain explorers for direct import of contracts
- Advanced optimization options for generated Ralph code
- In-browser testing of translated contracts
