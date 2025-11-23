# Krista Infinispan

Python package with Infinispan integration for Krista infrastructure. This package provides simple and robust cache operations with automatic serialization, retry logic, and ProtoStream support.

## Installation

### From PyPI
```bash
pip install krista-infinispan
```


## Configuration

### cache_config.json

The package uses a `cache_config.json` file for Infinispan connection settings. This file should be placed in your project root or specified via environment variables.

**Example cache_config.json:**
```json
{
  "host": "localhost",
  "port": 11222,
  "username": "admin",
  "password": "admin",
  "caches": {
    "default": {
      "enabled": true,
      "memory_size": "50MB",
      "ttl_hours": 2,
      "l1_size": "5MB",
      "l1_expiration_minutes": 30,
      "description": "Default cache configuration",
      "locking": {
        "isolation": "READ_COMMITTED",
        "acquire_timeout": 15000,
        "concurrency_level": 1000,
        "striping": false
      },
      "transaction": {
        "mode": "NON_XA",
        "locking": "OPTIMISTIC",
        "auto_commit": true,
        "recovery_enabled": false
      },
      "encoding": {
        "key": {
          "media_type": "application/x-protostream"
        },
        "value": {
          "media_type": "application/x-protostream"
        }
      },
      "persistence": {
        "enabled": true,
        "type": "file-store",
        "path": "cache-data-default",
        "passivation": false,
        "write_behind": {
          "enabled": true,
          "modification_queue_size": 2048,
          "fail_silently": false
        }
      }
    },
    "user-sessions": {
      "enabled": true,
      "memory_size": "100MB",
      "ttl_hours": 24,
      "l1_size": "10MB",
      "l1_expiration_minutes": 60,
      "description": "User session cache with longer TTL",
      "locking": {
        "isolation": "REPEATABLE_READ",
        "acquire_timeout": 10000
      },
      "persistence": {
        "enabled": false
      }
    }
  }
}
```

**Configuration Parameters:**

### Server Connection
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | string | `localhost` | Infinispan server hostname |
| `port` | integer | `11222` | Infinispan server port |
| `username` | string | `admin` | Authentication username |
| `password` | string | `admin` | Authentication password |

### Cache Configuration
Each cache in the `caches` object supports these parameters:

#### Basic Settings
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable the cache |
| `memory_size` | string | `50MB` | Maximum memory size (e.g., "100MB", "1GB") |
| `ttl_hours` | integer | `2` | Time-to-live in hours |
| `l1_size` | string | `5MB` | L1 cache size for clustering |
| `l1_expiration_minutes` | integer | `30` | L1 cache expiration time |
| `description` | string | - | Human-readable cache description |

#### Locking Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `locking.isolation` | string | `READ_COMMITTED` | Isolation level (READ_COMMITTED, REPEATABLE_READ, SERIALIZABLE) |
| `locking.acquire_timeout` | integer | `15000` | Lock acquisition timeout in milliseconds |
| `locking.concurrency_level` | integer | `1000` | Expected concurrent threads |
| `locking.striping` | boolean | `false` | Enable lock striping |

#### Transaction Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transaction.mode` | string | `NON_XA` | Transaction mode (NON_XA, NON_DURABLE_XA, FULL_XA) |
| `transaction.locking` | string | `OPTIMISTIC` | Locking mode (OPTIMISTIC, PESSIMISTIC) |
| `transaction.auto_commit` | boolean | `true` | Enable auto-commit |
| `transaction.recovery_enabled` | boolean | `false` | Enable transaction recovery |

#### Encoding Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `encoding.key.media_type` | string | `application/x-protostream` | Key encoding format |
| `encoding.value.media_type` | string | `application/x-protostream` | Value encoding format |

#### Persistence Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `persistence.enabled` | boolean | `true` | Enable persistence |
| `persistence.type` | string | `file-store` | Store type (file-store, jdbc-store, etc.) |
| `persistence.path` | string | - | File store path |
| `persistence.passivation` | boolean | `false` | Enable passivation |
| `persistence.write_behind.enabled` | boolean | `true` | Enable write-behind |
| `persistence.write_behind.modification_queue_size` | integer | `2048` | Write-behind queue size |
| `persistence.write_behind.fail_silently` | boolean | `false` | Fail silently on write errors |

### Environment Variables

You can override configuration using environment variables:

```bash
export INFINISPAN_HOST=prod-server.example.com
export INFINISPAN_PORT=11222
export INFINISPAN_USERNAME=myuser
export INFINISPAN_PASSWORD=mypassword
export INFINISPAN_CACHE_NAME=production-cache
```

## Usage

### Basic Cache Operations

```python
from krista_infinispan import CacheOperations

# Initialize with default config
cache = CacheOperations()

# Or with custom config file
cache = CacheOperations(config_file="custom_config.json")

# Put data into cache
cache.put("user:123", {"name": "John", "age": 30})

# Get data from cache
user_data = cache.get("user:123")
print(user_data)  # {"name": "John", "age": 30}

# Check if key exists
if cache.exists("user:123"):
    print("User exists in cache")

# Delete from cache
cache.delete("user:123")
```

### Advanced Configuration

