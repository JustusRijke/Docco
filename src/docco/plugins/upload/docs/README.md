# upload plugin

Uploads the generated PDF to an SFTP server after the pipeline completes (POSTPROCESS phase).

## Configuration

```toml
[upload]
enable = true        # true / false / "ask" (prompt before uploading); default: false
host = "sftp.example.com"
port = 22            # optional, default: 22
user = "myuser"
password = "mypassword"
path = "/remote/uploads"
```

All keys except `enable` and `port` are required. If the `[upload]` section is absent, the plugin is a no-op. If the section is present but `enable` is `false` (the default), it skips and logs.

Setting `enable = "ask"` prompts interactively before each upload (`Upload PDF? [y/N]`); pressing Enter without input defaults to **No**.

**Warning:** Passwords are stored in plain text in `docco.toml`.
