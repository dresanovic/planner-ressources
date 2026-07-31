# Data Model: Containerized Application Distribution

This feature introduces no application database tables or domain-record
changes. It defines deployment entities and their relationships.

## Release Image

Represents one immutable published application build.

### Attributes

- Registry name
- Exact release tag
- Major/minor convenience tags
- Optional stable convenience tag
- Source revision
- Supported architectures
- OCI source/version/revision labels
- Software bill of materials
- Build provenance digest
- Public or private package visibility

### Validation rules

- Exact tag matches the published release.
- Stable convenience tag is omitted for prereleases.
- Both required Linux architectures are present.
- Publication occurs only after all required checks pass.

## Deployment Configuration

Represents administrator-supplied runtime configuration.

### Attributes

- Exact image reference
- Host port
- Institution time zone
- Lecturer-review fingerprint key

### Validation rules

- Image reference should use an exact release tag or digest.
- Host port maps to the single application port.
- Fingerprint key is required in production and contains at least 32 bytes of
  key material.

## Persistent Application Data

Represents state retained independently from a container instance.

### Attributes

- Planner database
- Verified backup files
- Named volume identity

### Relationships

- One deployment mounts one persistent-data volume.
- Multiple sequential container versions may reuse the same volume.
- Only one live SQLite-backed application container may use the volume.

## State transitions

```text
empty volume
  -> first startup initializes database
  -> normal operation updates database
  -> backup creates verified snapshot
  -> restart/replacement reuses database
  -> upgrade applies supported startup migrations
```

Container removal does not remove persistent data unless the administrator
explicitly removes the volume.