```python
from krista_infinispan import CacheOperations, CacheConfig

# Custom configuration
config = CacheConfig(
    host="cluster.example.com",
    port=11222,
    username="myapp",
    password="secret123",
    cache_name="user-sessions"
)

# Initialize with retry settings
cache = CacheOperations(
    config=config,
    max_retries=5,
    initial_retry_delay=2.0,
    retry_backoff_multiplier=2.0,
    max_retry_delay=60.0
)
```

### Data Serialization

The package automatically handles data serialization using a two-step process:

1. **Encoding**: Python objects → JSON → Base64
2. **ProtoStream Wrapping**: Base64 data → ProtoStream envelope

```python
# All Python data types are supported
cache.put("string_key", "Hello World")
cache.put("dict_key", {"users": [1, 2, 3], "active": True})
cache.put("list_key", [1, 2, 3, 4, 5])
cache.put("number_key", 42)

# Data is automatically serialized and deserialized
data = cache.get("dict_key")
print(type(data))  # <class 'dict'>
```

### Error Handling and Retry Logic

The package includes built-in retry logic for network failures:

```python
cache = CacheOperations(
    max_retries=3,              # Retry up to 3 times
    initial_retry_delay=1.0,    # Start with 1 second delay
    retry_backoff_multiplier=2.0, # Double delay each retry
    max_retry_delay=30.0        # Cap delay at 30 seconds
)

try:
    cache.put("key", "value")
except Exception as e:
    print(f"Failed after retries: {e}")
```

### Cache Management

```python
# Ensure cache exists before operations
cache.ensure_cache_exists()

# Get cache statistics
stats = cache.get_cache_stats()

# Clear entire cache
cache.clear_cache()

# Get all keys
keys = cache.get_all_keys()
```

### Cache Creation with Advanced Parameters

```python
from krista_infinispan import CacheCreator, CacheOperations

# Create cache creator
creator = CacheCreator()

# Create cache with custom configuration
cache_config = {
    "memory_size": "200MB",
    "ttl_hours": 6,
    "l1_size": "20MB",
    "l1_expiration_minutes": 120,
    "locking": {
        "isolation": "REPEATABLE_READ",
        "acquire_timeout": 20000,
        "concurrency_level": 2000
    },
    "transaction": {
        "mode": "FULL_XA",
        "locking": "PESSIMISTIC",
        "recovery_enabled": true
    },
    "encoding": {
        "key": {"media_type": "application/x-protostream"},
        "value": {"media_type": "application/x-protostream"}
    },
    "persistence": {
        "enabled": true,
        "type": "file-store",
        "path": "my-custom-cache",
        "write_behind": {
            "enabled": true,
            "modification_queue_size": 4096
        }
    }
}

# Create the cache
success = creator.create_cache("my-custom-cache", cache_config)

# Use the cache
cache = CacheOperations(cache_name="my-custom-cache")
cache.put("key", "value")
```

### Multiple Cache Configurations

```python
# Different caches for different use cases
cache_configs = {
    "user-sessions": {
        "memory_size": "500MB",
        "ttl_hours": 24,
        "persistence": {"enabled": false},  # In-memory only
        "locking": {"isolation": "READ_COMMITTED"}
    },
    "product-catalog": {
        "memory_size": "1GB", 
        "ttl_hours": 168,  # 1 week
        "persistence": {
            "enabled": true,
            "type": "file-store",
            "path": "product-data"
        },
        "transaction": {"mode": "FULL_XA"}
    },
    "temp-data": {
        "memory_size": "100MB",
        "ttl_hours": 1,  # Short-lived
        "persistence": {"enabled": false}
    }
}
```

## ProtoStream Integration

The package uses ProtoStream format for Infinispan compatibility:

**Internal ProtoStream Format:**
```json
{
  "_type": "cache.CacheEntry",
  "value": "base64-encoded-json-data"
}
```

This ensures compatibility with Infinispan's ProtoStream serialization while maintaining Python object fidelity.

## Authentication

The package supports HTTP Digest Authentication:

```json
{
  "username": "your-username",
  "password": "your-password"
}
```

For production environments, consider using:
- Environment variables for credentials
- Encrypted configuration files
- Secret management systems

## SSL/TLS Configuration

For secure connections:

```json
{
  "protocol": "https",
  "port": 11443,
  "ssl_enabled": true,
  "ssl_verify": true
}
```

To disable SSL verification (not recommended for production):

```json
{
  "ssl_verify": false
}
```

## Logging

The package uses Python's standard logging. Configure logging in your application:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('krista_infinispan')
logger.setLevel(logging.INFO)
```

## Error Handling

Common exceptions and how to handle them:

```python
from krista_infinispan import CacheOperations
from requests.exceptions import ConnectionError, Timeout

cache = CacheOperations()

try:
    cache.put("key", "value")
except ConnectionError:
    print("Cannot connect to Infinispan server")
except Timeout:
    print("Request timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

1. **Connection Pooling**: Configure appropriate `connection_pool_size`
2. **Timeouts**: Set reasonable timeout values
3. **Retry Logic**: Tune retry parameters for your network conditions
4. **Batch Operations**: Use bulk operations when available

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see [LICENSE](../LICENSE) file for details.
