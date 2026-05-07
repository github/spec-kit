# Authentication

Specify CLI uses **opt-in authentication** for HTTP requests to catalog
sources, extension downloads, and release checks.  No credentials are
sent unless you explicitly configure them.

## Configuration

Create `~/.specify/auth.json` to enable authentication:

```json
{
  "providers": [
    {
      "hosts": ["github.com", "api.github.com", "raw.githubusercontent.com", "codeload.github.com"],
      "provider": "github",
      "auth": "bearer",
      "token_env": "GH_TOKEN"
    }
  ]
}
```

> **Security:** Restrict the file to owner-only access:
> ```
> chmod 600 ~/.specify/auth.json
> ```

Without this file, all HTTP requests are unauthenticated.

## Fields

Each entry in the `providers` array has the following fields:

| Field | Required | Description |
|---|---|---|
| `hosts` | Yes | Array of hostnames this entry applies to. Supports exact hostnames, or a leading `*.` wildcard for subdomains only (for example, `*.visualstudio.com`). `*.visualstudio.com` matches `foo.visualstudio.com`, but not `visualstudio.com`. Other glob patterns such as `*github.com` or `gith?b.com` are not supported. |
| `provider` | Yes | Built-in provider key: `github` or `azure-devops`. |
| `auth` | Yes | Auth scheme (see below). |
| `token` | No | Token value (inline). Use `token_env` instead when possible. |
| `token_env` | No | Environment variable name to read the token from. |

For `azure-ad` auth, additional fields are required:

| Field | Required | Description |
|---|---|---|
| `tenant_id` | Yes | Azure AD tenant ID. |
| `client_id` | Yes | Service principal client ID. |
| `client_secret_env` | Yes | Environment variable containing the client secret. |

Either `token` or `token_env` must be set for `bearer` and `basic-pat` schemes.

## Providers and auth schemes

### GitHub (`github`)

| Scheme | Header | Use for |
|---|---|---|
| `bearer` | `Authorization: Bearer <token>` | PATs, fine-grained PATs, OAuth tokens, GitHub App tokens |

**Example — PAT via environment variable:**

```json
{
  "hosts": ["github.com", "api.github.com", "raw.githubusercontent.com", "codeload.github.com"],
  "provider": "github",
  "auth": "bearer",
  "token_env": "GH_TOKEN"
}
```

### Azure DevOps (`azure-devops`)

| Scheme | Header | Use for |
|---|---|---|
| `basic-pat` | `Authorization: Basic base64(:<PAT>)` | Personal Access Tokens |
| `bearer` | `Authorization: Bearer <token>` | Pre-acquired OAuth / Azure AD tokens |
| `azure-cli` | `Authorization: Bearer <token>` | Token acquired via `az account get-access-token` |
| `azure-ad` | `Authorization: Bearer <token>` | Token acquired via OAuth2 client credentials flow |

**Example — PAT via environment variable:**

```json
{
  "hosts": ["dev.azure.com"],
  "provider": "azure-devops",
  "auth": "basic-pat",
  "token_env": "AZURE_DEVOPS_PAT"
}
```

**Example — Azure CLI (interactive login):**

```json
{
  "hosts": ["dev.azure.com"],
  "provider": "azure-devops",
  "auth": "azure-cli"
}
```

Requires `az login` to have been run beforehand.

**Example — Azure AD service principal (CI/automation):**

```json
{
  "hosts": ["dev.azure.com"],
  "provider": "azure-devops",
  "auth": "azure-ad",
  "tenant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "client_secret_env": "AZURE_CLIENT_SECRET"
}
```

## Multiple entries

You can configure multiple entries for different hosts or organizations:

```json
{
  "providers": [
    {
      "hosts": ["github.com", "api.github.com", "raw.githubusercontent.com", "codeload.github.com"],
      "provider": "github",
      "auth": "bearer",
      "token_env": "GH_TOKEN"
    },
    {
      "hosts": ["dev.azure.com"],
      "provider": "azure-devops",
      "auth": "basic-pat",
      "token_env": "AZURE_DEVOPS_PAT"
    }
  ]
}
```

## How it works

1. For each outbound HTTP request, the URL hostname is matched against
   the `hosts` patterns in `auth.json`.
2. If a match is found, the corresponding provider resolves the token
   and attaches the appropriate `Authorization` header.
3. If the request receives a 401 or 403, the next matching entry is tried.
4. After all matching entries are exhausted, an unauthenticated request
   is attempted as a final fallback.
5. On redirects, the `Authorization` header is stripped if the redirect
   target leaves the entry's declared hosts — preventing credential
   leakage to CDNs or third-party services.

## Template

A reference `auth.json` with GitHub pre-configured:

```json
{
  "providers": [
    {
      "hosts": [
        "github.com",
        "api.github.com",
        "raw.githubusercontent.com",
        "codeload.github.com"
      ],
      "provider": "github",
      "auth": "bearer",
      "token_env": "GH_TOKEN"
    }
  ]
}
```

To use it:

```bash
mkdir -p ~/.specify
# Copy the JSON above into ~/.specify/auth.json
chmod 600 ~/.specify/auth.json
```
