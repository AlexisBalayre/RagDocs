---
title: Configuration
weight: 160
aliases:
  - ../configuration
  - /guides/configuration/
---

# Configuration

Qdrant ships with sensible defaults for collection and network settings that are suitable for most use cases. You can view these defaults in the [Qdrant source](https://github.com/qdrant/qdrant/blob/master/config/config.yaml). If you need to customize the settings, you can do so using configuration files and environment variables.

<aside role="status">
  Qdrant Cloud does not allow modifying the Qdrant configuration.
</aside>

## Configuration Files

To customize Qdrant, you can mount your configuration file in any of the following locations. This guide uses `.yaml` files, but Qdrant also supports other formats such as `.toml`, `.json`, and `.ini`.

1. **Main Configuration: `qdrant/config/config.yaml`**

   Mount your custom `config.yaml` file to override default settings:

   ```bash
   docker run -p 6333:6333 \
       -v $(pwd)/config.yaml:/qdrant/config/config.yaml \
       qdrant/qdrant
   ```

2. **Environment-Specific Configuration: `config/{RUN_MODE}.yaml`**

   Qdrant looks for an environment-specific configuration file based on the `RUN_MODE` variable. By default, the [official Docker image](https://hub.docker.com/r/qdrant/qdrant) uses `RUN_MODE=production`, meaning it will look for `config/production.yaml`.

   You can override this by setting `RUN_MODE` to another value (e.g., `dev`), and providing the corresponding file:

   ```bash
   docker run -p 6333:6333 \
       -v $(pwd)/dev.yaml:/qdrant/config/dev.yaml \
       -e RUN_MODE=dev \
       qdrant/qdrant
   ```

3. **Local Configuration: `config/local.yaml`**

   The `local.yaml` file is typically used for machine-specific settings that are not tracked in version control:

   ```bash
   docker run -p 6333:6333 \
       -v $(pwd)/local.yaml:/qdrant/config/local.yaml \
       qdrant/qdrant
   ```

4. **Custom Configuration via `--config-path`**

   You can specify a custom configuration file path using the `--config-path` argument. This will override other configuration files:

   ```bash
   docker run -p 6333:6333 \
       -v $(pwd)/config.yaml:/path/to/config.yaml \
       qdrant/qdrant \
       ./qdrant --config-path /path/to/config.yaml
   ```

For details on how these configurations are loaded and merged, see the [loading order and priority](#loading-order-and-priority). The full list of available configuration options can be found [below](#configuration-options).

## Environment Variables

You can also configure Qdrant using environment variables, which always take the highest priority and override any file-based settings.

Environment variables follow this format: they should be prefixed with `QDRANT__`, and nested properties should be separated by double underscores (`__`). For example:

```bash
docker run -p 6333:6333 \
    -e QDRANT__LOG_LEVEL=INFO \
    -e QDRANT__SERVICE__API_KEY=<MY_SECRET_KEY> \
    -e QDRANT__SERVICE__ENABLE_TLS=1 \
    -e QDRANT__TLS__CERT=./tls/cert.pem \
    qdrant/qdrant
```

This results in the following configuration:

```yaml
log_level: INFO
service:
  enable_tls: true
  api_key: <MY_SECRET_KEY>
tls:
  cert: ./tls/cert.pem
```

## Loading Order and Priority

During startup, Qdrant merges multiple configuration sources into a single effective configuration. The loading order is as follows (from least to most significant):

1. Embedded default configuration
2. `config/config.yaml`
3. `config/{RUN_MODE}.yaml`
4. `config/local.yaml`
5. Custom configuration file
6. Environment variables

### Overriding Behavior

Settings from later sources in the list override those from earlier sources:

- Settings in `config/{RUN_MODE}.yaml` (3) will override those in `config/config.yaml` (2).
- A custom configuration file provided via `--config-path` (5) will override all other file-based settings.
- Environment variables (6) have the highest priority and will override any settings from files.

## Configuration Validation

Qdrant validates the configuration during startup. If any issues are found, the server will terminate immediately, providing information about the error. For example:

```console
Error: invalid type: 64-bit integer `-1`, expected an unsigned 64-bit or smaller integer for key `storage.hnsw_index.max_indexing_threads` in config/production.yaml
```

This ensures that misconfigurations are caught early, preventing Qdrant from running with invalid settings.

## Configuration Options

The following YAML example describes the available configuration options.

```yaml
log_level: INFO

# Logging configuration
# Qdrant logs to stdout. You may configure to also write logs to a file on disk.
# Be aware that this file may grow indefinitely.
# logger:
#   on_disk:
#     enabled: true
#     log_file: path/to/log/file.log
#     log_level: INFO

storage:
  # Where to store all the data
  storage_path: ./storage

  # Where to store snapshots
  snapshots_path: ./snapshots

  snapshots_config:
    # "local" or "s3" - where to store snapshots
    snapshots_storage: local
    # s3_config:
    #   bucket: ""
    #   region: ""
    #   access_key: ""
    #   secret_key: ""
    #   endpoint_url: ""

  # Where to store temporary files
  # If null, temporary snapshots are stored in: storage/snapshots_temp/
  temp_path: null

  # If true - the point's payload will not be stored in memory.
  # It will be read from the disk every time it is requested.
  # This setting saves RAM by (slightly) increasing the response time.
  # Note: those payload values that are involved in filtering and are indexed - remain in RAM.
  on_disk_payload: true

  # Maximum number of concurrent updates to shard replicas
  # If `null` - maximum concurrency is used.
  update_concurrency: null

  # Write-ahead-log related configuration
  wal:
    # Size of a single WAL segment
    wal_capacity_mb: 32

    # Number of WAL segments to create ahead of actual data requirement
    wal_segments_ahead: 0

  # Normal node - receives all updates and answers all queries
  node_type: "Normal"

  # Listener node - receives all updates, but does not answer search/read queries
  # Useful for setting up a dedicated backup node
  # node_type: "Listener"

  performance:
    # Number of parallel threads used for search operations. If 0 - auto selection.
    max_search_threads: 0

    # Max number of threads (jobs) for running optimizations across all collections, each thread runs one job.
    # If 0 - have no limit and choose dynamically to saturate CPU.
    # Note: each optimization job will also use `max_indexing_threads` threads by itself for index building.
    max_optimization_threads: 0

    # CPU budget, how many CPUs (threads) to allocate for an optimization job.
    # If 0 - auto selection, keep 1 or more CPUs unallocated depending on CPU size
    # If negative - subtract this number of CPUs from the available CPUs.
    # If positive - use this exact number of CPUs.
    optimizer_cpu_budget: 0

    # Prevent DDoS of too many concurrent updates in distributed mode.
    # One external update usually triggers multiple internal updates, which breaks internal
    # timings. For example, the health check timing and consensus timing.
    # If null - auto selection.
    update_rate_limit: null

    # Limit for number of incoming automatic shard transfers per collection on this node, does not affect user-requested transfers.
    # The same value should be used on all nodes in a cluster.
    # Default is to allow 1 transfer.
    # If null - allow unlimited transfers.
    #incoming_shard_transfers_limit: 1

    # Limit for number of outgoing automatic shard transfers per collection on this node, does not affect user-requested transfers.
    # The same value should be used on all nodes in a cluster.
    # Default is to allow 1 transfer.
    # If null - allow unlimited transfers.
    #outgoing_shard_transfers_limit: 1

    # Enable async scorer which uses io_uring when rescoring.
    # Only supported on Linux, must be enabled in your kernel.
    # See: <https://qdrant.tech/articles/io_uring/#and-what-about-qdrant>
    #async_scorer: false

  optimizers:
    # The minimal fraction of deleted vectors in a segment, required to perform segment optimization
    deleted_threshold: 0.2

    # The minimal number of vectors in a segment, required to perform segment optimization
    vacuum_min_vector_number: 1000

    # Target amount of segments optimizer will try to keep.
    # Real amount of segments may vary depending on multiple parameters:
    #  - Amount of stored points
    #  - Current write RPS
    #
    # It is recommended to select default number of segments as a factor of the number of search threads,
    # so that each segment would be handled evenly by one of the threads.
    # If `default_segment_number = 0`, will be automatically selected by the number of available CPUs
    default_segment_number: 0

    # Do not create segments larger this size (in KiloBytes).
    # Large segments might require disproportionately long indexation times,
    # therefore it makes sense to limit the size of segments.
    #
    # If indexation speed have more priority for your - make this parameter lower.
    # If search speed is more important - make this parameter higher.
    # Note: 1Kb = 1 vector of size 256
    # If not set, will be automatically selected considering the number of available CPUs.
    max_segment_size_kb: null

    # Maximum size (in KiloBytes) of vectors to store in-memory per segment.
    # Segments larger than this threshold will be stored as read-only memmaped file.
    # To enable memmap storage, lower the threshold
    # Note: 1Kb = 1 vector of size 256
    # To explicitly disable mmap optimization, set to `0`.
    # If not set, will be disabled by default. Previously this was called memmap_threshold_kb.
    memmap_threshold: null

    # Maximum size (in KiloBytes) of vectors allowed for plain index.
    # Default value based on https://github.com/google-research/google-research/blob/master/scann/docs/algorithms.md
    # Note: 1Kb = 1 vector of size 256
    # To explicitly disable vector indexing, set to `0`.
    # If not set, the default value will be used.
    indexing_threshold_kb: 20000

    # Interval between forced flushes.
    flush_interval_sec: 5

    # Max number of threads (jobs) for running optimizations per shard.
    # Note: each optimization job will also use `max_indexing_threads` threads by itself for index building.
    # If null - have no limit and choose dynamically to saturate CPU.
    # If 0 - no optimization threads, optimizations will be disabled.
    max_optimization_threads: null

  # This section has the same options as 'optimizers' above. All values specified here will overwrite the collections
  # optimizers configs regardless of the config above and the options specified at collection creation.
  #optimizers_overwrite:
  #  deleted_threshold: 0.2
  #  vacuum_min_vector_number: 1000
  #  default_segment_number: 0
  #  max_segment_size_kb: null
  #  memmap_threshold: null
  #  indexing_threshold_kb: 20000
  #  flush_interval_sec: 5
  #  max_optimization_threads: null

  # Default parameters of HNSW Index. Could be overridden for each collection or named vector individually
  hnsw_index:
    # Number of edges per node in the index graph. Larger the value - more accurate the search, more space required.
    m: 16

    # Number of neighbours to consider during the index building. Larger the value - more accurate the search, more time required to build index.
    ef_construct: 100

    # Minimal size (in KiloBytes) of vectors for additional payload-based indexing.
    # If payload chunk is smaller than `full_scan_threshold_kb` additional indexing won't be used -
    # in this case full-scan search should be preferred by query planner and additional indexing is not required.
    # Note: 1Kb = 1 vector of size 256
    full_scan_threshold_kb: 10000

    # Number of parallel threads used for background index building.
    # If 0 - automatically select.
    # Best to keep between 8 and 16 to prevent likelihood of building broken/inefficient HNSW graphs.
    # On small CPUs, less threads are used.
    max_indexing_threads: 0

    # Store HNSW index on disk. If set to false, index will be stored in RAM. Default: false
    on_disk: false

    # Custom M param for hnsw graph built for payload index. If not set, default M will be used.
    payload_m: null

  # Default shard transfer method to use if none is defined.
  # If null - don't have a shard transfer preference, choose automatically.
  # If stream_records, snapshot or wal_delta - prefer this specific method.
  # More info: https://qdrant.tech/documentation/guides/distributed_deployment/#shard-transfer-method
  shard_transfer_method: null

  # Default parameters for collections
  collection:
    # Number of replicas of each shard that network tries to maintain
    replication_factor: 1

    # How many replicas should apply the operation for us to consider it successful
    write_consistency_factor: 1

    # Default parameters for vectors.
    vectors:
      # Whether vectors should be stored in memory or on disk.
      on_disk: null

    # shard_number_per_node: 1

    # Default quantization configuration.
    # More info: https://qdrant.tech/documentation/guides/quantization
    quantization: null

    # Default strict mode parameters for newly created collections.
    strict_mode:
      # Whether strict mode is enabled for a collection or not.
      enabled: false

      # Max allowed `limit` parameter for all APIs that don't have their own max limit.
      max_query_limit: null

      # Max allowed `timeout` parameter.
      max_timeout: null

      # Allow usage of unindexed fields in retrieval based (eg. search) filters.
      unindexed_filtering_retrieve: null

      # Allow usage of unindexed fields in filtered updates (eg. delete by payload).
      unindexed_filtering_update: null

      # Max HNSW value allowed in search parameters.
      search_max_hnsw_ef: null

      # Whether exact search is allowed or not.
      search_allow_exact: null

      # Max oversampling value allowed in search.
      search_max_oversampling: null

service:
  # Maximum size of POST data in a single request in megabytes
  max_request_size_mb: 32

  # Number of parallel workers used for serving the api. If 0 - equal to the number of available cores.
  # If missing - Same as storage.max_search_threads
  max_workers: 0

  # Host to bind the service on
  host: 0.0.0.0

  # HTTP(S) port to bind the service on
  http_port: 6333

  # gRPC port to bind the service on.
  # If `null` - gRPC is disabled. Default: null
  # Comment to disable gRPC:
  grpc_port: 6334

  # Enable CORS headers in REST API.
  # If enabled, browsers would be allowed to query REST endpoints regardless of query origin.
  # More info: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
  # Default: true
  enable_cors: true

  # Enable HTTPS for the REST and gRPC API
  enable_tls: false

  # Check user HTTPS client certificate against CA file specified in tls config
  verify_https_client_certificate: false

  # Set an api-key.
  # If set, all requests must include a header with the api-key.
  # example header: `api-key: <API-KEY>`
  #
  # If you enable this you should also enable TLS.
  # (Either above or via an external service like nginx.)
  # Sending an api-key over an unencrypted channel is insecure.
  #
  # Uncomment to enable.
  # api_key: your_secret_api_key_here

  # Set an api-key for read-only operations.
  # If set, all requests must include a header with the api-key.
  # example header: `api-key: <API-KEY>`
  #
  # If you enable this you should also enable TLS.
  # (Either above or via an external service like nginx.)
  # Sending an api-key over an unencrypted channel is insecure.
  #
  # Uncomment to enable.
  # read_only_api_key: your_secret_read_only_api_key_here

  # Uncomment to enable JWT Role Based Access Control (RBAC).
  # If enabled, you can generate JWT tokens with fine-grained rules for access control.
  # Use generated token instead of API key.
  #
  # jwt_rbac: true

cluster:
  # Use `enabled: true` to run Qdrant in distributed deployment mode
  enabled: false

  # Configuration of the inter-cluster communication
  p2p:
    # Port for internal communication between peers
    port: 6335

    # Use TLS for communication between peers
    enable_tls: false

  # Configuration related to distributed consensus algorithm
  consensus:
    # How frequently peers should ping each other.
    # Setting this parameter to lower value will allow consensus
    # to detect disconnected nodes earlier, but too frequent
    # tick period may create significant network and CPU overhead.
    # We encourage you NOT to change this parameter unless you know what you are doing.
    tick_period_ms: 100

# Set to true to prevent service from sending usage statistics to the developers.
# Read more: https://qdrant.tech/documentation/guides/telemetry
# Defaults: false
telemetry_disabled: false

# TLS configuration.
# Required if either service.enable_tls or cluster.p2p.enable_tls is true.
tls:
  # Server certificate chain file
  cert: ./tls/cert.pem

  # Server private key file
  key: ./tls/key.pem

  # Certificate authority certificate file.
  # This certificate will be used to validate the certificates
  # presented by other nodes during inter-cluster communication.
  #
  # If verify_https_client_certificate is true, it will verify
  # HTTPS client certificate
  #
  # Required if cluster.p2p.enable_tls is true.
  ca_cert: ./tls/cacert.pem

  # TTL in seconds to reload certificate from disk, useful for certificate rotations.
  # Only works for HTTPS endpoints. Does not support gRPC (and intra-cluster communication).
  # If `null` - TTL is disabled.
  cert_ttl: 3600
```