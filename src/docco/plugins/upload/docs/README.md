# upload plugin

Uploads the generated PDF to an SFTP server after the pipeline completes (POSTPROCESS phase).

## Configuration

```toml
[upload]
enable = true        # set to false to skip upload but keep config in place
host = "sftp.example.com"
port = 22            # optional, default: 22
user = "myuser"
password = "mypassword"
path = "/remote/uploads"
```

All keys except `enable` and `port` are required. If the `[upload]` section is absent, or `enable = false`, the plugin skips the upload (and logs this). The default for `enable` is `true`.

**Warning:** Passwords are stored in plain text in `docco.toml`.
