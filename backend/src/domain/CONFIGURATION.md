# Domain Configuration System

## Overview

All hard-coded values have been moved to a centralized configuration system located in `src/domain/config/`. This follows the principle of having configuration in one place and makes the system more maintainable.

## Configuration Structure

### `DOMAIN_CONFIG` - Central Configuration Object

```python
from src.domain.config import DOMAIN_CONFIG

# Access configuration values
max_file_size = DOMAIN_CONFIG.file_constraints.MAX_FILE_SIZE_BYTES
free_user_quota = DOMAIN_CONFIG.user_quotas.FREE_USER_QUOTA
```

## Configuration Categories

### 1. User Quotas (`user_quotas`)
- `FREE_USER_QUOTA`: 50 images
- `PAID_USER_QUOTA`: 1000 images  
- `ADMIN_USER_QUOTA`: 1000 images

### 2. File Constraints (`file_constraints`)
- `MAX_FILE_SIZE_BYTES`: 20MB (20 * 1024 * 1024)
- `MAX_IMAGE_SIZE_FOR_PROCESSING`: 10MB (10 * 1024 * 1024)
- `THUMBNAIL_WIDTH`: 400 pixels
- `THUMBNAIL_HEIGHT`: 240 pixels

### 3. Data Retention (`data_retention`)
- `INACTIVE_FREE_USER_THRESHOLD_DAYS`: 30 days
- `TEMP_FILE_RETENTION_HOURS`: 24 hours

### 4. Search Configuration (`search`)
- `DEFAULT_SEARCH_LIMIT`: 20 results
- `MAX_SEARCH_LIMIT`: 100 results
- `MAX_EXTRACTED_TEXT_SNIPPET_LENGTH`: 200 characters

### 5. Processing Configuration (`processing`)
- `S3_DELETE_BATCH_SIZE`: 1000 (S3 delete batch limit)
- `DEFAULT_PROCESSING_TIMEOUT_MINUTES`: 2 minutes

## Usage Examples

### In Use Cases
```python
from ..config import DOMAIN_CONFIG

class UploadReceiptUseCase:
    async def execute(self, request):
        # Use configuration instead of hard-coded values
        if file_size > DOMAIN_CONFIG.file_constraints.MAX_FILE_SIZE_BYTES:
            max_size_mb = DOMAIN_CONFIG.file_constraints.MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise ValidationError(f"File too large (max {max_size_mb}MB)")
```

### In Entities
```python
from ..config import DOMAIN_CONFIG

class UserRole(Enum):
    @property
    def image_quota(self) -> int:
        if self == UserRole.FREE:
            return DOMAIN_CONFIG.user_quotas.FREE_USER_QUOTA
        # ...
```

## Benefits

1. **Single Source of Truth**: All configuration values in one place
2. **Easy Maintenance**: Change values without hunting through code
3. **Type Safety**: Configuration values are typed and validated
4. **Immutable**: Uses `@dataclass(frozen=True)` to prevent accidental changes
5. **Clear Documentation**: Self-documenting configuration structure
6. **Environment-Specific**: Can be extended for different environments

## Extending Configuration

To add new configuration values:

1. Add to appropriate configuration dataclass in `config/__init__.py`
2. Update the `DomainConfig` class if needed
3. Import and use `DOMAIN_CONFIG` in your code
4. Update this documentation

## Configuration Override (Future)

The configuration system can be extended to support environment-specific overrides:

```python
# Future enhancement
DOMAIN_CONFIG = DomainConfig.from_environment()
```

This centralized approach makes the domain layer more maintainable and follows clean architecture principles by keeping configuration separate from business logic.
